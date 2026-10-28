"""Render dependency graphs as PlantUML, ASCII trees, and native SVG."""

from collections import deque
from html import escape
from pathlib import Path
import re


def _all_nodes(graph):
    """Include referenced leaf nodes that are outside the expanded graph."""
    nodes = set(graph.edges)
    nodes.update(n for values in graph.edges.values() for n in values)
    return sorted(nodes)


def plantuml(graph):
    """Generate valid PlantUML source for every graph edge."""
    nodes = _all_nodes(graph)
    names = {node: f'n{idx}' for idx, node in enumerate(nodes)}
    lines = ['@startuml', 'left to right direction',
             'skinparam linetype ortho']
    for node in nodes:
        safe = node.replace('"', '\\"')
        lines.append(f'rectangle "{safe}" as {names[node]}')
    for parent, children in graph.edges.items():
        for child in children:
            lines.append(f'{names[parent]} --> {names[child]}')
    return '\n'.join(lines + ['@enduml', ''])


def ascii_tree(graph, root):
    """Render a finite ASCII tree; shared nodes and cycles are marked."""
    lines = [root]
    visited = {root}
    stack = [(root, '', iter(enumerate(graph.edges.get(root, []))))]
    while stack:
        node, prefix, iterator = stack[-1]
        try:
            index, child = next(iterator)
        except StopIteration:
            stack.pop()
            continue
        neighbors = graph.edges.get(node, [])
        last = index == len(neighbors) - 1
        branch = '`-- ' if last else '|-- '
        seen = child in visited
        lines.append(prefix + branch + child + (' (seen)' if seen else ''))
        if not seen:
            visited.add(child)
            next_prefix = prefix + ('    ' if last else '|   ')
            stack.append((child, next_prefix,
                          iter(enumerate(graph.edges.get(child, [])))))
    return '\n'.join(lines)


def _depths(graph, root):
    """Assign each node a level with a queue-based BFS."""
    depths = {root: 0}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for neighbor in graph.edges.get(node, []):
            if neighbor not in depths:
                depths[neighbor] = depths[node] + 1
                queue.append(neighbor)
    return depths


def _positions(graph, root):
    """Arrange nodes by BFS depth in equally spaced vertical columns."""
    depths = _depths(graph, root)
    for node in _all_nodes(graph):
        depths.setdefault(node, max(depths.values(), default=0) + 1)
    layers = {}
    for node, level in depths.items():
        layers.setdefault(level, []).append(node)
    return {node: (40 + level * 360, 130 + idx * 100)
            for level, nodes in layers.items()
            for idx, node in enumerate(sorted(nodes))}


def _rectangles(positions):
    """Draw accessible SVG boxes with XML-escaped package labels."""
    result = []
    for node, (x, y) in positions.items():
        label = escape(node)
        result.append(f'<rect x="{x}" y="{y}" width="300" '
                      'height="54" rx="10" fill="#e9f3ff" '
                      'stroke="#2358a5" stroke-width="2"/>')
        result.append(f'<text x="{x + 12}" y="{y + 33}" '
                      'font-size="14" fill="#193451">'
                      f'{label}</text>')
    return result


def _arrows(graph, positions):
    """Draw arrows; backward/cycle edges use a dashed stroke."""
    lines = []
    for parent, children in graph.edges.items():
        sx, sy = positions[parent]
        for child in children:
            tx, ty = positions[child]
            backward = tx <= sx
            x1 = sx + (150 if backward else 300)
            x2 = tx + (150 if backward else 0)
            if backward:
                curve = f'M{x1},{sy} C{x1},25 {x2},25 {x2},{ty}'
                marker = ' stroke-dasharray="6 4"'
            else:
                curve = f'M{x1},{sy + 27} L{x2},{ty + 27}'
                marker = ''
            lines.append(f'<path d="{curve}" fill="none" '
                         'stroke="#536d8a" stroke-width="2" '
                         f'marker-end="url(#arrow)"{marker}/>')
    return lines


def svg_graph(graph, root):
    """Generate an SVG graph without third-party rendering dependencies."""
    positions = _positions(graph, root)
    width = max(x for x, _ in positions.values()) + 350
    height = max(y for _, y in positions.values()) + 110
    content = [f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{width}" height="{height}" '
               f'viewBox="0 0 {width} {height}" role="img">',
               '<title>Maven dependency graph</title>',
               '<defs><marker id="arrow" markerWidth="8" '
               'markerHeight="8" refX="7" refY="3" '
               'orient="auto"><path d="M0,0 L7,3 L0,6" '
               'fill="none" stroke="#536d8a"/></marker></defs>',
               '<rect width="100%" height="100%" fill="white"/>']
    return '\n'.join(content + _arrows(graph, positions)
                     + _rectangles(positions) + ['</svg>', ''])


def save_visuals(graph, root, directory):
    """Write the editable PlantUML source and an easily opened SVG image."""
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    name = re.sub(r'[^A-Za-z0-9_-]+', '_', root)
    uml_file = output / f'{name}.puml'
    svg_file = output / f'{name}.svg'
    uml_file.write_text(plantuml(graph), encoding='utf-8')
    svg_file.write_text(svg_graph(graph, root), encoding='utf-8')
    return uml_file, svg_file
