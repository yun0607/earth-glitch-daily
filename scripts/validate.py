#!/usr/bin/env python3
"""Validate scheduled daily species; standard library only."""
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit

P = Path(__file__).resolve().parents[1] / 'data' / 'species.json'
allowed = {'海洋','昆蟲','植物','真菌','哺乳','鳥類','爬蟲','兩棲','其他'}
fields = {'date','scientificName','title','category','teaser','feature','bugRating','taxonId','photo'}
photo_fields = {'url','author','attribution','license','source'}
licenses = {'cc0','cc-by','cc-by-sa','cc-by-nc','cc-by-nc-sa'}

def https_url(value):
    return isinstance(value, str) and urlsplit(value).scheme == 'https' and bool(urlsplit(value).hostname)
data = json.loads(P.read_text(encoding='utf-8'))
assert isinstance(data, list) and data, 'Species data must be a nonempty list'
dates, names = [], []
for i,item in enumerate(data,1):
    assert isinstance(item,dict) and set(item)==fields, f'Entry {i}: wrong fields'
    assert all(isinstance(item[k],str) and item[k].strip() for k in fields-{'bugRating','taxonId','photo'}), f'Entry {i}: missing text'
    assert item['taxonId'] is None or (type(item['taxonId']) is int and item['taxonId'] > 0), f'Entry {i}: invalid taxonId'
    photo = item['photo']
    if photo is not None:
        assert item['taxonId'] is not None, f'Entry {i}: photo requires verified taxonId'
        assert isinstance(photo,dict) and set(photo)==photo_fields, f'Entry {i}: wrong photo fields'
        assert all(isinstance(photo[k],str) and photo[k].strip() for k in photo_fields), f'Entry {i}: missing photo metadata'
        assert photo['license'] in licenses, f'Entry {i}: unsupported photo license'
        assert https_url(photo['url']) and https_url(photo['source']), f'Entry {i}: photo URLs must use HTTPS'
    day=dt.date.fromisoformat(item['date'])
    assert day.isoformat()==item['date'], f'Entry {i}: invalid ISO date'
    assert item['category'] in allowed, f'Entry {i}: invalid category'
    assert type(item['bugRating']) is int and 1 <= item['bugRating'] <= 5, f'Entry {i}: invalid rating'
    assert len(item['scientificName'].split())>=2, f'Entry {i}: scientificName requires binomial'
    dates.append(day);names.append(item['scientificName'].lower().strip())
assert dates==sorted(dates), 'Dates must be sorted'
assert len(set(dates))==len(dates), 'Duplicate release dates'
assert len(set(names))==len(names), 'Duplicate scientific names'
assert all((b-a).days==1 for a,b in zip(dates,dates[1:])), 'Schedule has gaps'
print(f'PASS: {len(data)} species, {dates[0]} through {dates[-1]}, unique dates and names')
