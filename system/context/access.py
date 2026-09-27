"""Executable access_contract boundary; arguments are trusted host state."""
from pathlib import PurePosixPath

from system.validation.validate_v1 import frontmatter_lines, simple_frontmatter


def permitted(header: str, *, path: str, scope_path: str, host_read: bool,
              required: bool, personal_owner: bool, private_instance: bool) -> bool:
    atom, scope = PurePosixPath(path), PurePosixPath(scope_path)
    if (not host_read or not required or atom.is_absolute() or scope.is_absolute()
            or '..' in atom.parts or '..' in scope.parts
            or not scope.is_relative_to('workspace/context')
            or not atom.is_relative_to(scope) or atom.suffix != '.md'):
        return False
    lines = frontmatter_lines(header)
    if lines is None or sum(line.startswith('ai_access:') for line in lines) != 1:
        return False
    access = simple_frontmatter(header).get('ai_access')
    if access == 'allow':
        return True
    return (access == 'restricted' and personal_owner and private_instance
            and scope.is_relative_to('workspace/context/personal')
            and atom.is_relative_to('workspace/context/personal'))
