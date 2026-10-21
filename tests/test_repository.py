import ast
import json
import re
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_json_workspace_is_portable(self):
        for p in list((ROOT/'.vscode').glob('*.json'))+[ROOT/'team15.code-workspace']:
            value=json.loads(p.read_text())
            self.assertNotIn('C:\\Users',p.read_text())
            self.assertIsInstance(value,dict)
        self.assertEqual(json.loads((ROOT/'team15.code-workspace').read_text())['folders'],[{'path':'.'}])

    def test_markdown_relative_links_exist(self):
        for p in ROOT.rglob('*.md'):
            if '.git' in p.parts:continue
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):continue
                with self.subTest(file=p.name,target=target):
                    self.assertTrue((p.parent/target.split('#')[0]).exists())

    def test_physical_dependencies_declared(self):
        for package in ('localization_server_TEAM_15','path_planner_server_TEAM_15'):
            root=ET.parse(ROOT/package/'package.xml').getroot()
            deps=[e.text for e in root.findall('exec_depend')]
            self.assertIn('turtlebot4_navigation',deps)
            self.assertIn('ament_index_python',deps)

    def test_preserved_executable_registrations(self):
        tree=ast.parse((ROOT/'tracker_TEAM_15/setup.py').read_text())
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        for executable in ('tracker_two_tb4_TEAM_15','tracker_tb3_sim_TEAM_15','tracker_node','capture_report'):
            self.assertIn(f'{executable} = tracker_TEAM_15.{executable}:main',literals)
            self.assertTrue((ROOT/'tracker_TEAM_15/tracker_TEAM_15'/f'{executable}.py').exists())


if __name__=='__main__':unittest.main()
