"""Register the public distribution feed of an open- or closed-source app."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from build_catalog import write_atomic


def register(config_path, repository, license_kind, bundle_identifiers=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}', repository):
        raise ValueError('Use a GitHub owner/repository name without extra paths or credentials.')
    if license_kind not in ('open-source', 'closed-source'):
        raise ValueError('License must be open-source or closed-source.')
    if bundle_identifiers and any(not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', bundle) for bundle in bundle_identifiers):
        raise ValueError('Bundle identifiers must be dot-separated identifiers.')
    config_path = Path(config_path)
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    url = f'https://github.com/{repository}/releases/latest/download/altstore-source.json'
    entries = config['sources']
    matching = [entry for entry in entries if entry['url'] == url]
    if len(matching) > 1:
        raise ValueError('The registry already contains duplicate entries for this app source.')
    entry = matching[0] if matching else {'url': url}
    entry.update(license=license_kind, enabled=True)
    if bundle_identifiers is not None:
        entry['expectedBundleIdentifiers'] = list(dict.fromkeys(bundle_identifiers))
    if not matching:
        entries.append(entry)
    write_atomic(config_path, config)
    return url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--license', required=True, choices=['open-source', 'closed-source'], dest='license_kind')
    parser.add_argument('--bundle-id', action='append', dest='bundle_identifiers')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'apps.json')
    args = parser.parse_args()
    print('Registered: ' + register(args.config, args.repository, args.license_kind, args.bundle_identifiers))
    print('Next: commit and push apps.json, then manually run the Refresh app catalog workflow on main.')


if __name__ == '__main__':
    main()
