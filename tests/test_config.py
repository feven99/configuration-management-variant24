"""Stage 1 invalid-parameter demonstrations for the INI parser."""

from pathlib import Path
import tempfile
import unittest

from src.config import load_config


VALID = '''[maven]
group_id = org.example
artifact_id = demo
version = 1.0.0
repository = https://repo.maven.apache.org/maven2
test_mode = false
test_path = examples/sample.pom
ascii_tree = true
filter_substring = x
'''


class ConfigurationTests(unittest.TestCase):
    """Check error handling for configurable user input."""

    def parse(self, data):
        """Load temporary INI data, avoiding modifications to example files."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'example.ini'
            path.write_text(data, encoding='utf-8')
            return load_config(str(path))

    def test_valid_options(self):
        self.assertEqual(self.parse(VALID)['artifact'], 'demo')

    def test_missing_section(self):
        with self.assertRaisesRegex(ValueError, r'\[maven\]'):
            self.parse('[other]\nfoo=bar\n')

    def test_invalid_group(self):
        with self.assertRaisesRegex(ValueError, 'group_id'):
            self.parse(VALID.replace('org.example', 'bad group'))

    def test_invalid_artifact(self):
        with self.assertRaisesRegex(ValueError, 'artifact_id'):
            self.parse(VALID.replace('demo', 'bad/artifact'))

    def test_invalid_version(self):
        with self.assertRaisesRegex(ValueError, 'version'):
            self.parse(VALID.replace('1.0.0', '!bad'))

    def test_invalid_repository(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            self.parse(VALID.replace('https://', 'http://'))

    def test_invalid_test_mode(self):
        with self.assertRaisesRegex(ValueError, 'test_mode'):
            self.parse(VALID.replace('test_mode = false',
                                     'test_mode = perhaps'))

    def test_invalid_ascii_tree(self):
        with self.assertRaisesRegex(ValueError, 'ascii_tree'):
            self.parse(VALID.replace('ascii_tree = true',
                                     'ascii_tree = perhaps'))

    def test_missing_test_path(self):
        with self.assertRaisesRegex(ValueError, 'test_path'):
            self.parse(VALID.replace('test_mode = false',
                                     'test_mode = true').replace(
                                         'test_path = examples/sample.pom',
                                         'test_path ='))

    def test_invalid_package(self):
        with self.assertRaisesRegex(ValueError, 'package'):
            self.parse(VALID + 'package = abc\n')


if __name__ == '__main__':
    unittest.main()
