#!/usr/bin/env python3
"""Compare the built/local report with an externally supplied authoritative .msg."""
import argparse
from pathlib import Path
import sys


ROSIDL_TYPE_ALIASES = {
    'float32': 'float',
    'float64': 'double',
}


def canonical_type(kind):
    """Return the rosidl runtime spelling for a source message type."""
    kind = kind.replace('/msg/', '/')
    return ROSIDL_TYPE_ALIASES.get(kind, kind)


def fields(text):
    result = []
    for line in text.splitlines():
        clean = line.split('#', 1)[0].strip()
        if clean:
            parts = clean.split()
            if len(parts) != 2:
                raise ValueError('Expected unbounded two-token message field')
            result.append((canonical_type(parts[0]), parts[1]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path,
                        help='Authoritative lecturer/hardware .msg file')
    parser.add_argument('--actual', type=Path,
                        default=Path(__file__).resolve().parents[1]/'tracker_interfaces_team_15/msg/TrackerReport.msg')
    parser.add_argument('--installed', action='store_true', help='Also check generated ROS type')
    args = parser.parse_args()
    expected, actual = fields(args.expected.read_text()), fields(args.actual.read_text())
    if expected != actual:
        print(f'INCOMPATIBLE: expected {expected}, repository {actual}', file=sys.stderr)
        return 1
    if args.installed:
        from tracker_interfaces_team_15.msg import TrackerReport
        installed = [(canonical_type(kind), name)
                     for name, kind in TrackerReport.get_fields_and_field_types().items()]
        if installed != expected:
            print(f'INCOMPATIBLE installed type: {installed}', file=sys.stderr)
            return 1
    print('Schema fields, order and types match the supplied authority.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
