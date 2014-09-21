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
from simplekml import Kml

'''
アプリケーションID：
    dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-
シークレット：
    b3b63e985a61dc575026bd5036ab24399d83a02e
'''
NORMALIZE_FLAGS = 'NFKC'
GEOCODER = 'http://geo.search.olp.yahooapis.jp/OpenLocalPlatform/V1/geoCoder'
REVERSE_GEOCODER = 'http://reverse.search.olp.yahooapis.jp/OpenLocalPlatform/V1/reverseGeoCoder'
APPID = 'dj0zaiZpPUJhRjVhaE1hQW5KbCZzPWNvbnN1bWVyc2VjcmV0Jng9YjY-'


def toOneByteAlphaNumeric(s):
  t = dict((0xff00 + ch, 0x0020 + ch) for ch in range(0x5f))
  t[0x3000] = 0x0020
  return s.translate(t)


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
  address = None
  with urlopen('%s?%s' % (request.get_full_url(), request.get_data().decode('ascii'))) as response:
    response_text = response.read()
    response_obj = json.loads(response_text.decode('utf8'), encoding='utf8')
    # logger.debug(json.dumps(response_obj, ensure_ascii=True))
    result_info = response_obj['ResultInfo']
    result_status = result_info['Status']
    result_count = result_info['Count']
    result_feature = None
    if result_status == 200 and result_count > 0:
      if result_count == 1:
        result_feature = response_obj['Feature'][0]
      else:
        result_feature = response_obj['Feature'][0]
        logger.warn('Feature of result are there more than 1.')
        for i, feature in enumerate(response_obj['Feature']):
          logger.warn('Feature[%d]: %s,' %(i, feature['Property']['Address']))
    else:
      logger.warn('Failed to reverse geocode. (%0.13f, %0.13f)' %(lat, lon))

    address = result_feature['Property']['Address']

  return address


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


class AllocationManager(object):
  def __init__(self, path):
    self.path = path
    self.aza = None
    with codecs.open(self.path, 'r', 'utf8') as f:
      self.allocation = json.load(f, encoding='utf8')

  def getAllocationDataByLatLon(self, lat, lon):
    address = reverse_geocode(lat, lon)
    return (address, self.getAllocationData(address))

  def getAllocationData(self, address):
    if self.aza is None:
      self.aza = Aza(self.allocation)
    logger.debug(address)
    return self.aza.generateChikuList(address)

  @staticmethod
  def generateList(struct, text=''):
    l = []
    for k, v in struct.items():
      if isinstance(v, dict):
        l += AllocationManager.generateList(v, '%s%s:' %(text, k))
      else:
        l.append('%s%s:%s' %(text, k, v))

    return l

class Node(object):

  def __init__(self, allocation):
    self.allocation = allocation
    self.nodes = dict()
    self.key = None


class SubNode(Node):

  def __init__(self, parentNode, allocation, address):
    super(SubNode, self).__init__(allocation)
    self.parentNode = parentNode
    self.address = address


class Aza(Node):

  def generateChikuList(self, address):
    self.address = address
    struct = {}
    aza_under = None
    m = re.match(r'^石川県金沢市(.*)$', self.address)
    if m:
      aza_under = m.groups()[0]
      m = re.match('^(%s)(.*)$' % '|'.join([name for name, _ in self.allocation.items()]), aza_under)
      if m:
        self.key = m.groups()[0]
        self.nodes[self.key] = Gaiku(self, self.allocation[self.key], m.groups()[1]).narrow()
      else:
        raise Exception('The Aza that corresponds to the allocation-data could not be found. aza: %s,' % aza_under)
    else:
      raise Exception('Not in Kanazawa. address: %s' % self.address)

    return self.nodes


