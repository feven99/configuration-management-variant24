"""Reverse dependency tests on a complete mock repository."""

import unittest

from src.graph import Graph, test_source
from src.reverse import reverse_bfs, reverse_test_repository


class ReverseTests(unittest.TestCase):
    """Test incoming BFS for ordinary, isolated and cyclic repositories."""

    def setUp(self):
        self.repository, _ = test_source('examples/graph.json')

    def test_global_reverse_bfs(self):
        expected = ['D', 'F', 'B', 'C', 'G']
        self.assertEqual(reverse_test_repository(
            self.repository, 'A'), expected)

    def test_reverse_isolated_node(self):
        self.assertEqual(reverse_test_repository(self.repository, 'H'), [])

    def test_reverse_leaf(self):
        self.assertEqual(reverse_test_repository(
            self.repository, 'E'), ['B', 'A', 'D', 'F', 'C', 'G'])

    def test_filtered_reverse(self):
        result = reverse_test_repository(self.repository, 'A', 'D')
        self.assertEqual(result, ['F', 'G'])

    def test_reverse_removes_self_cycle(self):
        graph = Graph({'A': ['A', 'B'], 'B': ['A']})
        self.assertEqual(reverse_bfs(graph, 'A'), ['B'])


if __name__ == '__main__':
    unittest.main()
