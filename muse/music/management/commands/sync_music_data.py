from datetime import datetime
import requests
import csv
from django.core.management.base import BaseCommand

URL_PREFIX = "http://localhost:3200/"
SINGER_LIST = "getSingerList?area=-100&sex=-100&index=-100&genre=-100"


class Command(BaseCommand):
    today = datetime.today().date()

    def handle(self, *args, **options):
        res = requests.get(URL_PREFIX + SINGER_LIST).json()
        res = res.get('response', {}).get('singerList', {}).get('data', {}).get('singerlist', [])
        singer_list = []
        for s in res:
            print(s)
            singer_list.append([s['singer_id'], s['singer_mid'], s['singer_name'], s['singer_pic']])

        with open('singer_list.csv', 'w') as f:
            writer = csv.writer(f, dialect='excel', delimiter=',')
            writer.writerows(singer_list)