"""Command-line entry point for variant 24, stage 2."""

import argparse
import configparser
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from .maven import fetch_pom, local_pom, parse_pom, pom_url


COORDINATE = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')
VERSION = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.+-]*$')


def load_config(path: str) -> dict[str, object]:
    """Read and validate user-facing configuration values."""
    config = configparser.ConfigParser(interpolation=None)
    if not Path(path).is_file():
        raise ValueError(f'Configuration file not found: {path}')
    try:
        config.read(path, encoding='utf-8')
    except configparser.Error as exc:
        raise ValueError(f'Invalid INI configuration: {exc}') from exc
    if not config.has_section('maven'):
        raise ValueError('Missing [maven] section')
    options = config['maven']
    group = options.get('group_id', '').strip()
    artifact = options.get('artifact_id', '').strip()
    version = options.get('version', '').strip()
    repository = options.get('repository', '').strip()
    test_path = options.get('test_path', '').strip()
    try:
        test_mode = options.getboolean('test_mode', fallback=False)
        ascii_tree = options.getboolean('ascii_tree', fallback=False)
    except ValueError as exc:
        raise ValueError(f'Invalid boolean configuration: {exc}') from exc
    for name, coordinate in [('group_id', group), ('artifact_id', artifact)]:
        if not COORDINATE.fullmatch(coordinate):
            raise ValueError(f'Invalid or missing {name}: {coordinate!r}')
    if not VERSION.fullmatch(version):
        raise ValueError(f'Invalid or missing version: {version!r}')
    if test_mode:
        if not test_path:
            raise ValueError('test_path is required when test_mode=true')
    else:
        parsed = urlparse(repository)
        if parsed.scheme != 'https' or not parsed.netloc:
            raise ValueError('repository must be a valid HTTPS URL')
    return {
        'group': group, 'artifact': artifact, 'version': version,
        'repository': repository, 'test_mode': test_mode,
        'test_path': test_path, 'ascii_tree': ascii_tree,
        'filter_substring': options.get('filter_substring', '').strip(),
    }


def main() -> int:
    """Fetch POM and display only directly declared dependencies."""
    parser = argparse.ArgumentParser(description='Maven direct dependencies')
    parser.add_argument('--config', default='config.ini',
                        help='INI configuration path')
    args = parser.parse_args()
    try:
        settings = load_config(args.config)
        if settings['test_mode']:
            data = local_pom(str(settings['test_path']))
        else:
            url = pom_url(str(settings['repository']),
                          str(settings['group']), str(settings['artifact']),
                          str(settings['version']))
            print(f'POM URL: {url}')
            data = fetch_pom(url)
        dependencies = parse_pom(data)
    except ValueError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    coordinate = (f"{settings['group']}:{settings['artifact']}:"
                  f"{settings['version']}")
    print(f'Direct dependencies of {coordinate}:')
    if not dependencies:
        print('  (none)')
    for dep in dependencies:
        suffix = ' [optional]' if dep.optional else ''
        print(f'  - {dep.group_id}:{dep.artifact_id}:{dep.version}'
              f' [scope={dep.scope}]{suffix}')
    print(f'Total: {len(dependencies)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
