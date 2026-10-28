"""Dependency graphs collected by an iterative breadth-first search."""

from collections import deque
from dataclasses import dataclass, field
import json
from pathlib import Path
import re


@dataclass
class Graph:
    """Directed graph: an edge means 'left depends on right'."""

    edges: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def artifact_name(node):
    """Find the artifact portion of a Maven coordinate or test node."""
    fields = node.split(':')
    return fields[1] if len(fields) == 3 else node


def _is_filtered(node, substring):
    """Apply the configured substring to package/artifact names."""
    return bool(substring and substring in artifact_name(node))


def bfs(root, children, substring='', max_nodes=100):
    """Build all reachable edges with a queue, without recursion."""
    if _is_filtered(root, substring):
        raise ValueError('Root package is excluded by filter_substring')
    graph = Graph()
    queue = deque([root])
    queued = {root}
    while queue:
        if len(graph.edges) >= max_nodes:
            graph.warnings.append(f'Stopped at maximum {max_nodes} nodes')
            break
        node = queue.popleft()
        try:
            neighbors = children(node)
        except ValueError as exc:
            graph.warnings.append(f'{node}: {exc}')
            neighbors = []
        graph.edges[node] = list(dict.fromkeys(
            item for item in neighbors if not _is_filtered(item, substring)
        ))
        for neighbor in graph.edges[node]:
            if neighbor not in queued:
                queue.append(neighbor)
                queued.add(neighbor)
    return graph


def load_test_graph(path):
    """Read a JSON adjacency list of uppercase Latin-letter package names."""
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read test graph: {exc}') from exc
    if not isinstance(data, dict):
        raise ValueError('Test graph must be a JSON object')
    valid = re.compile(r'^[A-Z]+$')
    for node, neighbors in data.items():
        if not isinstance(node, str) or not valid.fullmatch(node):
            raise ValueError(f'Invalid test package: {node!r}')
        if not isinstance(neighbors, list):
            raise ValueError(f'Test graph node {node} must have a list')
        if any(not isinstance(n, str) or not valid.fullmatch(n)
               for n in neighbors):
            raise ValueError(f'Invalid neighbor of {node}')
    return {key: list(dict.fromkeys(value)) for key, value in data.items()}


def test_source(path):
    """Return the complete mock repository and its child-fetch callback."""
    repository = load_test_graph(path)
    return repository, lambda node: repository.get(node, [])


def mock_full_graph(repository, substring=''):
    """Index all mock nodes for repository-wide reverse dependency queries."""
    nodes = set(repository)
    nodes.update(n for neighbors in repository.values() for n in neighbors)
    return Graph({node: [n for n in repository.get(node, [])
                         if not _is_filtered(n, substring)]
                  for node in sorted(nodes)
                  if not _is_filtered(node, substring)})
