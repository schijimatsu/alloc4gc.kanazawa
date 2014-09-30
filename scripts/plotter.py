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
  Shape, 
)
from scripts.location import (
  GeoHash, 
  reverse_geocode, 
  geocode, 
  AllocationManager, 
  call_yahoo_api, 
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


def convert_to_kml(geohashes):
  kml = Kml()
  for geohash in geohashes:
    poly = geohash.to_polygon()
    kml.newpolygon(name=geohash.geohash, outerboundaryis=[(coord[1], coord[0]) for coord in poly.exterior.coords])
  return kml

def prepare_geohash(conn, path):
  c = conn.cursor()
  # c.execute('drop table geohashes;')
  conn.commit()
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


def get_polygon(path):
  shape = Shape(path)
  shape.load()
  return shape.union().to_shaply_object()[0]


def get_square_boundary(path):
  shape = Shape(path)
  shape.load()
  return shape.union().create_square_boundary().to_tuple()[0]


def generate_polygon_from_geohashes(conn, path):
  c = conn.cursor()

  c.execute('select * from geohashes where is_border = 1;')
  whole_poly = None
  count = 0
  polygons = []
  for row in c:
    geohash = GeoHash(geohash=row[0])
    temp = geohash.to_polygon()
    if whole_poly is None:
      whole_poly = temp
    else:
      whole_poly = whole_poly.union(temp)

  kml = Kml()
  kml.newpolygon(name="KanazawaCity", outerboundaryis=[point for point in whole_poly.exterior.coords])
  kml.save(path)

def create_allocation_table(conn):
  conn = sqlite3.connect('allocation.sqlite')
  c_allocations = conn.cursor()
  c_allocations.execute('drop table if exists chikus;')
  c_allocations.execute('''
    create table chikus (
      id integer primary key autoincrement, 
      aza varchar(32), 
      gaiku varchar(32), 
      banchi varchar(32), 
      chiku varchar(32), 
      geohash varchar(64), 
      lat real, 
      lon real, 
      address varchar(128)
    );
  ''')
  conn.commit()

def create_reverse_geocoding_table(conn):
  c_allocations = conn.cursor()
  c_allocations.execute('drop table if exists reverse_geocodings;')
  c_allocations.execute('''
    create table reverse_geocodings (
      id integer primary key autoincrement, 
      geohash varchar(32), 
      lat real, 
      lon real, 
      response text
    );
  ''')
  conn.commit()

def reverse_geocode_for_all(conn, conn_geocoding):
  c = conn.cursor()
  c.execute('select * from geohashes;')
  c_geocoding = conn_geocoding.cursor()
  for row in c:
    response_text = call_yahoo_api(row[1], row[2])
    try:
      c_geocoding.execute("insert into reverse_geocodings(geohash, lat, lon, response) values(?, ?, ?, ?);", [row[0], row[1], row[2], response_text])
      conn_geocoding.commit()
      logger.debug('lat: %0.13f, lon: %0.13f,' %(row[1], row[2]))
    except:
      logger.exception('Failed to store response. lat: %0.13f, lon: %0.13f,' %(row[1], row[2]))
    time.sleep(2)

def allocate_on_border(conn, conn_allocations):
  c = conn.cursor()
  c_allocations = conn_allocations.cursor()
  # prepare_geohash(conn, args[0])
  # generate_polygon_from_geohashes(conn, 'boundary_geohash.kml')

  c.execute('select * from geohashes where is_border = 1;')
  manager = AllocationManager(args[0])
  for row in c:
    time.sleep(1.5)
    try:
      address, allocation_data = manager.getAllocationDataByLatLon(row[1], row[2])
      # logger.debug(
      #   AllocationManager.generateList(
      #     allocation_data, 
      #     '%0.6f,%0.6f,%s,' %(
      #       row[1], 
      #       row[2], 
      #       address, 
      #     )
      #   )
      # )
      # logger.debug(allocation_data)
      items = [item.split(':') for item in AllocationManager.generateList(allocation_data)]
      for aza, gaiku, banchi, chiku in items:
        c_allocations.execute("insert into chikus(geohash, lat, lon, address, aza, gaiku, banchi, chiku) values('%s', %0.13f, %0.13f, '%s', '%s', '%s', '%s', '%s');" %(
            row[0], 
            row[1], 
            row[2], 
            address, 
            aza, 
            gaiku, 
            banchi, 
            chiku, 
          )
        )
      conn_allocations.commit()
    except:
      logger.exception('Exception occurred on mapping.')

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("-o", dest="output", help="pass the path/to/geohash.json", metavar="FILE")

  (options, args) = parser.parse_args()

  # conn_allocations = sqlite3.connect('allocation.sqlite')
  # create_allocation_table(conn_allocations)

  conn = sqlite3.connect('geohash.sqlite')
  # allocate_on_border(conn, conn_allocations)

  conn_reverse_geocoding = sqlite3.connect('reverse_geocoding.sqlite')
  create_reverse_geocoding_table(conn_reverse_geocoding)

  reverse_geocode_for_all(conn, conn_reverse_geocoding)

