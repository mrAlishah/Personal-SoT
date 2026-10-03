"""Host implementation of system/adapters/source_access_contract.md."""
from dataclasses import dataclass, field
from typing import Literal
import re

from system.context.access import permitted
from system.routing.runtime_naming import classify_bootstrap_invocation, is_profile_identity
from system.routing.source_scope import resolve_scope
from system.validation.validate_public import contains_raw_secret


Failure = Literal['source_unavailable', 'source_unauthorized', 'source_unresolved',
                  'capability_unavailable', 'partial_coverage']

_MESSAGES = {
    'source_unavailable': 'The canonical source cannot currently be read. Check your connection.',
    'source_unauthorized': 'Required access is not authorized. Check trusted host permissions.',
    'source_unresolved': 'One canonical source or owner could not be resolved. Check the trusted mapping.',
    'capability_unavailable': 'The host does not expose the required source operation.',
    'partial_coverage': 'Only part of the requested source could be inspected. No absence conclusion is justified.',
}


class SourceUnavailable(Exception):
    def __init__(self, message='', *, reason: Failure = 'source_unavailable'):
        self.reason = reason if reason in _MESSAGES else 'source_unavailable'
        super().__init__(_MESSAGES[self.reason])


@dataclass(frozen=True)
class SourceBinding:
    source: str
    selector: str | None = None


@dataclass(frozen=True)
class Snapshot:
    source: str
    revision: str | None
    private: bool
    tree: str = ''
    selector: str | None = None


@dataclass(frozen=True)
class Provenance:
    source_identity: str
    selected_ref: str | None
    resolved_revision: str | None
    logical_scope: str | None
    canonical_path: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Result:
    success: bool
    message: str
    content: str = field(default='', repr=False)
    provenance: Provenance | None = None
    failure: Failure | None = None
    write_applied: bool = False
    validation_ran: bool = False
    validation_passed: bool = False


def safe_path(path: str) -> bool:
    parts = path.split('/')
    if parts[:2] == ['workspace', 'profiles'] and len(parts) >= 3:
        if not path.endswith('.md'):
            return False
        identity = '/'.join(parts[2:])[:-len('.md')]
        return is_profile_identity(identity)
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
        self.binding = getattr(transport, 'binding', None)
        self.personal_owner = personal_owner
        self.host_read = host_read
        self.entrypoint = entrypoint
        self.snapshot = None

    def _resolve(self):
        if (not isinstance(self.binding, SourceBinding)
                or not isinstance(self.binding.source, str) or not self.binding.source
                or (self.binding.selector is not None and not isinstance(self.binding.selector, str))):
            raise SourceUnavailable(reason='source_unresolved')
        if self.host_read is not True:
            raise SourceUnavailable(reason='source_unauthorized')
        if not callable(getattr(self.transport, 'resolve', None)) or not callable(getattr(self.transport, 'read', None)):
            raise SourceUnavailable(reason='capability_unavailable')
        snapshot = self.transport.resolve()
        if (not isinstance(snapshot, Snapshot) or snapshot.source != self.binding.source
                or (self.binding.selector is not None and snapshot.selector != self.binding.selector)
                or (snapshot.revision is not None and (not isinstance(snapshot.revision, str) or not snapshot.revision))
                or (snapshot.selector is not None and not isinstance(snapshot.selector, str))
                or not isinstance(snapshot.private, bool)):
            raise SourceUnavailable(reason='source_unresolved')
        return snapshot

    def _provenance(self, snapshot, path, scope=None):
        warnings = () if snapshot.revision is not None else (
            'Revision unavailable; the requested source was reread, not proven unchanged.',)
        return Provenance(snapshot.source, snapshot.selector, snapshot.revision, scope, path, warnings)

    def _anchor(self, snapshot):
        self.snapshot = None
        entrypoint = self._read(snapshot, self.entrypoint)
        runtime = re.findall(r'^runtime_contract: (system/[a-z0-9_/]+\.md)$', entrypoint, re.M)
        if len(runtime) != 1:
            raise SourceUnavailable(reason='source_unresolved')
        self._read(snapshot, runtime[0])
        self.snapshot = snapshot

    def _failure(self, reason):
        return Result(False, _MESSAGES[reason], failure=reason)

    def _read(self, snapshot, path, *, metadata_only=False):
        if not safe_path(path):
            raise SourceUnavailable()
        value = self.transport.read(snapshot, path, metadata_only=metadata_only)
        if not isinstance(value, str):
            raise SourceUnavailable()
        if len(value.encode('utf-8')) > 65536:
            raise SourceUnavailable(reason='partial_coverage')
        if contains_raw_secret(value):
            raise SourceUnavailable()
        return value

    def reanchor(self, command='@do:sot') -> Result:
        self.snapshot = None
        try:
            invocation = classify_bootstrap_invocation(command)
            if invocation is None:
                raise SourceUnavailable(reason='source_unresolved')
            snapshot = self._resolve()
            self._anchor(snapshot)
            return Result(True, invocation.diagnostic or 'Canonical source resolved. Runtime composition is still required.',
                          provenance=self._provenance(snapshot, self.entrypoint))
        except SourceUnavailable as error:
            return self._failure(error.reason)
        except (ValueError, OSError, TypeError, AttributeError):
            return self._failure('source_unavailable')

    def lookup(self, scope: str, atom: str, *, required=True) -> Result:
        """One already-selected owner; caller applies canonical query planning.

        No memory input, broad search, persistence, or negative-result cache.
        'Unavailable' never means a fact is absent from all plausible owners.
        """
        try:
            if self.snapshot is None or required is not True or not safe_path(atom):
                raise SourceUnavailable()
            previous = self.snapshot
            self.snapshot = None
            snapshot = self._resolve()
            if snapshot != previous or snapshot.revision is None:
                self._anchor(snapshot)
            else:
                self.snapshot = snapshot
            registry = self._read(snapshot, 'system/routing/context_registry.md')
            scope_path = resolve_scope(registry, scope)
            if scope_path is None:
                raise SourceUnavailable(reason='source_unresolved')
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
                          self._provenance(snapshot, path, scope))
        except SourceUnavailable as error:
            return self._failure(error.reason)
        except (ValueError, OSError, TypeError, AttributeError):
            return self._failure('source_unavailable')