class Gaiku(SubNode):

  def narrow(self):
    if self.address == '' and not '' in self.allocation:
      for k, v in self.allocation.items():
        self.nodes[k] = Banchi(self, v, self.address).narrow()
    else:
      r = re.compile('^(-|－)*(%s)(.*)$' % '|'.join(sorted([number for number, _ in self.allocation.items() if number != ''], reverse=True)))
      m = r.match(toOneByteAlphaNumeric(self.address))
      if m:
        self.key = m.groups()[1]
        banchi_under = m.groups()[2]
      elif '' in self.allocation:
        self.key = ''
        banchi_under = self.address
      elif 'others' in self.allocation:
        self.key = 'others'
        banchi_under = None
        self.nodes[''] = Banchi(self, self.allocation[self.key], self.address).narrow()
      else:
        raise Exception('The Gaiku that corresponds to the allocation-data could not be found.\naddress: %s, gaiku: %s,' %(
          self.parentNode.address, 
          self.address, 
          )
        )
        banchi_under = None

      if banchi_under is not None:
        self.nodes[self.key] = Banchi(self, self.allocation[self.key], banchi_under).narrow()

      return self.nodes


class Banchi(SubNode):

  def bottomUp(self):
    bu = {}
    for banchi in [toOneByteAlphaNumeric(banchi) for banchi, chiku in self.allocation.items()]:
      if not self.allocation[banchi] in bu:
        bu[self.allocation[banchi]] = [banchi]
      else:
        bu[self.allocation[banchi]].append(banchi)

    return bu

  def integrateBanchis(self, _banchis=None):
    banchis = _banchis or []
    temp, ret = [[]]*2
    numbers = [int(banchi) for banchi in banchis if not (banchi == '' or not isdigit(banchi))]
    texts = [banchi for banchi in banchis if banchi == '' or not isdigit(banchi)]
    for number in sorted(numbers, reverse=True):
      if len(temp) == 0 or temp[:-1][0]+1 == number:
        temp.append(number)
      else:
        ret.append(self.broadOrSingle(temp))
        temp = [number]

    ret.append(self.broadOrSingle(temp))
    ret += texts

    return ret

  def broadOrSingle(self, l):
    if len(l) > 1:
      return '%s〜%s' %(l[0], l[:-1][0])
    else:
      return l[0]

  def checkMoreThan(self, banchi_under, narrowed_allocation):
    r = re.compile(r'^([^0-9]*?)([0-9]+?)〜$')
    prefix, value = [None]*2
    for k, v in narrowed_allocation.items():
      m = r.match(k)
      if m:
        prefix = m.groups()[0]
        value = m.groups()[1]
        break

    if value is not None and banchi_under != '':
      r = re.compile(r'^(-|－)?([^0-9]*?)([0-9]+)$')
      m = r.match(banchi_under)
      if m and int(m.groups()[2]) >= int(toOneByteAlphaNumeric(value)):
        if prefix is not None and prefix == m.groups()[1]:
          return [m.groups()[2], prefix+value+'〜']
        else:
          return [m.groups()[2], value+'〜']
      else:
        return None
    else:
      return None

  def narrow(self):
    if self.address == '' and not self.allocation['']:
      if self.parentNode.parentNode.allocation['others']:
        self.nodes['others'] = self.parentNode.parentNode.allocation['others']

      bu = self.bottomUp()
      for chiku, banchis in bu.items():
        for key in self.integrateBanchis(banchis):
          self.nodes[key] = chiku

    else:
      r = re.compile(r'^(-|－)*(%s)$' % '|'.join(sorted([number for number, _ in self.allocation.items() if number != ''], reverse=True)))
      m = r.match(self.address)
      if m:
        self.key = m.groups()[1]
        self.nodes[self.key] = self.allocation[self.key]
      else:
        moreThan = self.checkMoreThan(self.address, self.allocation)
        if moreThan is not None:
          self.key = moreThan[0]
          self.nodes[self.key] = self.allocation[moreThan[1]]
        elif '' in self.allocation:
          self.key = ''
          self.nodes[self.key] = self.allocation['']
        elif 'others' in self.parentNode.allocation:
          self.nodes = self.parentNode.allocation['others']
        else:
          raise Exception('The Banchi that corresponds to the allocation-data could not be found.\naddress: %s, banchi: %s,' %(
            self.parentNode.parentNode.address, 
            self.address, 
            )
          )

    return self.nodes

