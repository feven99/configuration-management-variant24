"""Validate PlantUML, SVG and ASCII graph renderings."""

import tempfile
import unittest
from pathlib import Path

from src.graph import bfs, test_source
from src.visual import ascii_tree, plantuml, save_visuals, svg_graph


class VisualizationTests(unittest.TestCase):
    """Ensure all edges are rendered and cycles remain finite."""

    def setUp(self):
        _, children = test_source('examples/graph.json')
        self.graph = bfs('A', children)

    def test_plantuml_directed_edges(self):
        text = plantuml(self.graph)
        self.assertIn('@startuml', text)
        self.assertIn('@enduml', text)
        self.assertEqual(text.count('-->'), 6)

    def test_ascii_marks_cycle(self):
        tree = ascii_tree(self.graph, 'A')
        self.assertIn('A (seen)', tree)
        self.assertIn('D (seen)', tree)
        self.assertEqual(tree.count('A (seen)'), 1)

    def test_svg_is_xml(self):
        import xml.etree.ElementTree as et
        root = et.fromstring(svg_graph(self.graph, 'A'))
        self.assertTrue(root.tag.endswith('svg'))
        self.assertEqual(len(root.findall('.//{*}path')), 7)

    def test_save_outputs(self):
        with tempfile.TemporaryDirectory() as path:
            uml, svg = save_visuals(self.graph, 'A', path)
            self.assertTrue(uml.is_file())
            self.assertTrue(svg.is_file())
            self.assertTrue(Path(svg).read_text().startswith('<svg'))

    def test_isolated_package_visualization(self):
        _, source = test_source('examples/graph.json')
        graph = bfs('H', source)
        self.assertEqual(ascii_tree(graph, 'H'), 'H')
        self.assertIn('@startuml', plantuml(graph))


if __name__ == '__main__':
    unittest.main()
