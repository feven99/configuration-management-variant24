"""Parse and validate INI settings for all practical-work stages."""

import configparser
from pathlib import Path
import re
from urllib.parse import urlparse

COORDINATE = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')
VERSION = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.+-]*$')
TEST_PACKAGE = re.compile(r'^[A-Z]+$')


def _boolean(section, name):
    """Read a required boolean without silently accepting missing values."""
    try:
        return section.getboolean(name)
    except (ValueError, configparser.NoOptionError) as exc:
        raise ValueError(f'Invalid or missing {name}: {exc}') from exc


def _read_ini(path):
    """Read an INI file and require the Maven configuration section."""
    file = Path(path)
    if not file.is_file():
        raise ValueError(f'Configuration file not found: {path}')
    config = configparser.ConfigParser(interpolation=None)
    try:
        with file.open(encoding='utf-8') as stream:
            config.read_file(stream)
    except (configparser.Error, UnicodeError, OSError) as exc:
        raise ValueError(f'Invalid INI configuration: {exc}') from exc
    if not config.has_section('maven'):
        raise ValueError('Missing [maven] section')
    return config['maven']


def _validate_coordinate(name, value):
    """Validate Maven group or artifact names."""
    if not COORDINATE.fullmatch(value):
        raise ValueError(f'Invalid or missing {name}: {value!r}')


def _validate_inputs(settings):
    """Check configuration-specific path, URL, and package constraints."""
    if not VERSION.fullmatch(settings['version']):
        raise ValueError(f"Invalid or missing version: {settings['version']!r}")
    _validate_coordinate('group_id', settings['group'])
    _validate_coordinate('artifact_id', settings['artifact'])
    parsed = urlparse(settings['repository'])
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError('repository must be a valid HTTPS URL')
    if settings['test_mode'] and not settings['test_path']:
        raise ValueError('test_path is required when test_mode=true')
    if settings['test_mode'] and not Path(settings['test_path']).is_file():
        raise ValueError(f"Test file not found: {settings['test_path']}")
    if '\n' in settings['filter_substring']:
        raise ValueError('filter_substring must be a single line')


def load_config(path):
    """Return validated settings for a POM or an uppercase test graph."""
    options = _read_ini(path)
    settings = {
        'group': options.get('group_id', '').strip(),
        'artifact': options.get('artifact_id', '').strip(),
        'version': options.get('version', '').strip(),
        'repository': options.get('repository', '').strip(),
        'test_mode': _boolean(options, 'test_mode'),
        'test_path': options.get('test_path', '').strip(),
        'ascii_tree': _boolean(options, 'ascii_tree'),
        'filter_substring': options.get('filter_substring', '').strip(),
        'package': options.get('package', '').strip(),
    }
    _validate_inputs(settings)
    if settings['package'] and not TEST_PACKAGE.fullmatch(settings['package']):
        raise ValueError('package must contain uppercase Latin letters')
    return settings
