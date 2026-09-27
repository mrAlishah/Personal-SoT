"""Exact registered scope selection; no fallback or owner invention."""
from system.validation.validate_v1 import SCOPE_RE, context_registry_entries


def resolve_scope(registry: str, scope: str) -> str | None:
    if not SCOPE_RE.fullmatch(scope):
        return None
    parts = scope.split('/')
    if parts[0] == 'personal':
        if len(parts) > 1 and (len(parts) < 3 or parts[1] != 'projects'):
            return None
        expected = 'workspace/context/' + scope
    elif parts[0] == 'org' and len(parts) >= 2:
        if len(parts) > 2 and (len(parts) < 4 or parts[2] != 'projects'):
            return None
        expected = 'workspace/context/organizations/' + '/'.join(parts[1:])
    else:
        return None
    targets = [target.rstrip('/') for name, target in context_registry_entries(registry) if name == scope]
    return expected if targets == [expected] else None
