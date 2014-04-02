"use strict"

class GeoHash
  BITS = [0x10, 0x08, 0x04, 0x02, 0x01]
  BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

  NEIGHBORS = 
    right:
      even: "bc01fg45238967deuvhjyznpkmstqrwx", 
      odd: "p0r21436x8zb9dcf5h7kjnmqesgutwvy", 
    ,
    left: 
      even: "238967debc01fg45kmstqrwxuvhjyznp", 
      odd: "14365h7k9dcfesgujnmqp0r2twvyx8zb", 
    ,
    top: 
      even: "p0r21436x8zb9dcf5h7kjnmqesgutwvy", 
      odd: "bc01fg45238967deuvhjyznpkmstqrwx", 
    ,
    bottom: 
      even: "14365h7k9dcfesgujnmqp0r2twvyx8zb", 
      odd: "238967debc01fg45kmstqrwxuvhjyznp", 
    ,

  BORDERS = 
    right: 
      even: "bcfguvyz", 
      odd: "prxz", 
    ,
    left: 
      even: "0145hjnp", 
      odd: "028b", 
    ,
    top: 
      even: "prxz", 
      odd: "bcfguvyz", 
    ,
    bottom: 
      even: "028b", 
      odd: "0145hjnp", 
    ,
  
  adjacent: (direction) ->
    src_hash = geohash.toLowerCase()
    last_chr = src_hash.charAt src_hash.length-1
    type = if src_hash.length % 2 then 'even' else 'odd'
    base = src_hash.slice 0, -1
    if BORDERS[direction][type].indexOf last_chr != -1
      base = adjacent base, direction
    return base + BASE32[NEIGHBORS[direction][type].indexOf last_chr]

  encode: (lat, lon, precision=12) ->
    is_even = true
    [@lat_arr, @lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    ch = 0
    @geohash = ''

    while geohash.length < precision
      [val, arr] = if is_even then [lon, @lon_arr] else [lat, @lat_arr]
      mid = (arr[0] + arr[1]) / 2
      if val > mid
        ch |= BITS[bit]
        arr[0] = mid
      else
        arr[1] = mid

      is_even = not is_even
      if bit < 4
        bit++
      else
        geohash += BASE32[ch]
        bit = 0
        ch = 0
  
    @center_lat = (@lat_arr[0]+@lat_arr[1])/2
    @center_lon = (@lon_arr[0]+@lon_arr[1])/2
    
    return @geohash

  decode: (geohash=null) ->
    @geohash = geohash || @geohash
    [lat_arr, lon_arr] = [[-90.0, 90.0], [-180.0, 180.0]]
    bit = 0
    is_even = true

    for c in geohash.split ''
      ch = BASE32.indexOf c
      for i in [0..4]
        arr = if is_even then lat_arr else lon_arr
        mid = (arr[0] + arr[1]) / 2
        if ch & BITS[bit]
          arr[0] = mid
        else
          arr[1] = mid
      
        is_even = not is_even

    [@lat, @lon] = [(lat_arr[0]+lat_arr[1])/2, (lon_arr[0]+lon_arr[1])/2]
    return [@lat, @lon]
