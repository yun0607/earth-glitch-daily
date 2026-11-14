#!/usr/bin/env python3
"""Resolve licensed iNaturalist photos at maintenance time, not in the browser."""
import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parents[1] / 'data' / 'species.json'
LICENSES = {'cc0', 'cc-by', 'cc-by-sa'}
NC_LICENSES = {'cc-by-nc', 'cc-by-nc-sa'}


def https(value):
    return isinstance(value, str) and urlsplit(value).scheme == 'https' and bool(urlsplit(value).hostname)


class API:
    def __init__(self):
        self.last_request = 0

    def get(self, path, **params):
        # Sequential requests, at most one start per second, including retries.
        for attempt in range(3):
            time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            request = Request('https://api.inaturalist.org/v1/' + path + '?' + urlencode(params),
                              headers={'User-Agent': 'EarthGlitchDaily-photo-maintenance/1.0'})
            try:
                with urlopen(request, timeout=25) as response:
                    return json.load(response)
            except HTTPError as error:
                if attempt == 2 or (error.code != 429 and error.code < 500):
                    raise
                delay = error.headers.get('Retry-After', '')
                time.sleep(max(2 ** attempt, float(delay) if delay.isdigit() else 0))
            except (URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)


def photo_record(photo, licenses, author=None):
    if not isinstance(photo, dict):
        return None
    license_code = str(photo.get('license_code') or '').lower()
    url = photo.get('medium_url')
    # Observation photo responses provide only a square URL; retain its host,
    # photo ID and file extension while selecting iNaturalist's medium size.
    if not url and https(photo.get('url')):
        url = photo['url'].replace('/square.', '/medium.')
    author = photo.get('attribution_name') or author
    attribution = photo.get('attribution')
    source = photo.get('native_page_url')
    if not https(source) and type(photo.get('id')) is int:
        source = 'https://www.inaturalist.org/photos/' + str(photo['id'])
    if license_code not in licenses or not all(https(v) for v in (url, source)):
        return None
    if not isinstance(author, str) or not author.strip() or not isinstance(attribution, str) or not attribution.strip():
        return None
    return dict(url=url, author=author, attribution=attribution, license=license_code, source=source)


def resolve(api, name, licenses):
    # Common-name matches can precede the scientific name (e.g. Pipa pipa).
    results = api.get('taxa', q=name, rank='species', per_page=200).get('results', [])
    taxon = next((t for t in results if t.get('rank') == 'species'
                  and t.get('name', '').casefold() == name.casefold()
                  and t.get('is_active') is True), None)
    if not taxon:
        raise ValueError('查無精確匹配且有效的 species；保留原資料')
    taxon_id = taxon['id']
    photo = photo_record(taxon.get('default_photo'), licenses)
    if photo:
        return taxon_id, photo, 'default'
    detail = api.get(f'taxa/{taxon_id}').get('results', [])
    if detail:
        for entry in detail[0].get('taxon_photos', []):
            if entry.get('taxon_id') != taxon_id:
                continue
            photo = photo_record(entry.get('photo'), licenses)
            if photo:
                return taxon_id, photo, 'taxon_photos'
    # Bound fallback work to 90 observations; do not crawl the entire species.
    for page in range(1, 4):
        observations = api.get('observations', taxon_id=taxon_id, photos='true',
                               photo_license=','.join(sorted(licenses)),
                               per_page=30, page=page).get('results', [])
        for observation in observations:
            if observation.get('taxon', {}).get('id') != taxon_id:
                continue
            user = observation.get('user') or {}
            for candidate in observation.get('photos', []):
                photo = photo_record(candidate, licenses, user.get('name') or user.get('login'))
                if photo:
                    return taxon_id, photo, 'observation'
        if len(observations) < 30:
            break
    return taxon_id, None, 'no suitable photo'


def save(data):
    temporary = DATA.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(DATA)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='重新檢查已存照片；查詢失敗時保留原資料')
    parser.add_argument('--allow-nc', action='store_true', help='僅在已確認非商業用途符合條款時使用')
    parser.add_argument('--name', help='僅處理此精確學名')
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding='utf-8'))
    if args.name and not any(item['scientificName'] == args.name for item in data):
        parser.error('指定學名不在發布清單內')
    licenses = LICENSES | (NC_LICENSES if args.allow_nc else set())
    api, failures = API(), 0
    for item in data:
        if args.name and item['scientificName'] != args.name:
            continue
        if item.get('photo') and not args.refresh:
            print(f"SKIP {item['scientificName']}: 已有照片", flush=True)
            continue
        try:
            taxon_id, photo, reason = resolve(api, item['scientificName'], licenses)
        except (URLError, TimeoutError, ValueError, KeyError) as error:
            failures += 1
            print(f"ERROR {item['scientificName']}: {error}", flush=True)
            continue
        item.update(taxonId=taxon_id, photo=photo)
        save(data)
        print(f"OK {item['scientificName']}: {reason}", flush=True)
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
