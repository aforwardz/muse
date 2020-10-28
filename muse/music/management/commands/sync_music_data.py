from datetime import datetime
import os
import requests
import pandas as pd
import time
import csv
from django.core.management.base import BaseCommand

URL_PREFIX = "http://localhost:3200/"
SINGER_LIST = "getSingerList?area=-100&sex=-100&index=-100&genre=-100&page={}"
ALBUM_LIST = "getSingerAlbum?singermid={}&page={}"
ALBUM_SONGS = "getAlbumInfo?albummid={}"


class Command(BaseCommand):
    today = datetime.today().date()

    def add_arguments(self, parser):
        parser.add_argument('--all', type=bool)
        parser.add_argument('--singer', type=bool)
        parser.add_argument('--album', type=bool)
        parser.add_argument('--song', type=bool)

    def sync_singers(self):
        page, limit, singer_list = 1, 80, []
        res = requests.get(URL_PREFIX + SINGER_LIST.format(page)).json()
        res = res.get('response', {}).get('singerList', {}).get('data', {})
        total = res.get('total')
        while total and page <= total // limit + 1:
            res = res.get('singerlist', [])
            for s in res:
                print(s)
                singer_list.append(dict((k, s.get(k)) for k in
                                        ('singer_id', 'singer_mid', 'singer_name', 'singer_pic')))
            page += 1
            time.sleep(0.1)

            res = requests.get(URL_PREFIX + SINGER_LIST.format(page)).json()
            res = res.get('response', {}).get('singerList', {}).get('data', {})

        df = pd.DataFrame.from_records(singer_list, index='singer_id')
        df = df[~df.index.duplicated(keep='first')]
        df.to_csv('material/singer_list.csv', header=False)

    def sync_albums(self, smid):
        page, limit, album_list = 1, 5, []
        res = requests.get(URL_PREFIX + ALBUM_LIST.format(smid, page)).json()
        res = res.get('response', {}).get('singer', {}).get('data', {})
        total = res.get('total')
        while total and page <= total // limit + 1:
            res = res.get('albumList', [])
            album_list.extend(res)
            page += 1
            time.sleep(0.1)

            res = requests.get(URL_PREFIX + ALBUM_LIST.format(smid, page)).json()
            res = res.get('response', {}).get('singer', {}).get('data', {})

        if album_list:
            df = pd.DataFrame.from_records(album_list, index='albumID')
            df = df[~df.index.duplicated(keep='first')]
            if not os.path.isdir('material/%s' % smid):
                os.mkdir('material/%s' % smid)
            df.to_csv('material/%s/albums.csv' % smid, header=False)

    def sync_album_songs(self, smid):
        song_list = []
        with open('material/%s/albums.csv' % smid, 'r') as f:
            reader = csv.reader(f, dialect='excel', delimiter=',')
            for i, line in enumerate(reader):
                if i:
                    try:
                        res = requests.get(URL_PREFIX + ALBUM_SONGS.format(line[1])).json()
                        res = res.get('response', {}).get('data', {}).get('list', [])
                    except Exception as e:
                        continue
                    print(smid, res)
                    for s in res:
                        song_list.append(dict((k, s.get(k)) for k in
                                              ('songid', 'songmid', 'songname', 'albumid', 'albummid', 'albumname')))

        if song_list:
            df = pd.DataFrame.from_records(song_list, index='songid')
            df = df[~df.index.duplicated(keep='first')]
            if not os.path.isdir('material/%s' % smid):
                os.mkdir('material/%s' % smid)
            df.to_csv('material/%s/songs.csv' % smid, header=False)

    def handle(self, *args, **options):
        total = True if options.get('all') else False
        singer = True if options.get('singer') else False
        album = True if options.get('album') else False
        song = True if options.get('song') else False

        if total or singer:
            self.sync_singers()

        if total or album:
            with open('material/singer_list.csv', 'r') as f:
                reader = csv.reader(f, dialect='excel', delimiter=',')
                for line in reader:
                    self.sync_albums(line[1])

        if total or song:
            for r, d, _ in os.walk('material'):
                if not d:
                    smid = r.split('/')[-1]
                    self.sync_album_songs(smid)



