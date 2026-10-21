#!/usr/bin/env python3
"""Run portable source parsing plus isolated unit tests; does not launch ROS."""
import ast
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    counts={'python':0,'xml':0,'json':0,'yaml':0,'yaml_skipped':0,'notebooks':0}
    errors=[]
    try:
        import yaml
    except ImportError:
        yaml=None
    for p in ROOT.rglob('*'):
        if not p.is_file() or any(part in p.parts for part in
                                  ('.git','build','install','log','__pycache__','.venv')):
            continue
        try:
            if p.suffix=='.py':
                ast.parse(p.read_text(encoding='utf-8-sig'),feature_version=(3,10));counts['python']+=1
            elif p.suffix=='.xml':
                ET.parse(p);counts['xml']+=1
            elif p.suffix in ('.json','.code-workspace'):
                json.loads(p.read_text());counts['json']+=1
            elif p.suffix in ('.yaml','.yml'):
                if yaml:yaml.safe_load(p.read_text());counts['yaml']+=1
                else:counts['yaml_skipped']+=1
            elif p.suffix=='.ipynb':counts['notebooks']+=1
        except Exception as error:errors.append([str(p.relative_to(ROOT)),str(error)])
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'static':counts,'errors':errors,'tests':result.testsRun,
                      'failures':len(result.failures),'test_errors':len(result.errors),
                      'skips':len(result.skipped)},indent=2))
    return int(bool(errors) or not result.wasSuccessful())


if __name__=='__main__':raise SystemExit(main())
