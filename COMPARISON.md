# Stage 5: comparison with the native Maven dependency tool

The program reads raw artifact POMs and follows all directly declared
`<dependencies>`. Maven's effective dependency tree is **not** the same data.

## Independent reproduction (requires Maven installed separately)

First run the supplied program on the live repository:

```powershell
py -m src.main --config config.ini --stage 2
py -m src.main --config config.ini --stage 5 --max-nodes 40 --no-open
```

Then compare against Maven's own resolution for the sample consumer project:

```powershell
mvn -f examples/comparison-pom.xml dependency:tree
```

To examine the root artifact itself, also inspect the effective POM after
creating an appropriate local Maven consumer or Maven project:

```powershell
mvn -f examples/comparison-pom.xml help:effective-pom
```

## What should differ and why

| This project | Standard `mvn dependency:tree` |
| --- | --- |
| Shows POM-declared direct edges | Shows dependency resolution as used by a consumer project |
| Traverses declared test/provided/optional edges | Applies transitivity, scope and optionality rules |
| Does not resolve inherited parent dependencyManagement and imported BOMs | Uses effective POM and dependency management |
| Keeps cycles as edges (visited set stops repeated expansion) | Maven normally resolves valid artifact dependency trees and mediation |
| Displays all declared version coordinates separately | Resolves version conflicts, exclusions, mediation and nearest-wins rules |
| Limits graph to discovered dependencies | Derives the graph from a complete project's effective dependencies |

The supplied consumer POM depends on `commons-lang3:3.12.0`; its Maven output
will include the consumer root, and its dependency traversal can differ from
raw dependencies of the `commons-lang3` artifact's **own** POM. Therefore a
literal count comparison between the two roots is not equivalent.

**Verification status:** The Python unit tests, sample graph visualizations
and offline POM demonstration have been executed in the delivery environment.
The user's prior run demonstrated live repository access. Maven itself is not
installed in the delivery environment, so no native Maven command output is
claimed here. Run the commands above to complete the external comparison on
an installation with Maven available, and save the observed output for class.
## Actual Comparison Results

Date: 28 October 2026

### Python Application

The Python application analyzed `org.apache.commons:commons-lang3:3.12.0` and found 7 directly declared dependencies in its POM file. The dependencies were reported with test scope.

### Apache Maven 3.10.0

Maven was executed using `examples/comparison-pom.xml` with the `dependency:tree` goal.

```text
org.example:graph-comparison:jar:1.0.0
\- org.apache.commons:commons-lang3:jar:3.12.0:compile
BUILD SUCCESS
```

### Explanation of Differences

The Python application reads raw POM dependency declarations, including test dependencies. Maven builds the resolved dependency tree for the consuming project and applies dependency scope and transitivity rules.

Therefore, the Python application reported 7 declared dependencies for commons-lang3, while Maven showed commons-lang3 as one direct compile dependency of the comparison project. These outputs describe different dependency relationships and should not be interpreted as equivalent graphs.

### Conclusion

The Python implementation successfully retrieves Maven POM dependencies and produces dependency graphs. The Maven comparison demonstrates the difference between raw POM metadata and Maven's effective dependency resolution.

