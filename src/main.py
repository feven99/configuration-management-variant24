"""CLI entry point for the five practical-work stages of variant 24."""

import argparse
import sys
from pathlib import Path

from .config import load_config
from .graph import bfs, test_source
from .reverse import reverse_bfs, reverse_test_repository
from .maven import fetch_pom, local_pom, parse_pom, pom_url
from .source import maven_source


def _print_settings(settings):
    """Show every user-configurable setting in key-value form."""
    for key, value in settings.items():
        print(f'{key} = {value}')


def _direct(settings):
    """Read and display one Maven POM's direct dependencies."""
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


def _graph_input(settings, max_nodes):
    """Collect a reachable graph using an iterative BFS."""
    is_mock = settings['test_mode'] and Path(
        settings['test_path']).suffix.lower() == '.json'
    if settings['test_mode'] and not is_mock:
        raise ValueError('Stages 3-5 test mode requires a JSON graph file')
    if is_mock:
        source, children = test_source(settings['test_path'])
        root = settings['package']
        if not root or root not in source:
            raise ValueError('package must name a node in the test graph')
    else:
        root = (f"{settings['group']}:{settings['artifact']}:"
                f"{settings['version']}")
        children = maven_source(settings['repository'])
    graph = bfs(root, children, settings['filter_substring'], max_nodes)
    return root, graph


def _print_graph(root, graph):
    """Print graph edges and partial-data warnings for Stage 3."""
    print(f'BFS dependency graph from {root}:')
    for node, neighbors in graph.edges.items():
        print(f'  {node} -> {", ".join(neighbors) or "(none)"}')
    for warning in graph.warnings:
        print(f'WARNING: {warning}', file=sys.stderr)


def _reverse(settings, max_nodes):
    """Show reverse dependencies, with repository scope made explicit."""
    root, graph = _graph_input(settings, max_nodes)
    if settings['test_mode'] and settings['test_path'].endswith('.json'):
        repository, _ = test_source(settings['test_path'])
        result = reverse_test_repository(
            repository, root, settings['filter_substring'])
        print('Scope: entire supplied test repository')
    else:
        result = reverse_bfs(graph, root)
        print('Scope: discovered graph ONLY; not the entire Maven index')
        print('WARNING: Maven POMs do not list their reverse dependents')
    print(f'Reverse dependencies of {root}:')
    for item in result:
        print(f'  - {item}')
    print(f'Total: {len(result)}')


def main(argv=None):
    """Run one stage (Stage 2 remains the default for compatibility)."""
    parser = argparse.ArgumentParser(description='Maven graph, variant 24')
    parser.add_argument('--config', default='config.ini')
    parser.add_argument('--stage', type=int, choices=(1, 2, 3, 4), default=2)
    parser.add_argument('--max-nodes', type=int, default=100)
    args = parser.parse_args(argv)
    try:
        if args.max_nodes < 1:
            raise ValueError('max-nodes must be positive')
        settings = load_config(args.config)
        if args.stage == 1:
            _print_settings(settings)
        elif args.stage == 2:
            _direct(settings)
        elif args.stage == 3:
            root, graph = _graph_input(settings, args.max_nodes)
            _print_graph(root, graph)
        else:
            _reverse(settings, args.max_nodes)
    except ValueError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
