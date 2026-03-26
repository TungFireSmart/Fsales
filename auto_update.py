import json
import os
import subprocess
import tempfile
import urllib.request
from urllib.error import URLError, HTTPError

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


def _parse_version(v: str):
    parts = []
    for p in str(v).strip().split('.'):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote_version: str, current_version: str) -> bool:
    return _parse_version(remote_version) > _parse_version(current_version)


class AutoUpdater:
    """
    Simple startup updater:
    - Reads update_config.json for manifest URL
    - Fetches manifest JSON: {version, installer_url, notes}
    - If newer, downloads installer and launches it
    """

    def __init__(self, app_dir: str, current_version: str):
        self.app_dir = app_dir
        self.current_version = current_version
        p1 = os.path.join(app_dir, 'update_config.json')
        p2 = os.path.join(app_dir, '_internal', 'update_config.json')
        self.config_path = p1 if os.path.exists(p1) else p2

    def _load_config(self):
        if not os.path.exists(self.config_path):
            return None
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _fetch_manifest(self, manifest_url: str):
        req = urllib.request.Request(manifest_url, headers={'User-Agent': 'FSales-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = resp.read().decode('utf-8-sig', errors='ignore')
        return json.loads(data)

    def get_manifest_info(self):
        cfg = self._load_config()
        if not cfg:
            return None

        manifest_url = (cfg.get('manifest_url') or '').strip()
        if not manifest_url:
            return None

        try:
            manifest = self._fetch_manifest(manifest_url)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            return None
        except Exception:
            return None

        remote_version = str(manifest.get('version', '')).strip()
        installer_url = str(manifest.get('installer_url', '')).strip()
        notes = str(manifest.get('notes', '')).strip()

        if not remote_version or not installer_url:
            return None

        return {
            'version': remote_version,
            'installer_url': installer_url,
            'notes': notes,
        }

    def check(self):
        info = self.get_manifest_info()
        if not info:
            return None
        if not is_newer(info['version'], self.current_version):
            return None
        return info

    def download_installer(self, installer_url: str):
        fd, path = tempfile.mkstemp(prefix='fsales-update-', suffix='.exe')
        os.close(fd)
        req = urllib.request.Request(installer_url, headers={'User-Agent': 'FSales-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp, open(path, 'wb') as f:
            f.write(resp.read())
        return path

    def launch_installer(self, installer_path: str):
        """Launch installer reliably on Windows without shell-quote pitfalls."""
        if not installer_path or not os.path.exists(installer_path):
            raise FileNotFoundError(f'Installer not found: {installer_path}')

        # Start detached so current app can exit immediately.
        creationflags = DETACHED_PROCESS | CREATE_NO_WINDOW
        subprocess.Popen([installer_path], close_fds=True, creationflags=creationflags)
