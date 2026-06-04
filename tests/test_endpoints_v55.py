"""v5.5.0+ P8-C: 4 新端点单测 (image_manifest / archives x2 / endings)"""
import sys
import os
import unittest
import json


class TestImageManifest(unittest.TestCase):
    """v5.5.0+ P8-C1: /api/image_manifest"""

    def test_manifest_no_filter(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/image_manifest')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertIn('manifest', data)
        self.assertIn('total', data)
        self.assertIn('categories', data)
        self.assertGreater(data['total'], 0)
        self.assertIsInstance(data['manifest'], dict)

    def test_manifest_filter_category(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/image_manifest?category=btn')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['filter'], 'btn')
        for cat in data['categories']:
            self.assertEqual(cat, 'btn')

    def test_manifest_filter_unknown_category(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/image_manifest?category=__nonexistent__')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['total'], 0)


class TestArchivesList(unittest.TestCase):
    """v5.5.0+ P8-C2: /api/archives"""

    def test_archives_list_empty(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/archives')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('archives', data)
        self.assertIn('total', data)
        self.assertIn('user_data_dir', data)
        self.assertIsInstance(data['archives'], list)
        self.assertGreaterEqual(data['total'], 0)


class TestArchivesGet(unittest.TestCase):
    """v5.5.0+ P8-C3: /api/archives/<campaign_id>"""

    def test_archives_get_nonexistent(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/archives/__nonexistent_xyz__')
        self.assertEqual(r.status_code, 404)
        data = r.get_json()
        self.assertIn('error', data)

    def test_archives_get_default(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/archives/default')
        if r.status_code == 404:
            return
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn('campaign_id', data)
        self.assertIn('db_size_kb', data)
        self.assertIn('saves', data)
        self.assertIn('total_saves', data)
        self.assertIn('auto_saves', data)
        self.assertIn('manual_saves', data)


class TestEndings(unittest.TestCase):
    """v5.5.0+ P8-C4: /api/endings"""

    def test_endings_full(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/endings')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('endings', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 12)
        self.assertEqual(len(data['endings']), 12)

    def test_endings_keys_unique(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/endings')
        data = r.get_json()
        keys = [e['key'] for e in data['endings']]
        self.assertEqual(len(keys), len(set(keys)))

    def test_endings_required_fields(self):
        from server import app
        client = app.test_client()
        r = client.get('/api/endings')
        data = r.get_json()
        for e in data['endings']:
            self.assertIn('key', e)
            self.assertIn('name', e)
            self.assertIn('desc', e)


if __name__ == '__main__':
    unittest.main(verbosity=2)
