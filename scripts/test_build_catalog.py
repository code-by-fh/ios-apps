import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_catalog import aggregate, build, fetch_json, https_url, write_atomic


def app(bundle='dev.example.counter'):
    return {'name': 'Counter', 'bundleIdentifier': bundle, 'developerName': 'Example',
            'localizedDescription': 'Offline counter.', 'iconURL': 'https://example.com/icon.png',
            'versions': [{'version': '0.1.0', 'buildVersion': '3', 'date': '2026-11-08',
                          'downloadURL': 'https://example.com/3.ipa', 'size': 6165711,
                          'minOSVersion': '15.0'},
                         {'version': '0.1.0', 'buildVersion': '2', 'date': '2026-11-07',
                          'downloadURL': 'https://example.com/2.ipa', 'size': 6000000}],
            'appPermissions': {'entitlements': ['com.apple.security.application-groups'],
                               'privacy': {'NSCameraUsageDescription': 'Scan QR codes.'}},
            'futureSchemaField': {'preserve': True}}


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.config = {'name': 'Floris Apps', 'identifier': 'dev.codebyfh.iosapps',
                       'sourceURL': 'https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json',
                       'website': 'https://github.com/code-by-fh/ios-apps',
                       'sources': [{'url': 'https://example.com/open.json', 'license': 'open-source', 'enabled': True}]}
        self.source = {'apps': [app()]}

    def test_preserves_versions_permissions_and_unknown_fields(self):
        snapshot = copy.deepcopy(self.source)
        catalog = aggregate(self.config, lambda url: self.source)
        self.assertEqual(catalog['apps'], self.source['apps'])
        self.assertEqual(self.source, snapshot)
        self.assertEqual(catalog['news'], [])
        self.assertEqual(catalog['iconURL'], app()['iconURL'])

    def test_open_and_closed_sources_have_identical_output_format(self):
        self.config['sources'].append({'url': 'https://example.com/closed.json', 'license': 'closed-source'})
        catalog = aggregate(self.config, lambda url: {'apps': [app('dev.closed.app')]} if 'closed' in url else self.source)
        self.assertEqual(len(catalog['apps']), 2)
        self.assertNotIn('license', catalog['apps'][1])

    def test_disabled_source_not_fetched(self):
        self.config['sources'].append({'url': 'http://disabled.invalid', 'enabled': False})
        calls = []
        aggregate(self.config, lambda url: calls.append(url) or self.source)
        self.assertEqual(calls, ['https://example.com/open.json'])

    def test_duplicate_bundle_rejected(self):
        self.config['sources'].append({'url': 'https://example.com/second.json', 'license': 'closed-source'})
        with self.assertRaisesRegex(ValueError, 'Duplicate bundle'):
            aggregate(self.config, lambda url: self.source)

    def test_reject_empty_or_invalid_source(self):
        for source in ({'apps': []}, {}, [], '<html>'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                aggregate(self.config, lambda url: source)

    def test_invalid_required_metadata_and_permissions(self):
        for mutate in [lambda a: a.pop('bundleIdentifier'),
                       lambda a: a.pop('appPermissions'),
                       lambda a: a['appPermissions'].update(privacy=[]),
                       lambda a: a['appPermissions'].update(entitlements={}),
                       lambda a: a['versions'][0].update(size=True),
                       lambda a: a['versions'][0].update(date='2026-02-31'),
                       lambda a: a['versions'][0].update(downloadURL='http://example.com/app.ipa')]:
            source = {'apps': [app()]}
            mutate(source['apps'][0])
            with self.assertRaises(ValueError):
                aggregate(self.config, lambda url: source)

    def test_expected_bundle_identifiers_pinned(self):
        self.config['sources'][0]['expectedBundleIdentifiers'] = ['dev.wrong.app']
        with self.assertRaisesRegex(ValueError, 'expected list'):
            aggregate(self.config, lambda url: self.source)
        self.config['sources'][0]['expectedBundleIdentifiers'] = ['dev.example.counter']
        self.assertEqual(len(aggregate(self.config, lambda url: self.source)['apps']), 1)

    def test_https_urls_without_credentials_required(self):
        for url in ('http://example.com', 'file:///tmp/source.json', 'https://user:pass@example.com/source', 'https://example.com/#fragment'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                https_url(url, 'URL')

    def test_failed_refresh_leaves_previous_catalog_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'apps.json'
            output = root / 'altstore-source.json'
            config.write_text(json.dumps(self.config))
            output.write_text('previous catalog')
            with self.assertRaises(ValueError):
                build(config, output, lambda url: {'apps': []})
            self.assertEqual(output.read_text(), 'previous catalog')

    def test_atomic_output_is_valid_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'altstore-source.json'
            catalog = aggregate(self.config, lambda url: self.source)
            write_atomic(output, catalog)
            self.assertEqual(json.loads(output.read_text()), catalog)
            self.assertEqual(list(Path(temporary).glob('*.tmp')), [])

    def test_fetch_does_not_send_authorization(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, limit):
                return b'{"apps": []}'
        with patch('build_catalog.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = Response()
            fetch_json('https://example.com/source.json')
            request = factory.return_value.open.call_args.args[0]
            self.assertIsNone(request.get_header('Authorization'))
            self.assertEqual(request.get_header('Accept'), 'application/json')


if __name__ == '__main__':
    unittest.main()
