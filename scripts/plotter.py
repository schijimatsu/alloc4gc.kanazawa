#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import codecs
import re
from optparse import OptionParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from unicodedata import normalize
import sqlite3
import time
import logging
from logging.config import dictConfig
dictConfig({
  'version': 1,              
  'disable_existing_loggers': False,
  'formatters': {
    'standard': {
      'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    },
  },
  'handlers': {
    'default': {
      'level':'DEBUG',
      'class':'logging.StreamHandler',
    },
  },
  'loggers': {
    '': {
      'handlers': ['default'],
      'level': 'DEBUG',
      'propagate': False
    },
  }
})
logger = logging.getLogger(__package__)
from geohash import (
  encode as encode_to_geohash, 
  decode as decode_from_geohash, 
  neighbors, 
)
from simplekml import Kml
# sys.stdout = codecs.lookup('utf-8')[-1](sys.stdout)
# sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

from shapely.geometry import (
 Point, 
)
from shapely.geometry.polygon import (
  LinearRing, 
  Polygon, 
)
from shapely.ops import cascaded_union
from scripts.polygon import (
  get_square_boundary, 
  get_polygon, 
)
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
GEOCODER = 'http://geo.search.olp.yahooapis.jp/OpenLocalPlatform/V1/geoCoder'
REVERSE_GEOCODER = 'http://reverse.search.olp.yahooapis.jp/OpenLocalPlatform/V1/reverseGeoCoder'
APPID = 'dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-'
NORMALIZE_FLAGS = 'NFKC'

conn = None

def insert(chiku, boundary):
  c = conn.cursor()
  geohashes = list_geohashes(boundary)
  sql = 'insert into chikus(chiku, geohash) values(\'%s\', \'%s\')'
  for geohash in geohashes:
    c.execute(sql % (chiku, geohash))

  conn.commit()
  c.close()

def insert_aza(chiku, aza):
  geocoded = geocode(ADDRESS_PREFIX + aza)
  insert(chiku, geocoded)

def insert_gaiku(chiku, aza, gaiku):
  geocoded = geocode(ADDRESS_PREFIX + aza + gaiku)
  if geocoded is None:
    geocoded = geocode(ADDRESS_PREFIX + aza)
  insert(chiku, geocoded)

def insert_banchi(chiku, aza, gaiku, banchi):
  geocoded = geocode(ADDRESS_PREFIX + aza + gaiku + '-' + banchi)
  if geocoded is None:
    geocoded = geocode(ADDRESS_PREFIX + aza + gaiku)
  if geocoded is None:
    geocoded = geocode(ADDRESS_PREFIX + aza)
  insert(chiku, geocoded)

def plot(input, output='geohash.json'):
  allocations = None
  with codecs.open(input, 'r', 'utf8') as f:
    allocations = json.load(f)

  boundaries = []
  counter = 0
  for aza, gaikus in allocations.items():
    for gaiku, banchis in gaikus.items():
      # time.sleep(1)
      logger.debug('gaiku: %s, banchis: %s' %(gaiku, banchis))
      if isinstance(banchis, dict):
        for banchi, chiku in banchis.items():
          counter += 1
        #   time.sleep(1)
        #   if gaiku == '':
        #     insert_aza(chiku, aza)
        #   elif banchi == '':
        #     insert_gaiku(chiku, aza, gaiku)
        #   else:
        #     insert_banchi(chiku, aza, gaiku, banchi)
      else:
        counter += 1
        # if gaiku == '':
        #   insert_aza(banchis, aza)
        # elif gaiku != 'others':
        #   insert_gaiku(banchis, aza, gaiku)
        # else:
        #   logger.debug('No address. %s%s%s' %(aza, gaiku, banchis))
        #   pass

  logger.debug('counter: %d' % counter)
  # geohashes = list_geohashes(boundaries)
  # with open(output, 'w') as f:
  #   json.dump(geohashes, f)

def list_geohashes(boundary, precision=8):
  geohashes = []
  if boundary is not None:
    west, south, east, north = boundary
    north_west = GeoHash().encode(north, west, precision=precision)
    north_east = GeoHash().encode(north, east, precision=precision)
    south_east = GeoHash().encode(south, east, precision=precision)

    temp = north_west
    count = 0
    while True:
      # if count >= 500000: geohashes.append(temp)
      geohashes.append(temp)
      if temp == south_east:
        break
      elif temp == north_east:
        north_west = north_west.adjacent('bottom')
        north_east = north_east.adjacent('bottom')
        temp = north_west
      else:
        temp = temp.adjacent('right')
      # count += 1
      # if count >= 500010:
      #   break

  return geohashes

def reverse_geocode(lat, lon):
  data = urlencode(
    dict(
      appid=APPID,
      lat=lat, 
      lon=lon, 
      output='json',
    )
  ).encode('utf8')
  request = Request(REVERSE_GEOCODER, data=data, method='GET')
  with urlopen('%s?%s' % (request.get_full_url(), request.get_data().decode('ascii'))) as response:
    response_text = response.read()


def geocode(address):
  normal_address = normalize(NORMALIZE_FLAGS, address)
  logger.debug(normal_address)
  data = urlencode({
    'appid': APPID,
    'query': normal_address,
    'ei': 'UTF-8',
    'output': 'json',
  }).encode('utf8')
  request = Request(GEOCODER, data=data, method='GET')
  with urlopen('%s?%s' % (request.get_full_url(), request.get_data().decode('ascii'))) as response:
    response_text = response.read().decode('utf8')
    response_obj = json.loads(response_text, encoding='utf8')
    try:
      result_info = response_obj['ResultInfo']
      result_status = result_info['Status']
      result_count = result_info['Count']
      result_feature = None
      if result_status == 200 and result_count > 0:
        if result_count == 1:
          result_feature = response_obj['Feature'][0]
        else:
          result_feature = response_obj['Feature'][0]

        result_property = result_feature['Property']
        result_geometry = result_feature['Geometry']
        result_address = normalize(NORMALIZE_FLAGS, result_property['Address'])
        return [float(point.strip()) for point in re.split(r',| ', result_geometry['BoundingBox'])]
      else:
        print('Failed to get bounding box for %s, %s' %(address, response_obj))
        return None
    except:
      logger.debug(response_text)
      logger.exception('Error.')
      sys.exit(1)

class GeoHash(object):
  def __init__(self, geohash=None):
    if geohash is not None:
      self.geohash = geohash

  def __repr__(self):
    return self.geohash

  def __eq__(self, other):
    # logger.debug('%s == %s: %s' %(other.geohash, self.geohash, self.geohash == other.geohash))
    return self.geohash == other.geohash

  def adjacent(self, direction):
    adjacents = neighbors(self.geohash)
    ret = GeoHash()
    if direction == 'top':
      ret.geohash = adjacents[3]
    elif direction == 'left':
      ret.geohash = adjacents[0]
    elif direction == 'right':
      ret.geohash = adjacents[1]
    elif direction == 'bottom':
      ret.geohash = adjacents[2]
    else:
      ret.geohash = None

    return ret

  def encode(self, lat, lon, precision=8):
    self.precision = precision
    self.geohash = encode_to_geohash(lat, lon, precision=precision)
    return self

  def decode(self, delta=False):
    self.point = decode_from_geohash(self.geohash, delta)
    self.precision = len(self.geohash)
    self.delta = delta
    return self.point

  def get_boundary(self):
    point = self.decode(delta=True)
    return (point[1] - point[3], point[0] - point[2], point[1] + point[3], point[0] + point[2])

  def to_polygon(self):
    geohash_boundary = self.get_boundary()
    coordinates = []
    for i in range(len(geohash_boundary)):
      lat, lon = None, None
      if len(geohash_boundary)-1 <= i:
        lat = geohash_boundary[i]
        lon = geohash_boundary[0]
      elif i % 2 == 0:
        lat = geohash_boundary[i+1]
        lon = geohash_boundary[i]
      elif i % 2 == 1:
        lat = geohash_boundary[i]
        lon = geohash_boundary[i+1]
      coordinates.append((lon, lat))
    poly = Polygon(coordinates)
    return poly

def convert_to_kml(geohashes):
  kml = Kml()
  for geohash in geohashes:
    poly = geohash.to_polygon()
    kml.newpolygon(name=geohash.geohash, outerboundaryis=[(coord[1], coord[0]) for coord in poly.exterior.coords])
  return kml

def prepare_geohash(conn, path):
  c = conn.cursor()
  # c.execute('drop table chikus;')
  # c.execute('drop table geohashes;')
  conn.commit()
  # c.execute('create table chikus (chiku varchar(64), geohash varchar(64));')
  c.execute('create table geohashes (geohash varchar(16), lat real, lon real, delta integer, is_border int);')
  conn.commit()
  c.close()

  try:
    boundary = get_square_boundary(path)
    geohashes = list_geohashes(boundary, precision=8)
    boundary_ring = get_polygon(path)
    # convert_to_kml(geohashes).save('geohash.kml')
    c = conn.cursor()
    for geohash in geohashes:
      geohash_ring = geohash.to_polygon()
      if boundary_ring.intersects(geohash_ring):
        c.execute("insert into geohashes values('%s', %0.13f, %0.13f, %d, %d);" %(
            geohash.geohash, 
            geohash.point[0], 
            geohash.point[1], 
            geohash.delta, 
            1 if not boundary_ring.contains(geohash_ring) else 0, 
          )
        )
        conn.commit()
    c.close()
  except:
    logger.exception()

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("-o", dest="output", help="pass the path/to/geohash.json", metavar="FILE")

  (options, args) = parser.parse_args()

  conn = sqlite3.connect('geohash.sqlite')
  # prepare_geohash(conn, args[0])
  # c = conn.cursor()

  # c.execute('select * from geohashes where is_border = 1;')
  # whole_poly = None
  # count = 0
  # polygons = []
  # for row in c:
  #   geohash = GeoHash(geohash=row[0])
  #   temp = geohash.to_polygon()
  #   if whole_poly is None:
  #     whole_poly = temp
  #   else:
  #     whole_poly = whole_poly.union(temp)

  # kml = Kml()
  # kml.newpolygon(name="KanazawaCity", outerboundaryis=[point for point in whole_poly.exterior.coords])
  # kml.save('boundary_geohash.kml')
