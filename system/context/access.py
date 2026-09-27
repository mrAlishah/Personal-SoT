"""Executable access_contract boundary; arguments are trusted host state."""
from pathlib import PurePosixPath
import re

from system.validation.validate_v1 import frontmatter_lines, simple_frontmatter


def permitted(header: str, *, path: str, scope_path: str, host_read: bool,
              required: bool, personal_owner: bool, private_instance: bool) -> bool:
    atom, scope = PurePosixPath(path), PurePosixPath(scope_path)
    if (host_read is not True or required is not True or atom.is_absolute() or scope.is_absolute()
            or '..' in atom.parts or '..' in scope.parts
            or not scope.is_relative_to('workspace/context')
            or not atom.is_relative_to(scope) or atom.suffix != '.md'):
        return False
    lines = frontmatter_lines(header)
    if lines is None:
        return False
    declarations = [line for line in lines
                    if re.match(r'''^\s*["']?ai_access["']?\s*:''', line)]
    if len(declarations) != 1 or not declarations[0].startswith('ai_access:'):
        return False
    access = simple_frontmatter(header).get('ai_access')
    if access == 'allow':
        return True
    return (access == 'restricted' and personal_owner is True and private_instance is True
            and scope.is_relative_to('workspace/context/personal')
            and atom.is_relative_to('workspace/context/personal'))
