# Configuration Management — Practical Work No. 2, Variant 24

Five-stage CLI dependency graph tool for Java Maven artifacts, implemented
using **only Python 3.10+ standard library** for HTTP requests, XML parsing,
JSON, configuration, BFS, and rendering. No Maven/pip or third-party dependency
retrieval library is used by the implementation.

Source assignment: `ИКБО-51-25`, variant 24, pages 77–79.

## Run in Windows VS Code

Open **this folder** (the one containing `src`, `tests`, and `config.ini`).
In the terminal, type commands without the `PS C:\...>` prompt:

```powershell
py --version
py -m unittest discover -s tests -v
```

Commands for all five stages:

```powershell
# Stage 1: show the INI values and validate them
py -m src.main --stage 1 --config config.graph.ini

# Stage 2: direct dependencies from a local POM
py -m src.main --stage 2 --config config.offline.ini

# Stage 2: direct dependencies from the real Maven Central repository
py -m src.main --stage 2 --config config.ini

# Stage 3: iterative BFS on a test graph (cycles and shared nodes)
py -m src.main --stage 3 --config config.graph.ini

# Stage 3: filter package D from the graph
py -m src.main --stage 3 --config config.graph.filtered.ini

# Stage 4: reverse (incoming) dependencies in the complete test graph
py -m src.main --stage 4 --config config.graph.ini

# Stage 5: export PlantUML and SVG, open image, print ASCII tree
py -m src.main --stage 5 --config config.graph.ini
```

Stage 5 automatically opens `output/A.svg` in your browser, while saving
editable PlantUML diagram source to `output/A.puml`. If your computer cannot
open a browser automatically, open the SVG file manually. In headless
runs append `--no-open`. Output is ignored by Git to avoid committing generated
artifacts. The PlantUML diagram can also be rendered using an external
PlantUML renderer, but no renderer installation is necessary to view the SVG.

## Three separate graph demonstrations (Stage 5)

```powershell
py -m src.main --stage 5 --config config.graph.ini --package A
py -m src.main --stage 5 --config config.graph.ini --package B
py -m src.main --stage 5 --config config.graph.ini --package F
```

A has a cycle (A → B → D → A), B shares downstream descendants, and F
connects into the cycle. The test repository also contains an isolated H.

## Configuration (`[maven]` INI section)

| Field | Meaning |
| --- | --- |
| `group_id` | Maven group ID such as `org.apache.commons` |
| `artifact_id` | Maven artifact ID such as `commons-lang3` |
| `version` | Exact version of the root artifact |
| `repository` | HTTPS URL of a Maven-layout repository |
| `test_mode` | `true` for local files, `false` for HTTP |
| `test_path` | Offline POM (`.pom`) for Stage 2 or JSON mock graph for Stages 3–5 |
| `ascii_tree` | Enable the Stage 5 ASCII output |
| `filter_substring` | Exclude matching package names from BFS graph traversal |
| `package` | Uppercase test node, such as `A`, for graph mock mode |

Stage 1 prints all settings as key-value entries. Errors include missing
sections, invalid group/artifact/version, HTTP rather than HTTPS, wrong
booleans, missing test graph/POM and invalid uppercase mock package names.
To demonstrate validation and errors, run:

```powershell
py -m unittest tests.test_config -v
```

## File roles

- `src/config.py`: Stage 1, INI loading and parameter validation.
- `src/maven.py`: Stage 2, direct POM dependency retrieval and XML parse.
- `src/source.py`: adapt remote Maven POMs to graph edges.
- `src/graph.py`: Stage 3, iterative BFS, substring filter, mock graph loader.
- `src/reverse.py`: Stage 4, BFS for incoming/reverse dependencies.
- `src/visual.py`: Stage 5, PlantUML source, SVG image, ASCII tree.
- `src/main.py`: command-line entry point with `--stage 1..5`.
- `tests/`: regression tests for every implemented stage.
- `examples/graph.json`: uppercase Latin mock dependency repository.
- `examples/sample.pom`: offline Maven POM example.
- `COMPARISON.md`: native Maven comparison instructions and known differences.
- `run.bat` / `run.sh`: launch scripts.

## Algorithms and correctness

The forward graph uses a FIFO queue (`collections.deque`), not recursion.
A visited set prevents infinite cycle processing, while repeated/cyclic edges
remain in the adjacency list. The filter is applied to artifact/package names.
The reverse query also uses iterative BFS. In JSON mock mode, it indexes the
**entire** supplied mock repository, including nodes that cannot be reached
from the chosen package, so incoming edges are not incorrectly omitted.

In online mode, **a single artifact's POM does not identify every other
artifact which depends on it**. Therefore reverse queries are necessarily
limited to the discovered forward graph and explicitly say so. A complete
public-repository reverse-dependency index is outside this assignment's
input data and is not fabricated.

## Maven resolution limitations

The tool retrieves Maven POMs by URL using their exact declared coordinates.
It resolves local properties and this-POM dependency-management versions,
but does not implement full Maven semantics: inherited parent POMs,
imported BOMs, profiles, Maven ranges/dynamic versions, exclusions, mediation,
or effective scopes. Stage 3 online graphs may therefore be partial; the CLI
prints fetch errors and the `--max-nodes` limit (100 by default). Stage 2
prints all direct POM declarations, not Maven's resolved runtime dependencies.

For the required comparison with Maven's native tool, see `COMPARISON.md`.

## Tests and Git submission

```powershell
py -m unittest discover -s tests -v
```

The original GitHub repository already has the Stage 2 commit. The accompanying
`apply_stages.ps1` helper in the delivery ZIP adds Stages 1, 3, 4, and 5
as **four real, separate Conventional Commits**, with tests after each stage,
without overwriting `.git`. Use the supplied script from the ZIP and then
run `git push origin main`. Never commit `output/`, `__pycache__/` or binaries.
