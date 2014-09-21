#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scripts.plotter import geocode, list_geohashes, GeoHash

boundary = geocode('石川県金沢市城南二丁目22')
west, south, east, north = boundary
north_west = GeoHash().encode(north, west)
north_east = GeoHash().encode(north, east)
