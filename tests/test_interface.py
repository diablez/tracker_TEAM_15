import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify_interface', ROOT/'scripts/verify_interface.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)


class InterfaceTests(unittest.TestCase):
    def test_lecturer_slide_fields(self):
        expected=[('uint8','my_id'),('uint8','opp_id'),('sensor_msgs/CompressedImage','image'),
                  ('float32','rel_dist'),('float32','rel_orient')]
        actual=verify.fields((ROOT/'tracker_interfaces_team_15/msg/TrackerReport.msg').read_text())
        self.assertEqual(expected,actual)

    def test_header_and_field_order_are_not_wire_compatible(self):
        basic='uint8 my_id\nuint8 opp_id\nsensor_msgs/CompressedImage image'
        self.assertNotEqual(verify.fields(basic),verify.fields('std_msgs/Header header\n'+basic))
        self.assertNotEqual(verify.fields(basic),verify.fields('\n'.join(reversed(basic.splitlines()))))


if __name__=='__main__':unittest.main()
