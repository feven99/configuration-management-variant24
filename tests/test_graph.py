"""Graph traversal tests: cycles, duplicate paths, filters and mock files."""

import tempfile
import unittest
from pathlib import Path

from src.graph import bfs, load_test_graph, test_source


class GraphTests(unittest.TestCase):
    """Check that iterative BFS is finite and faithfully represents edges."""

    def setUp(self):
        self.repository, self.children = test_source('examples/graph.json')

    def test_bfs_cycles(self):
        graph = bfs('A', self.children)
        self.assertEqual(list(graph.edges), ['A', 'B', 'C', 'D', 'E'])
        self.assertEqual(graph.edges['D'], ['A'])

    def test_bfs_shares_nodes(self):
        graph = bfs('A', self.children)
        self.assertEqual(graph.edges['B'], ['D', 'E'])
        self.assertEqual(graph.edges['C'], ['D'])
        self.assertEqual(len(graph.edges), 5)

    def test_filter_excludes_target(self):
        graph = bfs('A', self.children, substring='D')
        self.assertNotIn('D', graph.edges)
        self.assertEqual(graph.edges['B'], ['E'])

    def test_filter_rejects_root(self):
        with self.assertRaises(ValueError):
            bfs('A', self.children, substring='A')

    def test_bfs_bound(self):
        graph = bfs('A', self.children, max_nodes=2)
        self.assertEqual(len(graph.edges), 2)
        self.assertTrue(graph.warnings)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"A": ["not_uppercase"]}')
            with self.assertRaisesRegex(ValueError, 'Invalid neighbor'):
                load_test_graph(str(path))

    def test_test_repository_nodes(self):
        self.assertIn('H', self.repository)
        self.assertEqual(self.children('H'), [])


if __name__ == '__main__':
    unittest.main()
