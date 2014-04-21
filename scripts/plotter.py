#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import json
from optparse import OptionParser

def plot(input, output='geohash.json'):
  pass

class GeoHash
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
    src_hash = geohash.lower()
    last_chr = src_hash[len(src_hash)-1:len(src_hash)]
    type = 'even' if src_hash.length % 2 else 'odd'
    base = src_hash[0:-1]
    if BORDERS[direction][type].find(last_chr) != -1:
      base = adjacent(base, direction)
    return base + BASE32[NEIGHBORS[direction][type].find(last_chr)]

  def encode(self, lat, lon, precision=12):
    is_even = true
    [self.lat_arr, self.lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    ch = 0
    self.geohash = ''

    while len(geohash) < precision:
      [val, arr] = [lon, self.lon_arr] if is_even else [lat, self.lat_arr]
      mid = (arr[0] + arr[1]) / 2
      if val > mid:
        ch |= BITS[bit]
        arr[0] = mid
      else:
        arr[1] = mid

      is_even = not is_even
      if bit < 4:
        bit++
      else:
        geohash += BASE32[ch]
        bit = 0
        ch = 0

    self.center_lat = (self.lat_arr[0] + self.lat_arr[1]) / 2
    self.center_lon = (self.lon_arr[0] + self.lon_arr[1]) / 2

    return self.geohash

  def decode(geohash=null):
    self.geohash = geohash || self.geohash
    [lat_arr, lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    is_even = true

    for c in geohash.split('')
      ch = BASE32.find(c)
      for i in range(5):
        arr = lat_arr if is_even else lon_arr
        mid = (arr[0] + arr[1]) / 2
        if ch & BITS[bit]:
          arr[0] = mid
        else:
          arr[1] = mid

        is_even = not is_even

    [self.lat, self.lon] = [(lat_arr[0] + lat_arr[1]) / 2, (lon_arr[0] + lon_arr[1]) / 2]
    return [self.lat, self.lon]

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("-o", dest="output", help="pass the path/to/geohash.json", metavar="FILE")

  (options, args) = parser.parse_args()

  if len(args) > 0:
    params = [args[0], options.get('output', None)]
    plot(*[param for param in params if param is not None])
