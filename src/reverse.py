"""Query incoming dependencies using an iterative BFS, never recursion."""

from collections import deque

from .graph import mock_full_graph


def reverse_bfs(graph, root):
    """Return packages that transitively depend on root in BFS order."""
    incoming = {}
    for parent, neighbors in graph.edges.items():
        for child in neighbors:
            incoming.setdefault(child, []).append(parent)
    queue = deque([root])
    seen = {root}
    result = []
    while queue:
        current = queue.popleft()
        for parent in sorted(incoming.get(current, [])):
            if parent not in seen:
                seen.add(parent)
                queue.append(parent)
                result.append(parent)
    return result


def reverse_test_repository(repository, root, substring=''):
    """Search the entire mock repository, not just root's descendants."""
    graph = mock_full_graph(repository, substring)
    if root not in graph.edges:
        raise ValueError('Root is excluded by the filter')
    return reverse_bfs(graph, root)
