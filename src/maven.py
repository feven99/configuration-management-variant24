"""Read direct Maven dependencies from a POM without external packages."""

from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen
import re
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Dependency:
    """A direct dependency declared in a Maven POM."""

    group_id: str
    artifact_id: str
    version: str
    scope: str
    optional: bool


def pom_url(repository: str, group: str, artifact: str, version: str) -> str:
    """Build a Maven-layout POM URL for a coordinate."""
    group_path = group.replace('.', '/')
    return (f"{repository.rstrip('/')}/{group_path}/{artifact}/"
            f"{version}/{artifact}-{version}.pom")


def fetch_pom(url: str) -> bytes:
    """Fetch a POM over HTTPS with a request timeout and size limit."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError('Repository must use a valid HTTPS URL')
    try:
        with urlopen(url, timeout=15) as response:
            data = response.read(2_000_001)
    except HTTPError as exc:
        raise ValueError(f'HTTP {exc.code} while requesting {url}') from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError(f'Cannot access Maven repository: {exc}') from exc
    if len(data) > 2_000_000:
        raise ValueError('POM exceeds the 2 MB size limit')
    return data


def child(node: ET.Element, name: str) -> ET.Element | None:
    """Find a direct XML child regardless of namespace."""
    return next((item for item in node if item.tag.split('}')[-1] == name),
                None)


def value(node: ET.Element | None, name: str) -> str:
    """Return text from a named direct child."""
    found = child(node, name) if node is not None else None
    return (found.text or '').strip() if found is not None else ''


def resolve(text: str, props: dict[str, str]) -> str:
    """Resolve simple Maven ${property} references, including nested ones."""
    pattern = re.compile(r'\$\{([^{}]+)\}')
    for _ in range(12):
        updated = pattern.sub(lambda match: props.get(match.group(1),
                                                       match.group(0)), text)
        if updated == text:
            break
        text = updated
    return text


def _pom_properties(root):
    """Find local property declarations and key Maven project properties."""
    parent = child(root, 'parent')
    group = value(root, 'groupId') or value(parent, 'groupId')
    version = value(root, 'version') or value(parent, 'version')
    props = {
        'project.groupId': group, 'pom.groupId': group,
        'project.version': version, 'pom.version': version,
        'project.parent.version': value(parent, 'version'),
        'parent.version': value(parent, 'version'),
    }
    properties = child(root, 'properties')
    if properties is not None:
        for item in properties:
            props[item.tag.split('}')[-1]] = (item.text or '').strip()
    return props


def _managed_versions(root, props):
    """Read versions declared in this POM's dependencyManagement."""
    managed = {}
    management = child(root, 'dependencyManagement')
    container = (child(management, 'dependencies')
                 if management is not None else None)
    if container is not None:
        for item in container:
            if item.tag.split('}')[-1] == 'dependency':
                key = (resolve(value(item, 'groupId'), props),
                       resolve(value(item, 'artifactId'), props))
                managed[key] = resolve(value(item, 'version'), props)
    return managed


def _parse_direct(root, props, managed):
    """Extract direct entries without descending into nested POM sections."""
    direct = child(root, 'dependencies')
    if direct is None:
        return []
    result = []
    for item in direct:
        if item.tag.split('}')[-1] != 'dependency':
            continue
        group = resolve(value(item, 'groupId'), props)
        artifact = resolve(value(item, 'artifactId'), props)
        version = resolve(value(item, 'version'), props)
        if not group or not artifact:
            raise ValueError('Dependency missing groupId or artifactId')
        version = version or managed.get((group, artifact), '')
        result.append(Dependency(
            group, artifact, version or '(managed externally)',
            resolve(value(item, 'scope') or 'compile', props),
            value(item, 'optional').lower() == 'true'))
    return result


def parse_pom(data: bytes) -> list[Dependency]:
    """Parse directly declared dependencies without Maven tooling."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f'Invalid POM XML: {exc}') from exc
    if root.tag.split('}')[-1] != 'project':
        raise ValueError('POM root element must be <project>')
    props = _pom_properties(root)
    managed = _managed_versions(root, props)
    return _parse_direct(root, props, managed)


def local_pom(path: str) -> bytes:
    """Read a local POM for deterministic offline tests."""
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f'Cannot read local POM: {exc}') from exc
