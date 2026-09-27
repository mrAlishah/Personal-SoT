"""Host-side read-only source boundary, never a standalone AI instruction parser."""
from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re

from system.context.access import permitted
from system.routing.runtime_naming import classify_bootstrap_invocation
from system.routing.source_scope import resolve_scope
from system.validation.validate_public import contains_raw_secret


class SourceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class Snapshot:
    source: str
    revision: str
    private: bool
    tree: str = ''


@dataclass(frozen=True)
class Result:
    success: bool
    message: str
    content: str = field(default='', repr=False)
    provenance: tuple[str, str, str] | None = None
    write_applied: bool = False
    validation_ran: bool = False
    validation_passed: bool = False


def safe_path(path: str) -> bool:
    return bool(re.fullmatch(r'[a-z0-9_]+(?:/[a-z0-9_]+)*\.md', path))


class SourceSession:
    """Construct only from trusted host binding, not prompt or source fields.

    Transport.resolve() probes current state. Transport.read(snapshot, path,
    metadata_only=...) must be pinned, bounded, non-logging and host-isolated.
    This is the source stage of runtime_bootstrap, not full profile activation.
    """

    def __init__(self, transport, *, personal_owner=False, host_read=True,
                 entrypoint='workspace/adapters/runtime_entrypoint.md'):
        self.transport = transport
        self.personal_owner = personal_owner
        self.host_read = host_read
        self.entrypoint = entrypoint
        self.snapshot = None

    def _read(self, snapshot, path, *, metadata_only=False):
        if not safe_path(path):
            raise SourceUnavailable()
        value = self.transport.read(snapshot, path, metadata_only=metadata_only)
        if not isinstance(value, str) or len(value.encode('utf-8')) > 65536:
            raise SourceUnavailable()
        if contains_raw_secret(value):
            raise SourceUnavailable()
        return value

    def reanchor(self, command='@do:sot') -> Result:
        self.snapshot = None
        try:
            invocation = classify_bootstrap_invocation(command)
            if invocation is None or not self.host_read:
                raise SourceUnavailable()
            snapshot = self.transport.resolve()
            entrypoint = self._read(snapshot, self.entrypoint)
            runtime = re.findall(r'^runtime_contract: (system/[a-z0-9_/]+\.md)$', entrypoint, re.M)
            if len(runtime) != 1:
                raise SourceUnavailable()
            self._read(snapshot, runtime[0])
            self.snapshot = snapshot
            return Result(True, invocation.diagnostic or 'Canonical source resolved. Runtime composition is still required.',
                          provenance=(snapshot.source, snapshot.revision, self.entrypoint))
        except (SourceUnavailable, ValueError, OSError):
            return Result(False, 'Canonical source is unavailable. Check your connection and trusted source configuration.')

    def lookup(self, scope: str, atom: str, *, required=True) -> Result:
        """One already-selected owner; caller applies canonical query planning.

        No memory input, broad search, persistence, or negative-result cache.
        'Unavailable' never means a fact is absent from all plausible owners.
        """
        try:
            snapshot = self.snapshot
            if snapshot is None or not self.host_read or not required or not safe_path(atom):
                raise SourceUnavailable()
            registry = self._read(snapshot, 'system/routing/context_registry.md')
            scope_path = resolve_scope(registry, scope)
            if scope_path is None:
                raise SourceUnavailable()
            path = scope_path + '/' + atom
            header = self._read(snapshot, path, metadata_only=True)
            if not permitted(header, path=path, scope_path=scope_path,
                             host_read=self.host_read, required=required,
                             personal_owner=self.personal_owner, private_instance=snapshot.private):
                raise SourceUnavailable()
            content = self._read(snapshot, path)
            # Recheck returned content, not only earlier metadata.
            if not permitted(content, path=path, scope_path=scope_path,
                             host_read=self.host_read, required=required,
                             personal_owner=self.personal_owner, private_instance=snapshot.private):
                raise SourceUnavailable()
            return Result(True, 'Current canonical atom loaded.', content,
                          (snapshot.source, snapshot.revision, path))
        except (SourceUnavailable, ValueError, OSError):
            return Result(False, 'The requested context is unavailable. Check source access or select another authorized owner.')
