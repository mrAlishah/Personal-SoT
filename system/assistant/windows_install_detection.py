"""Windows-native installation proof for Safe Update.

Python on Windows does not expose POSIX openat/O_NOFOLLOW/dir_fd. This module
keeps the same fail-closed routing intent with Win32 handles: reparse points
are rejected and accepted components are opened without FILE_SHARE_DELETE so
they stay pinned against rename/delete for the proof transaction.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

_REPARSE = 0x0400
_DIRECTORY = 0x0010
_DISK = 0x0001
_READ_ATTRIBUTES = 0x0080
_GENERIC_READ = 0x80000000
_SHARE_READ_WRITE = 0x00000001 | 0x00000002
_OPEN_EXISTING = 3
_OPEN_REPARSE_BACKUP = 0x00200000 | 0x02000000
_API = None


def _parts(relative: str):
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts:
        return None
    if any(
        part in ('.', '..') or not part or '/' in part or '\\' in part
        for part in path.parts
    ):
        return None
    return path.parts


def _api():
    global _API
    if os.name != 'nt':
        return None
    if _API is not None:
        return _API

    import ctypes
    from ctypes import wintypes

    class Info(ctypes.Structure):
        _fields_ = [
            ('attributes', wintypes.DWORD),
            ('created', wintypes.FILETIME),
            ('accessed', wintypes.FILETIME),
            ('written', wintypes.FILETIME),
            ('volume', wintypes.DWORD),
            ('size_high', wintypes.DWORD),
            ('size_low', wintypes.DWORD),
            ('links', wintypes.DWORD),
            ('index_high', wintypes.DWORD),
            ('index_low', wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    )
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(Info),
    )
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.GetFileType.argtypes = (wintypes.HANDLE,)
    kernel32.GetFileType.restype = wintypes.DWORD
    kernel32.ReadFile.argtypes = (
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    )
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    _API = (ctypes, wintypes, kernel32, Info)
    return _API


def _close(handle) -> None:
    api = _api()
    if api is None or handle is None:
        return
    try:
        api[2].CloseHandle(handle)
    except (OSError, ValueError):
        pass


def _open(path: Path, *, read: bool = False):
    api = _api()
    if api is None:
        return None
    ctypes, wintypes, kernel32, info_type = api
    handle = kernel32.CreateFileW(
        str(path),
        _READ_ATTRIBUTES | (_GENERIC_READ if read else 0),
        _SHARE_READ_WRITE,
        None,
        _OPEN_EXISTING,
        _OPEN_REPARSE_BACKUP,
        None,
    )
    if handle in (None, wintypes.HANDLE(-1).value):
        return None

    info = info_type()
    if (
        not kernel32.GetFileInformationByHandle(handle, ctypes.byref(info))
        or info.attributes & _REPARSE
    ):
        _close(handle)
        return None

    identity = (
        int(info.volume),
        (int(info.index_high) << 32) | int(info.index_low),
    )
    size = (int(info.size_high) << 32) | int(info.size_low)
    return handle, info, identity, size


class _Pin:
    def __init__(self, path: Path, identity, handle):
        self.path = path
        self.identity = identity
        self.handles = [handle]

    def close(self) -> None:
        while self.handles:
            _close(self.handles.pop())


def _pin(root):
    path = Path(os.path.abspath(os.fspath(root)))
    opened = _open(path)
    if opened is None:
        return None
    handle, info, identity, _size = opened
    if not info.attributes & _DIRECTORY:
        _close(handle)
        return None
    return _Pin(path, identity, handle)


def _walk(pin: _Pin, relative: str, *, read: bool = False):
    parts = _parts(relative)
    if not parts:
        return None
    path = pin.path
    opened = None
    for index, part in enumerate(parts):
        path = path / part
        opened = _open(path, read=read and index == len(parts) - 1)
        if opened is None:
            return None
        pin.handles.append(opened[0])
        if index < len(parts) - 1 and not opened[1].attributes & _DIRECTORY:
            return None
    return opened


def _regular(pin: _Pin, relative: str) -> bool:
    opened = _walk(pin, relative)
    return bool(
        opened
        and not opened[1].attributes & _DIRECTORY
        and _api()[2].GetFileType(opened[0]) == _DISK
    )


def _read(pin: _Pin, relative: str, *, limit: int = 4096):
    opened = _walk(pin, relative, read=True)
    if (
        opened is None
        or opened[1].attributes & _DIRECTORY
        or _api()[2].GetFileType(opened[0]) != _DISK
    ):
        return None

    ctypes, wintypes, kernel32, _info_type = _api()
    remaining = min(opened[3], limit)
    chunks = []
    while remaining:
        amount = min(65536, remaining)
        buffer = ctypes.create_string_buffer(amount)
        count = wintypes.DWORD()
        if not kernel32.ReadFile(
            opened[0], buffer, amount, ctypes.byref(count), None
        ):
            return None
        if not count.value:
            break
        chunks.append(buffer.raw[:count.value])
        remaining -= count.value
    return b''.join(chunks)


def detect(root, marker_paths) -> str:
    """Return git/zip/unknown from Windows-native pinned evidence."""
    if os.name != 'nt':
        return 'unknown'

    pin = _pin(root)
    if pin is None:
        return 'unknown'
    try:
        for marker in marker_paths:
            if not _regular(pin, str(marker).replace('\\', '/')):
                return 'unknown'

        dotgit = _walk(pin, '.git')
        is_git = False
        if dotgit:
            if dotgit[1].attributes & _DIRECTORY:
                is_git = True
            else:
                data = _read(pin, '.git')
                try:
                    first_line = (data or b'').decode('utf-8').splitlines()[0]
                except (UnicodeDecodeError, IndexError):
                    first_line = ''
                is_git = (
                    first_line.startswith('gitdir:')
                    and bool(first_line[len('gitdir:'):].strip())
                )

        current = _open(pin.path)
        if current is None:
            return 'unknown'
        try:
            if (
                not current[1].attributes & _DIRECTORY
                or current[2] != pin.identity
            ):
                return 'unknown'
        finally:
            _close(current[0])

        return 'git' if is_git else 'zip'
    finally:
        pin.close()
