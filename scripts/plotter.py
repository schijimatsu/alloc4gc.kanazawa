#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import json
import codecs
from optparse import OptionParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# sys.stdout = codecs.lookup('utf-8')[-1](sys.stdout)
# sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

'''
{
  'geohash': [
    {
      'address': <address>,
      'chiku': <chiku>,
    },
    ...
  ],
  ...
}
'''
'''
アプリケーションID：
    dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-
シークレット：
    b3b63e985a61dc575026bd5036ab24399d83a02e
'''
ADDRESS_PREFIX = '石川県金沢市'
YOLP = 'http://geo.search.olp.yahooapis.jp/OpenLocalPlatform/V1/geoCoder'
APPID = 'dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-'

def plot(input, output='geohash.json'):
  allocations = None
  with codecs.open(input, 'r', 'utf8') as f:
    allocations = json.load(f)

  boundaries = []
  for aza, gaikus in allocations.items():
    for gaiku, banchis in gaikus.items():
      for banchi, chiku in banchis.items():
        if gaiku == '':
          boundaries.append(geocode(ADDRESS_PREFIX+aza))
        elif banchi == '':
          boundaries.append(geocode(ADDRESS_PREFIX+aza+gaiku))
        else:
          boundaries.append(geocode(ADDRESS_PREFIX+aza+gaiku+'-'+banchi))

  geohashes = list_geohashes(boundaries)
  with open(output, 'w') as f:
    json.dump(geohashes, f)

def geocode(address):
  data = urlencode({
    'appid': APPID,
    'query': address,
    'ei': 'UTF-8',
    'output': 'json',
  }).encode('utf8')
  request = Request(YOLP, data=data, method='GET')
  with urlopen('%s?%s' % (request.get_full_url(), request.get_data().decode('ascii'))) as response:
    print(type(json.dumps(json.loads(response.read().decode('utf8'), encoding='utf8'))))

def list_geohashes(boundaries):
  pass

class GeoHash(object):
  BITS = [0x10, 0x08, 0x04, 0x02, 0x01]
  BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

  NEIGHBORS = {
    'right': {
      'even': "bc01fg45238967deuvhjyznpkmstqrwx", 
      'odd': "p0r21436x8zb9dcf5h7kjnmqesgutwvy", 
    },
    'left': {
      'even': "238967debc01fg45kmstqrwxuvhjyznp", 
      'odd': "14365h7k9dcfesgujnmqp0r2twvyx8zb", 
    },
    'top': {
      'even': "p0r21436x8zb9dcf5h7kjnmqesgutwvy", 
      'odd': "bc01fg45238967deuvhjyznpkmstqrwx", 
    },
    'bottom': {
      'even': "14365h7k9dcfesgujnmqp0r2twvyx8zb", 
      'odd': "238967debc01fg45kmstqrwxuvhjyznp", 
    },
  }

  BORDERS = {
    'right': {
      'even': "bcfguvyz", 
      'odd': "prxz", 
    },
    'left': {
      'even': "0145hjnp", 
      'odd': "028b", 
    },
    'top': {
      'even': "prxz", 
      'odd': "bcfguvyz", 
    },
    'bottom': {
      'even': "028b", 
      'odd': "0145hjnp", 
    },
  }

  def adjacent(self, direction):
    src_hash = self.geohash.lower()
    last_chr = src_hash[len(src_hash)-1:len(src_hash)]
    type = 'even' if src_hash.length % 2 else 'odd'
    base = src_hash[0:-1]
    if GeoHash.BORDERS[direction][type].find(last_chr) != -1:
      base = self.adjacent(base, direction)
    return base + GeoHash.BASE32[GeoHash.NEIGHBORS[direction][type].find(last_chr)]

  def encode(self, lat, lon, precision=12):
    is_even = True
    [self.lat_arr, self.lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    ch = 0
    self.geohash = ''

    while len(self.geohash) < precision:
      [val, arr] = [lon, self.lon_arr] if is_even else [lat, self.lat_arr]
      mid = (arr[0] + arr[1]) / 2
      if val > mid:
        ch |= GeoHash.BITS[bit]
        arr[0] = mid
      else:
        arr[1] = mid

      is_even = not is_even
      if bit < 4:
        bit += 1
      else:
        self.geohash += GeoHash.BASE32[ch]
        bit = 0
        ch = 0

    self.center_lat = (self.lat_arr[0] + self.lat_arr[1]) / 2
    self.center_lon = (self.lon_arr[0] + self.lon_arr[1]) / 2

    return self.geohash

  def decode(self, geohash=None):
    self.geohash = geohash or self.geohash
    [lat_arr, lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    is_even = True

    for c in geohash.split(''):
      ch = GeoHash.BASE32.find(c)
      for i in range(5):
        arr = lat_arr if is_even else lon_arr
        mid = (arr[0] + arr[1]) / 2
        if ch & GeoHash.BITS[bit]:
          arr[0] = mid
        else:
          arr[1] = mid

        is_even = not is_even

    [self.lat, self.lon] = [(lat_arr[0] + lat_arr[1]) / 2, (lon_arr[0] + lon_arr[1]) / 2]
    return [self.lat, self.lon]

if __name__ == '__main__':
  # parser = OptionParser()
  # parser.add_option("-o", dest="output", help="pass the path/to/geohash.json", metavar="FILE")

  # (options, args) = parser.parse_args()

  # if len(args) > 0:
  #   params = [args[0], options.get('output', None)]
  #   plot(*[param for param in params if param is not None])
  geocode(ADDRESS_PREFIX+'城南二丁目22-9')
  # print(urlopen('http://geo.search.olp.yahooapis.jp/OpenLocalPlatform/V1/geoCoder?appid=dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-&query=%E7%9F%B3%E5%B7%9D%E7%9C%8C%E9%87%91%E6%B2%A2%E5%B8%82%E5%9F%8E%E5%8D%97%E4%BA%8C%E4%B8%81%E7%9B%AE%EF%BC%92%EF%BC%92'))
