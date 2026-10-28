# Configuration Management — Practice 2, Variant 24

## Task

Stage 2: retrieve and print the **direct dependencies** of a Java Maven
artifact at a specified version, using an INI configuration and the URL of a
Maven repository. Maven, pip packages, and third-party XML/HTTP libraries are
not used. The project uses only Python 3.10+ standard-library modules.

## Configuration

Edit `config.ini`:

- `group_id`: Maven group ID (e.g., `org.apache.commons`).
- `artifact_id`: Maven artifact ID (e.g., `commons-lang3`).
- `version`: exact Maven version (e.g., `3.12.0`).
- `repository`: HTTPS base URL of a Maven-layout repository.
- `test_mode`: `true` to read an offline POM; otherwise `false`.
- `test_path`: path to a local POM when test mode is on.
- `ascii_tree`: Stage 1 setting, reserved for later visualization.
- `filter_substring`: Stage 1 setting, reserved for Stage 3.

Maven identifies packages by `group_id:artifact_id:version`, so group and
artifact are separate configuration fields.

## Run

```bash
./run.sh
# or:
python3 -m src.main --config config.ini
```

For a reproducible offline demonstration, run `python3 -m src.main --config config.offline.ini`; this outputs:

```text
Direct dependencies of org.example:demo:1.0.0:
  - junit:junit:4.13.2 [scope=test]
  - org.slf4j:slf4j-api:2.0.9 [scope=compile]
Total: 2
```

The offline config matches the coordinates declared by the sample POM.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Implementation notes and limitations

- Retrieves `group/path/artifact/version/artifact-version.pom` directly over
  HTTPS, then parses XML using `xml.etree.ElementTree`.
- Only top-level `<project><dependencies>` are returned; dependencies inside
  `<dependencyManagement>` are not counted as direct dependencies.
- Includes dependency scope and optional flag. Resolves straightforward POM
  properties and versions managed in the same POM.
- Parent POMs, imported BOMs, Maven profiles, activated properties, dynamic
  versions, and full effective-POM inheritance are **not** resolved. An
  unspecified version not managed locally is marked `(managed externally)`.
- Output includes all directly declared dependencies, including test,
  provided, and optional dependencies; this is *not* the resolved runtime
  dependency graph.
- Network errors, invalid configuration and malformed POMs return an error.

## Git submission

Initialize your public repo and use a Conventional Commit for Stage 2:

```bash
git init
git add README.md .gitignore config.ini config.offline.ini src tests examples run.sh
git commit -m "feat(maven): collect direct dependencies from POM files"
```

Push it to your public Git hosting account separately. Stage 3 and subsequent
features have intentionally not been implemented.
