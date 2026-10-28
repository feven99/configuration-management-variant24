"""Offline unit tests for dependency retrieval and POM parsing."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.main import load_config
from src.maven import fetch_pom, parse_pom, pom_url


class MavenTests(unittest.TestCase):
    """Verify XML extraction, URLs, and INI validation."""

    def test_direct_dependencies_and_properties(self):
        data = Path('examples/sample.pom').read_bytes()
        deps = parse_pom(data)
        self.assertEqual(len(deps), 2)
        self.assertEqual(deps[0].version, '4.13.2')
        self.assertEqual(deps[0].scope, 'test')
        self.assertEqual(deps[1].scope, 'compile')

    def test_dependency_management_is_not_a_direct_dependency(self):
        xml = b'''<project><dependencyManagement><dependencies>
        <dependency><groupId>a</groupId><artifactId>b</artifactId>
        <version>1.2</version></dependency></dependencies></dependencyManagement>
        <dependencies><dependency><groupId>a</groupId>
        <artifactId>b</artifactId></dependency></dependencies></project>'''
        deps = parse_pom(xml)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].version, '1.2')

    def test_no_direct_dependencies(self):
        self.assertEqual(parse_pom(b'<project/>'), [])

    def test_invalid_xml(self):
        with self.assertRaises(ValueError):
            parse_pom(b'<project>')

    def test_url_construction(self):
        actual = pom_url('https://repo.maven.apache.org/maven2',
                         'org.example', 'demo', '1.0')
        self.assertEqual(actual,
                         'https://repo.maven.apache.org/maven2/'
                         'org/example/demo/1.0/demo-1.0.pom')

    def test_reject_http(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            fetch_pom('http://example.com/file.pom')

    def test_config_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'config.ini'
            config.write_text('[maven]\ngroup_id=x\nartifact_id=y\n'
                              'version=1\nrepository=http://bad.example\n')
            with self.assertRaisesRegex(ValueError, 'HTTPS'):
                load_config(str(config))

    def test_optional(self):
        data = (b'<project><dependencies><dependency><groupId>x</groupId>'
                b'<artifactId>y</artifactId><version>1</version>'
                b'<optional>true</optional></dependency></dependencies></project>')
        self.assertTrue(parse_pom(data)[0].optional)


if __name__ == '__main__':
    unittest.main()
