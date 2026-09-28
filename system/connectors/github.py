"""Read-only GitHub transport; execute inside the host gate, not the model.

Uses the host's installed gh and credential store. No credentials in arguments,
temporary files, logs, exceptions, or canonical configuration.
"""
import base64
import hashlib
import json
import re
import subprocess
from urllib.parse import quote

from system.connectors.source import SourceBinding, Snapshot, SourceUnavailable, safe_path


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
        raise SourceUnavailable()
    return value


class GitHubSource:
    def __init__(self, repository: str, *, ref: str | None = None, runner=subprocess.run):
        if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Use one exact owner/repository binding')
        self.repository = repository
        self.ref = ref
        self.binding = SourceBinding(repository, ref)
        self.runner = runner

    def _api(self, suffix=''):
        try:
            result = self.runner(
                ['gh', 'api', '--include', '--hostname', 'github.com',
                 '/repos/' + self.repository + suffix],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, timeout=30, check=False,
            )
            response = result.stdout.replace('\r\n', '\n')
            status = re.match(r'HTTP/\S+ (\d{3})', response)
            if status:
                code = int(status.group(1))
                if code in (401, 403):
                    raise SourceUnavailable(reason='source_unauthorized')
                response = response.partition('\n\n')[2]
            if result.returncode != 0:
                raise SourceUnavailable()
            if len(response) > 2_000_000:
                raise SourceUnavailable(reason='partial_coverage')
            return json.loads(response)
        except FileNotFoundError:
            raise SourceUnavailable(reason='capability_unavailable') from None
        except (OSError, subprocess.SubprocessError, ValueError):
            raise SourceUnavailable('Source transport unavailable') from None

    def resolve(self) -> Snapshot:
        try:
            repository = self._api()
            if repository['full_name'].casefold() != self.repository.casefold():
                raise SourceUnavailable(reason='source_unresolved')
            if not isinstance(repository['private'], bool):
                raise SourceUnavailable()
            ref = self.ref or repository['default_branch']
            commit = self._api('/commits/' + quote(ref, safe=''))
            return Snapshot(self.repository, _sha(commit['sha']), repository['private'],
                            _sha(commit['commit']['tree']['sha']), ref)
        except (KeyError, TypeError, AttributeError):
            raise SourceUnavailable(reason='source_unresolved') from None

    def read(self, snapshot: Snapshot, path: str, *, metadata_only=False) -> str:
        try:
            if snapshot.source != self.repository or not safe_path(path):
                raise SourceUnavailable()
            _sha(snapshot.revision)
            tree = _sha(snapshot.tree)
            parts = path.split('/')
            for index, part in enumerate(parts):
                response = self._api('/git/trees/' + tree)
                if response.get('truncated') is not False:
                    raise SourceUnavailable(reason='partial_coverage')
                entries = [entry for entry in response['tree'] if entry['path'] == part]
                if len(entries) != 1:
                    raise SourceUnavailable()
                entry = entries[0]
                final = index == len(parts) - 1
                if (entry['type'], entry['mode']) not in (
                    {('blob', '100644'), ('blob', '100755')} if final else {('tree', '040000')}
                ):
                    raise SourceUnavailable()
                tree = _sha(entry['sha'])
            blob = self._api('/git/blobs/' + tree)
            if blob['sha'] != tree or blob['encoding'] != 'base64' or not 0 <= blob['size'] <= 65536:
                raise SourceUnavailable()
            raw = base64.b64decode(''.join(blob['content'].split()), validate=True)
            if len(raw) != blob['size']:
                raise SourceUnavailable()
            digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if digest != tree:
                raise SourceUnavailable()
            content = raw.decode('utf-8')
            if metadata_only:
                lines = content.splitlines()
                if not lines or lines[0] != '---':
                    return ''
                for index, line in enumerate(lines[1:65], 1):
                    if line == '---':
                        return '\n'.join(lines[:index + 1])
                return ''
            return content
        except (KeyError, TypeError, ValueError, AttributeError):
            raise SourceUnavailable('Source read unavailable') from None
