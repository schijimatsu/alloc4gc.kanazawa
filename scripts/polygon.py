#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import codecs
import re
from xml.etree import ElementTree as ET
from optparse import OptionParser
# from urllib.parse import urlencode
# from urllib.request import Request, urlopen
# from unicodedata import normalize
import sqlite3
import time
from datetime import datetime
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

from osgeo import ogr
from osgeo import osr
from osgeo.ogr import (
  Feature, 
  FeatureDefn, 
  Layer, 
  Geometry, 
)
from shapely import (
  geometry, 
  wkt, 
)

class Shape(object):
  def __init__(self, path=None):
    self.path = path

  def load(self):
    self.shapefile = ogr.Open(self.path)
    self.layer = self.shapefile.GetLayer(0)

  @staticmethod
  def new_shape(path=None):
    _path = path or '../data/gen/%s' % datetime.now().strftime('%Y%m%d%H%M%S%f')
    if os.path.exists(_path):
      os.makedirs(_path)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(_path)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    layer = data_source.CreateLayer("_",   srs, ogr.wkbPolygon)

    field_ken_name = ogr.FieldDefn("KEN_NAME", ogr.OFTString)
    field_ken_name.SetWidth(100)
    layer.CreateField(field_ken_name)
    field_ken_name = ogr.FieldDefn("CSS_NAME", ogr.OFTString)
    field_ken_name.SetWidth(100)
    layer.CreateField(field_ken_name)
    field_gst_name = ogr.FieldDefn("GST_NAME", ogr.OFTString)
    field_gst_name.SetWidth(100)
    layer.CreateField(field_gst_name)
    field_gst_name = ogr.FieldDefn("KIHON1", ogr.OFTString)
    field_gst_name.SetWidth(100)
    layer.CreateField(field_gst_name)
    field_gst_name = ogr.FieldDefn("KIHON2", ogr.OFTString)
    field_gst_name.SetWidth(100)
    layer.CreateField(field_gst_name)
    field_gst_name = ogr.FieldDefn("MOJI", ogr.OFTString)
    field_gst_name.SetWidth(100)
    layer.CreateField(field_gst_name)
    field_gst_name = ogr.FieldDefn("KCODE1", ogr.OFTString)
    field_gst_name.SetWidth(100)
    layer.CreateField(field_gst_name)
    shape = Shape(_path)
    shape.shapefile = data_source
    shape.layer = layer

    return shape

  def add_polygon(self, 
    geometry, 
    ken_name=None, 
    css_name=None,
    gst_name=None,
    kihon1=None,
    kihon2=None,
    moji=None,
    kcode1=None,
  ):
    feature = Feature(self.layer.GetLayerDefn())
    if ken_name is not None: feature.SetField('KEN_NAME', ken_name)
    if css_name is not None: feature.SetField('CSS_NAME', css_name)
    if gst_name is not None: feature.SetField('GST_NAME', gst_name)
    if kihon1 is not None: feature.SetField('KIHON1', gst_name)
    if kihon2 is not None: feature.SetField('KIHON2', gst_name)
    if moji is not None: feature.SetField('MOJI', gst_name)
    if kcode1 is not None: feature.SetField('KCODE1', gst_name)
    feature.SetGeometry(geometry)
    self.layer.CreateFeature(feature)

  def create_square_boundary(self):
    shape = Shape.new_shape()
    for i in range(self.layer.GetFeatureCount()):
      feature = self.layer.GetFeature(i)
      geometry_ref = feature.GetGeometryRef()
      boundary = geometry_ref.GetBoundary()
      (north, south, east, west) = [0.0]*4
      for point in boundary.GetPoints():
        if north == 0.0 or north < point[1]: north = point[1]
        if south == 0.0 or south > point[1]: south = point[1]
        if east == 0.0 or east < point[0]: east = point[0]
        if west == 0.0 or west > point[0]: west = point[0]
      ring = Geometry(ogr.wkbLinearRing)
      ring.AddPoint(east, north)
      ring.AddPoint(east, south)
      ring.AddPoint(west, south)
      ring.AddPoint(west, north)
      ring.AddPoint(east, north)
      poly = Geometry(ogr.wkbPolygon)
      poly.AddGeometry(ring)
      shape.add_polygon(poly)

    return shape

  def create_buffer(self, distance):
    shape = Shape.new_shape()
    for i in range(self.layer.GetFeatureCount()):
      feature = self.layer.GetFeature(i)
      geometry_ref = feature.GetGeometryRef()
      geometry_buffer = geometry_ref.Buffer(distance)
      shape.add_polygon(geometry_buffer)

    return shape

  def union(self):
    whole_geometry = None
    # KEN_NAME, GST_NAME = None, None
    for i in range(self.layer.GetFeatureCount()):
      feature = self.layer.GetFeature(i)
      geometry_ref = feature.GetGeometryRef()
      # ken_name = feature.GetField('KEN_NAME')
      # gst_name = feature.GetField('GST_NAME')
      # if KEN_NAME is None: KEN_NAME = ken_name
      # if GST_NAME is None: GST_NAME = gst_name
      if whole_geometry is None:
        whole_geometry = geometry_ref.Clone()
      else:
        whole_geometry = whole_geometry.Union(geometry_ref)

    shape = Shape.new_shape()
    shape.add_polygon(whole_geometry)

    return shape

  def tokml(self):
    kml = Kml()
    for i in range(self.layer.GetFeatureCount()):
      feature = self.layer.GetFeature(i)
      if feature.IsFieldSet('KEN_NAME'):
        ken_name = feature.GetField('KEN_NAME')
        css_name = feature.GetField('CSS_NAME')
        gst_name = feature.GetField('GST_NAME')
        kihon1 = feature.GetField('KIHON1')
        kihon2 = feature.GetField('KIHON2')
        moji = feature.GetField('MOJI')
        kcode1 = feature.GetField('KCODE1')
        key = '%s%s%s' %(
          ken_name, 
          gst_name, 
          moji, 
        )
      else:
        key = '石川県金沢市'
      geometry_ref = feature.GetGeometryRef()
      boundary = geometry_ref.GetBoundary()
      kml.newpolygon(name=key, outerboundaryis=[boundary.GetPoint(i) for i in range(boundary.GetPointCount())])

    return kml

  def to_tuple(self):
    tuples = []
    for i in range(self.layer.GetFeatureCount()):
      (north, east, west, south) = [0.0]*4
      feature = self.layer.GetFeature(i)
      geometry_ref = feature.GetGeometryRef()
      boundary = geometry_ref.GetBoundary()
      for point in boundary.GetPoints():
        if north == 0.0 or north < point[1]: north = point[1]
        if south == 0.0 or south > point[1]: south = point[1]
        if east == 0.0 or east < point[0]: east = point[0]
        if west == 0.0 or west > point[0]: west = point[0]
      tuples.append((west, south, east, north))

    return tuples

  def to_shaply_object(self):
    shapely_objects = []
    for i in range(self.layer.GetFeatureCount()):
      feature = self.layer.GetFeature(i)
      shapely_objects.append(wkt.loads(feature.GetGeometryRef().ExportToWkt()))

    return shapely_objects

