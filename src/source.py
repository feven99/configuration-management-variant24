"""Convert Maven POM dependency records into graph edges."""

from .maven import fetch_pom, parse_pom, pom_url


def maven_source(repository):
    """Return a callback that retrieves direct dependencies for one artifact."""
    def children(coordinate):
        """Load the exact-version POM and return its declared dependencies."""
        try:
            group, artifact, version = coordinate.split(':')
        except ValueError as exc:
            raise ValueError(f'Invalid Maven coordinate: {coordinate}') from exc
        url = pom_url(repository, group, artifact, version)
        dependencies = parse_pom(fetch_pom(url))
        result = []
        for dep in dependencies:
            if dep.version == '(managed externally)':
                continue
            result.append(f'{dep.group_id}:{dep.artifact_id}:{dep.version}')
        return result
    return children
