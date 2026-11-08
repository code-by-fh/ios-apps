"""Merge public AltStore/SideStore sources without changing application metadata."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
import urllib.request


def https_url(value, label):
    if not isinstance(value, str):
        raise ValueError(label + ' must be a public HTTPS URL')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError(label + ' must be an HTTPS URL without credentials or fragment')
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def validate_app(app):
    if not isinstance(app, dict):
        raise ValueError('Each app must be an object')
    for key in ('name', 'bundleIdentifier', 'developerName', 'localizedDescription'):
        text(app.get(key), 'App ' + key)
    https_url(app.get('iconURL'), 'App iconURL')
    versions = app.get('versions')
    if not isinstance(versions, list) or not versions:
        raise ValueError('App versions must be a nonempty list')
    identities = set()
    for version in versions:
        if not isinstance(version, dict):
            raise ValueError('Each version must be an object')
        for key in ('version', 'buildVersion', 'date'):
            text(version.get(key), 'Version ' + key)
        try:
            datetime.fromisoformat(version['date'].replace('Z', '+00:00'))
        except ValueError as error:
            raise ValueError('Version date must be ISO 8601') from error
        identity = (version['version'], version['buildVersion'])
        if identity in identities:
            raise ValueError('Duplicate version/build in app ' + app['bundleIdentifier'])
        identities.add(identity)
        https_url(version.get('downloadURL'), 'Version downloadURL')
        if type(version.get('size')) is not int or version['size'] <= 0:
            raise ValueError('Version size must be a positive integer')
        for key in ('minOSVersion', 'maxOSVersion'):
            if key in version:
                text(version[key], key)
    permissions = app.get('appPermissions')
    if not isinstance(permissions, dict):
        raise ValueError('App appPermissions must be an object')
    entitlements = permissions.get('entitlements')
    if not isinstance(entitlements, list) or any(not isinstance(key, str) or not key for key in entitlements):
        raise ValueError('App entitlements must be a list of strings')
    privacy = permissions.get('privacy')
    if not isinstance(privacy, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                           for key, value in privacy.items()):
        raise ValueError('App privacy must be a dictionary of strings')


class HTTPSOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        https_url(newurl, 'Redirect URL')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_json(url):
    """Fetch anonymously; never pass GitHub credentials to source URLs."""
    https_url(url, 'Source URL')
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Floris-iOS-Apps-Catalog/1.0', 'Accept': 'application/json',
    })
    opener = urllib.request.build_opener(HTTPSOnlyRedirect())
    with opener.open(request, timeout=45) as response:
        # Bound accidental HTML/error responses and unexpectedly huge catalogs.
        raw = response.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError('Source exceeds the 16 MiB JSON limit')
    return json.loads(raw.decode('utf-8-sig'))


def aggregate(config, fetch=fetch_json):
    if not isinstance(config, dict):
        raise ValueError('Catalog configuration must be an object')
    result = {key: text(config.get(key), key) for key in ('name', 'identifier')}
    for key in ('sourceURL', 'website'):
        result[key] = https_url(config.get(key), key)
    for key in ('subtitle', 'description', 'tintColor'):
        if key in config:
            result[key] = text(config[key], key)
    if 'iconURL' in config:
        result['iconURL'] = https_url(config['iconURL'], 'Catalog iconURL')
    sources = config.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('Configuration sources must be a nonempty list')
    apps, seen, seen_urls = [], set(), set()
    for registry_entry in sources:
        if not isinstance(registry_entry, dict):
            raise ValueError('Each registered source must be an object')
        enabled = registry_entry.get('enabled', True)
        if not isinstance(enabled, bool):
            raise ValueError('Source enabled must be boolean')
        if not enabled:
            continue
        url = https_url(registry_entry.get('url'), 'Registered source URL')
        if url in seen_urls:
            raise ValueError('Duplicate registered source URL: ' + url)
        seen_urls.add(url)
        if registry_entry.get('license') not in ('open-source', 'closed-source'):
            raise ValueError('Source license must be open-source or closed-source')
        expected = registry_entry.get('expectedBundleIdentifiers')
        if expected is not None and (not isinstance(expected, list) or not expected
                                     or any(not isinstance(value, str) or not value for value in expected)
                                     or len(expected) != len(set(expected))):
            raise ValueError('expectedBundleIdentifiers must contain unique nonempty strings')
        source = fetch(url)
        if not isinstance(source, dict) or not isinstance(source.get('apps'), list) or not source['apps']:
            raise ValueError('Registered source must contain a nonempty apps list: ' + url)
        source_bundles = set()
        for app in source['apps']:
            validate_app(app)
            bundle = app['bundleIdentifier']
            if bundle in seen:
                raise ValueError('Duplicate bundle identifier across catalog: ' + bundle)
            seen.add(bundle)
            source_bundles.add(bundle)
            # Forward the complete object, including future schema fields.
            apps.append(app)
        if expected is not None and source_bundles != set(expected):
            raise ValueError('Registered source bundle identifiers differ from expected list: ' + url)
    if not apps:
        raise ValueError('Catalog contains no enabled applications')
    result.update(apps=apps, news=[])
    result.setdefault('iconURL', apps[0]['iconURL'])
    return result


def write_atomic(output, catalog):
    output = Path(output)
    serialized = json.dumps(catalog, indent=2, ensure_ascii=False) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=output.name + '.', suffix='.tmp', dir=output.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build(config_path, output, fetch=fetch_json):
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    catalog = aggregate(config, fetch)
    write_atomic(output, catalog)
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('apps.json'))
    parser.add_argument('--output', type=Path, default=Path('altstore-source.json'))
    args = parser.parse_args()
    catalog = build(args.config, args.output)
    print(f"Catalog written: {args.output} ({len(catalog['apps'])} apps)")


if __name__ == '__main__':
    main()
