"""Offline behavioral tests for photo selection and persisted updates."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import update_photos as updater


def photo(license_code='cc-by', **overrides):
    result = dict(id=123, license_code=license_code, attribution_name='作者',
                  attribution='作者 (CC BY)', medium_url='https://example.org/medium.jpg')
    result.update(overrides)
    return result


class FakeAPI:
    def __init__(self, default=None, other=None, observations=None, rank='species'):
        self.calls = []
        self.responses = [dict(results=[dict(id=42, name='Test species', rank=rank,
                                            is_active=True, default_photo=default)]),
                          dict(results=[dict(taxon_photos=[dict(taxon_id=42, photo=p)
                                                           for p in (other or [])])]),
                          dict(results=observations or [])]

    def get(self, path, **params):
        self.calls.append((path, params))
        return self.responses.pop(0)


class SelectionTests(unittest.TestCase):
    def test_default_has_priority_without_extra_requests(self):
        api = FakeAPI(default=photo(), other=[photo('cc0')])
        taxon_id, selected, reason = updater.resolve(api, 'Test species', updater.LICENSES)
        self.assertEqual((taxon_id, reason, len(api.calls)), (42, 'default', 1))
        self.assertEqual(selected['source'], 'https://www.inaturalist.org/photos/123')

    def test_restricted_default_falls_back_to_licensed_taxon_photo(self):
        api = FakeAPI(default=photo(None), other=[photo('cc-by-nd'), photo('cc-by-sa')])
        _, selected, reason = updater.resolve(api, 'Test species', updater.LICENSES)
        self.assertEqual((reason, selected['license']), ('taxon_photos', 'cc-by-sa'))

    def test_observation_photo_license_and_exact_species_are_checked(self):
        observations = [dict(taxon=dict(id=99), photos=[photo()]),
                        dict(taxon=dict(id=42), user=dict(login='observer'),
                             photos=[photo(None), photo('cc-by', medium_url=None,
                                                       url='https://example.org/square.jpeg')])]
        api = FakeAPI(observations=observations)
        _, selected, reason = updater.resolve(api, 'Test species', updater.LICENSES)
        self.assertEqual(reason, 'observation')
        self.assertEqual(selected['url'], 'https://example.org/medium.jpeg')

    def test_nc_requires_explicit_option(self):
        self.assertIsNone(updater.photo_record(photo('cc-by-nc'), updater.LICENSES))
        self.assertIsNotNone(updater.photo_record(photo('cc-by-nc'), updater.LICENSES | updater.NC_LICENSES))

    def test_missing_credit_or_insecure_url_is_rejected(self):
        for changes in [dict(attribution=''), dict(attribution_name=''),
                        dict(medium_url='http://example.org/photo.jpg')]:
            self.assertIsNone(updater.photo_record(photo(**changes), updater.LICENSES))

    def test_unverified_rank_or_name_is_rejected(self):
        for api, name in [(FakeAPI(rank='genus'), 'Test species'), (FakeAPI(), 'Other species')]:
            with self.assertRaises(ValueError):
                updater.resolve(api, name, updater.LICENSES)

    def test_no_licensed_photo_returns_readable_fallback_data(self):
        taxon_id, selected, _ = updater.resolve(FakeAPI(), 'Test species', updater.LICENSES)
        self.assertEqual(taxon_id, 42)
        self.assertIsNone(selected)

    def test_refresh_failure_preserves_saved_json_and_default_skips_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'species.json'
            original = json.dumps([dict(scientificName='Test species', taxonId=42, photo=photo())])
            path.write_text(original)
            with patch.object(updater, 'DATA', path), patch.object(updater, 'resolve') as resolve:
                with patch('sys.argv', ['update_photos.py']):
                    self.assertFalse(updater.main())
                resolve.assert_not_called()
                resolve.side_effect = URLError('offline')
                with patch('sys.argv', ['update_photos.py', '--refresh']):
                    self.assertTrue(updater.main())
                self.assertEqual(path.read_text(), original)


if __name__ == '__main__':
    unittest.main()
