"""Isolated tests execute production policies and timer methods; no ROS graph."""
import ast
import importlib.util
import math
from pathlib import Path
import sys
from types import SimpleNamespace as S
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tracker_TEAM_15'))
from tracker_TEAM_15 import capture_policy as policy


def pose(x=-.5, y=0., heading=0.):
    return S(translation=S(x=x, y=y), rotation=S(x=0., y=0.,
             z=math.sin(heading/2), w=math.cos(heading/2)))


def header(ns=100_000_000_000):
    return S(stamp=S(sec=ns//10**9, nanosec=ns % 10**9), frame_id='camera')


class FakeTime:
    def __init__(self, nanoseconds=0): self.nanoseconds = nanoseconds


def timer_class(filename, class_name, **extra):
    # Keep original class/function AST bodies and substitute only ROS imports.
    tree = ast.parse((ROOT/'tracker_TEAM_15/tracker_TEAM_15'/filename).read_text())
    tree.body = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    ns = {'math': math, 'time': S(monotonic=lambda: 100.), 're': __import__('re'),
          'Node': object, 'Time': FakeTime, 'TransformException': RuntimeError,
          'TrackerReport': S, **vars(policy), **extra}
    exec(compile(tree, filename, 'exec'), ns)
    return ns[class_name]


class PolicyTests(unittest.TestCase):
    def test_geometry_rear(self):
        self.assertEqual(policy.capture_geometry(pose(), pose(0)), (.5, 0.))

    def test_front_range_and_nonfinite(self):
        for p in (pose(.5, heading=math.pi), pose(-.7), pose(float('nan'))):
            with self.subTest(p=p), self.assertRaises(ValueError):
                policy.capture_geometry(p, pose(0))

    def test_five_field_schema_and_optional_header(self):
        image = S(header=header())
        r = policy.populate_report(S(), image, 2, 7, .5, 10)
        self.assertEqual(set(vars(r)), {'my_id', 'opp_id', 'image', 'rel_dist', 'rel_orient'})
        r = policy.populate_report(S(header=S()), image, 2, 7, .5, 10)
        self.assertIs(r.header.stamp, image.header.stamp)
        self.assertEqual(r.header.frame_id, 'camera')

    def test_empty_missing_frame_and_metadata(self):
        image = S(header=header(), data=b'', format='jpeg')
        self.assertFalse(policy.image_valid(image))
        image.data = b'junk'; image.header.frame_id = ''
        self.assertFalse(policy.image_valid(image))
        image.header.frame_id = 'camera'; image.format = 'compressedDepth png'
        self.assertFalse(policy.image_valid(image))

    def test_real_decoder_corrupt_and_valid(self):
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest('OpenCV not installed; install declared test/runtime dependency')
        self.assertFalse(policy.decode_image(S(data=b'not a JPEG')))
        ok, encoded = cv2.imencode('.jpg', np.zeros((4, 4, 3), dtype=np.uint8))
        self.assertTrue(ok)
        self.assertTrue(policy.decode_image(S(data=encoded.tobytes())))

    def lookup(self, age_ns=100_000_000, fail_common=False):
        calls = []
        def lookup(target, frame, when):
            calls.append((frame, when.nanoseconds))
            if when.nanoseconds == 100_000_000_000 or (fail_common and when.nanoseconds):
                raise ValueError('TF not yet available')
            h = header(100_000_000_000-age_ns if when.nanoseconds == 0 else when.nanoseconds)
            return S(header=h, transform=pose() if frame == 'red' else pose(0))
        return lookup, calls

    def get_pair(self, lookup, **kw):
        return policy.pose_pair(lookup, 'map', ('red', 'green'), header().stamp,
                                100_000_000_000, FakeTime, FakeTime(), **kw)

    def test_exact_time(self):
        pair, approximate = self.get_pair(lambda t, f, w:S(transform=pose()))
        self.assertFalse(approximate); self.assertEqual(len(pair), 2)

    def test_fallback_disabled(self):
        with self.assertRaises(ValueError): self.get_pair(self.lookup()[0])

    def test_bounded_common_time_fallback(self):
        lookup, calls = self.lookup()
        pair, approximate = self.get_pair(lookup, allow_latest=True)
        self.assertTrue(approximate)
        self.assertEqual(calls[-2:], [('red', 99_900_000_000), ('green', 99_900_000_000)])

    def test_fallback_rejects_skew_stale_future_and_unstamped(self):
        for age in (300_000_000, 2_000_000_000, -100_000_000, 100_000_000_000):
            with self.subTest(age=age), self.assertRaises(ValueError):
                self.get_pair(self.lookup(age)[0], allow_latest=True)

    def test_fallback_common_time_unavailable(self):
        with self.assertRaises(ValueError):
            self.get_pair(self.lookup(fail_common=True)[0], allow_latest=True)


class TimerTests(unittest.TestCase):
    def node(self):
        cls = timer_class('capture_report.py', 'CaptureReport')
        n = cls.__new__(cls)
        n.cfg = dict(enable_reporting=True, max_receive_age_sec=.9, max_image_age_sec=1.,
                     require_target_visible=False, allow_latest_tf=False,
                     max_tf_image_skew_sec=.25, min_distance_m=.4, max_distance_m=.6,
                     camera_half_fov_deg=40., opponent_front_exclusion_deg=70.,
                     capture_cooldown_sec=5., save_images=False)
        n.image=S(header=header(), data=b'received frame'); n.image_received=100.
        n.last_report=-math.inf; n.last_report_stamp=-1
        n.global_frame='map'; n.chaser_frame='red'; n.opponent_frame='green'
        n.my_id=2; n.opp_id=7; n.log=lambda *a, **k:None
        n.get_clock=lambda:S(now=lambda:S(nanoseconds=100_000_000_000))
        n.get_logger=lambda:S(info=lambda *a:None)
        n.tf_buffer=S(lookup_transform=lambda t, f, w:S(transform=pose() if f=='red' else pose(0)))
        n.reports=[];n.publisher=S(publish=n.reports.append); n.image_pub=S(publish=lambda *a:None)
        return n

    def test_valid_capture(self):
        n=self.node();n.check();self.assertEqual(len(n.reports),1)

    def test_no_camera_disabled_stale_future_reused_and_cooldown(self):
        for case in ('missing','disabled','stale','future','reused','older','cooldown'):
            n=self.node()
            if case=='missing': n.image=None
            if case=='disabled': n.cfg['enable_reporting']=False
            if case=='stale': n.image_received=95.
            if case=='future': n.image.header=header(101_000_000_000)
            if case=='reused': n.last_report_stamp=100_000_000_000
            if case=='older': n.last_report_stamp=101_000_000_000
            if case=='cooldown': n.last_report=95.001
            with self.subTest(case=case):n.check();self.assertFalse(n.reports)

    def test_five_second_boundary(self):
        n=self.node();n.last_report=95.;n.check();self.assertEqual(len(n.reports),1)

    def test_missing_tf_skips(self):
        n=self.node()
        def missing(*a): raise RuntimeError('no TF')
        n.tf_buffer.lookup_transform=missing;n.check();self.assertFalse(n.reports)

    def test_physical_pursuit_without_camera(self):
        cls=timer_class('tracker_two_tb4_TEAM_15.py','TrackerTwoTB4')
        n=cls.__new__(cls)
        n.global_frame='map'; n.enemy_base='green';n.chaser_base='red';n.enemy_offset=.5
        n.tf_buffer=S(lookup_transform=lambda t, f, w:S(transform=pose(0) if f=='green' else pose(-1)))
        n.yaw_from_transform=lambda t:0.;n.latest_image=None
        n.last_goal_x=None;n.last_goal_y=None;n.last_goal_yaw=None
        n.broadcast_goal_frame=lambda *a:None
        goals=[];n.send_goal=lambda *a:goals.append(a) or True
        n.update_goal()
        self.assertEqual(goals,[(-.5,0.,0.)])

    def test_physical_missing_camera_report_returns(self):
        cls=timer_class('tracker_two_tb4_TEAM_15.py','TrackerTwoTB4')
        n=cls.__new__(cls);n.enable_reporting=True;n.latest_image=None
        n.check_report()  # Must return without a camera, independent of pursuit.

    def test_physical_corrupt_frame_discards_cache(self):
        cls=timer_class('tracker_two_tb4_TEAM_15.py','TrackerTwoTB4',
                        decode_image=lambda image:False)
        n=cls.__new__(cls);n.enable_reporting=True;n.latest_image='previous frame'
        n.tracker_image_callback(S(header=header(),format='jpeg',data=b'corrupt'))
        self.assertIsNone(n.latest_image)


if __name__=='__main__': unittest.main()
