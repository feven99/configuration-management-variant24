"""CLI entry point for the five practical-work stages of variant 24."""

import argparse
import sys

from .config import load_config
from .maven import fetch_pom, local_pom, parse_pom, pom_url


def _print_settings(settings):
    """Show every user-configurable setting in key-value form."""
    for key, value in settings.items():
        print(f'{key} = {value}')


def _direct(settings):
    """Read and display the given Maven POM's direct dependencies."""
    if settings['test_mode']:
        data = local_pom(settings['test_path'])
    else:
        url = pom_url(settings['repository'], settings['group'],
                      settings['artifact'], settings['version'])
        print(f'POM URL: {url}')
        data = fetch_pom(url)
    dependencies = parse_pom(data)
    name = (f"{settings['group']}:{settings['artifact']}:"
            f"{settings['version']}")
    print(f'Direct dependencies of {name}:')
    for dep in dependencies:
        suffix = ' [optional]' if dep.optional else ''
        print(f'  - {dep.group_id}:{dep.artifact_id}:{dep.version}'
              f' [scope={dep.scope}]{suffix}')
    if not dependencies:
        print('  (none)')
    print(f'Total: {len(dependencies)}')


def main(argv=None):
    """Run the selected stage (default: Stage 2 for backward compatibility)."""
    parser = argparse.ArgumentParser(description='Maven graph, variant 24')
    parser.add_argument('--config', default='config.ini')
    parser.add_argument('--stage', type=int, choices=(1, 2), default=2)
    args = parser.parse_args(argv)
    try:
        settings = load_config(args.config)
        if args.stage == 1:
            _print_settings(settings)
        else:
            _direct(settings)
    except ValueError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
