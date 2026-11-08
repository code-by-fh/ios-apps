import json
from pathlib import Path
import tempfile
import unittest

from register_app import register


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'apps.json'
        self.original = {'name': 'Apps', 'sources': []}
        self.path.write_text(json.dumps(self.original), encoding='utf-8')

    def test_closed_source_uses_public_distribution_repo_without_code_links(self):
        register(self.path, 'owner/private-app-releases', 'closed-source', ['dev.owner.app'])
        source = json.loads(self.path.read_text())['sources'][0]
        self.assertEqual(source['license'], 'closed-source')
        self.assertEqual(source['expectedBundleIdentifiers'], ['dev.owner.app'])
        self.assertEqual(source['url'], 'https://github.com/owner/private-app-releases/releases/latest/download/altstore-source.json')

    def test_registration_is_idempotent(self):
        register(self.path, 'owner/app', 'open-source')
        register(self.path, 'owner/app', 'open-source')
        self.assertEqual(len(json.loads(self.path.read_text())['sources']), 1)

    def test_invalid_input_preserves_registry(self):
        before = self.path.read_bytes()
        for repository, license_kind in [('https://token@github.com/owner/app', 'open-source'),
                                         ('owner/app', 'secret'), ('../app', 'closed-source')]:
            with self.assertRaises(ValueError):
                register(self.path, repository, license_kind)
            self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