class Gxml(object):
  @staticmethod
  def save_to_kml(gxml, kml):
    geometry = Gxml(gxml)
    geometry.parse()
    geometry.tokml()
    geometry.save_kml(kml)

  def __init__(self, path):
    self.path = path
    self.parsed = None
    self.kml = None

  def tokml(self):
    self.kml = Kml()
    for area in self.parsed:
      self.kml.newpolygon(name=area[0], outerboundaryis=area[1])
    return self.kml

  def save_kml(self, path):
    self.kml.save(path)

  def parse(self):
    self.parsed = []
    with codecs.open(self.path, 'r', 'utf8') as f:
      root = ET.fromstring(f.read())
      geospace = root.find('./MetricGeospace')
      count = 0
      for node in geospace:
        count += 1
        if node.tag == 'GeometricFeature':
          ken_name = node.find('.//Property[@propertytypename="KEN_NAME"]').text
          css_name = node.find('.//Property[@propertytypename="CSS_NAME"]').text
          gst_name = node.find('.//Property[@propertytypename="GST_NAME"]').text
          kihon1 = node.find('.//Property[@propertytypename="KIHON1"]').text
          kihon2 = node.find('.//Property[@propertytypename="KIHON2"]').text
          moji = node.find('.//Property[@propertytypename="MOJI"]').text
          kcode1 = node.find('.//Property[@propertytypename="KCODE1"]').text
          key = '%s%s%s' %(
              ken_name, 
              gst_name, 
              moji, 
            )
          geometry = node.find('./Geometry//Coordinates').text
          self.parsed.append((key, [tuple(coordinate.split(',')) for coordinate in geometry.split(' ')]))
    return self.parsed

def get_polygon(path):
  shape = Shape(path)
  shape.load()
  return shape.union().to_shaply_object()[0]

def get_square_boundary(path):
  shape = Shape(path)
  shape.load()
  return shape.union().create_square_boundary().to_tuple()[0]

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("-o", dest="output", help="pass the path/to/geohash.json", metavar="FILE")
  parser.add_option("--kml", dest="kml", help="pass the path/to/*.kml", metavar="FILE")

  (options, args) = parser.parse_args()

  # conn = sqlite3.connect('geohash.sqlite')
  # c = conn.cursor()
  # c.execute('drop table chikus;')
  # c.execute('create table chikus (chiku varchar(64), geohash varchar(64));')
  # conn.commit()
  # c.close()

  # Gxml.save_to_kml(args[0], options.kml)

  shape = Shape(args[0])
  shape.load()
  shape.union().create_buffer(0.01).create_square_boundary().tokml().save('whole.kml')
