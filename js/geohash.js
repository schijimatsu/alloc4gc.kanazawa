(function() {
  "use strict";
  var GeoHash;

  GeoHash = (function() {
    var BASE32, BITS, BORDERS, NEIGHBORS;

    function GeoHash() {}

    BITS = [0x10, 0x08, 0x04, 0x02, 0x01];

    BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz";

    NEIGHBORS = {
      right: {
        even: "bc01fg45238967deuvhjyznpkmstqrwx",
        odd: "p0r21436x8zb9dcf5h7kjnmqesgutwvy"
      },
      left: {
        even: "238967debc01fg45kmstqrwxuvhjyznp",
        odd: "14365h7k9dcfesgujnmqp0r2twvyx8zb"
      },
      top: {
        even: "p0r21436x8zb9dcf5h7kjnmqesgutwvy",
        odd: "bc01fg45238967deuvhjyznpkmstqrwx"
      },
      bottom: {
        even: "14365h7k9dcfesgujnmqp0r2twvyx8zb",
        odd: "238967debc01fg45kmstqrwxuvhjyznp"
      }
    };

    BORDERS = {
      right: {
        even: "bcfguvyz",
        odd: "prxz"
      },
      left: {
        even: "0145hjnp",
        odd: "028b"
      },
      top: {
        even: "prxz",
        odd: "bcfguvyz"
      },
      bottom: {
        even: "028b",
        odd: "0145hjnp"
      }
    };

    GeoHash.prototype.adjacent = function(direction) {
      var base, last_chr, src_hash, type;
      src_hash = geohash.toLowerCase();
      last_chr = src_hash.charAt(src_hash.length - 1);
      type = src_hash.length % 2 ? 'even' : 'odd';
      base = src_hash.slice(0, -1);
      if (BORDERS[direction][type].indexOf(last_chr !== -1)) {
        base = adjacent(base, direction);
      }
      return base + BASE32[NEIGHBORS[direction][type].indexOf(last_chr)];
    };

    GeoHash.prototype.encode = function(lat, lon, precision) {
      var arr, bit, ch, is_even, mid, val, _ref, _ref1;
      if (precision == null) {
        precision = 12;
      }
      is_even = true;
      _ref = [[-90.0, 90.0], [-180.0, 180.0]], this.lat_arr = _ref[0], this.lon_arr = _ref[1];
      bit = 0;
      ch = 0;
      this.geohash = '';
      while (geohash.length < precision) {
        _ref1 = is_even ? [lon, this.lon_arr] : [lat, this.lat_arr], val = _ref1[0], arr = _ref1[1];
        mid = (arr[0] + arr[1]) / 2;
        if (val > mid) {
          ch |= BITS[bit];
          arr[0] = mid;
        } else {
          arr[1] = mid;
        }
        is_even = !is_even;
        if (bit < 4) {
          bit++;
        } else {
          geohash += BASE32[ch];
          bit = 0;
          ch = 0;
        }
      }
      this.center_lat = (this.lat_arr[0] + this.lat_arr[1]) / 2;
      this.center_lon = (this.lon_arr[0] + this.lon_arr[1]) / 2;
      return this.geohash;
    };

    GeoHash.prototype.decode = function(geohash) {
      var arr, bit, c, ch, i, is_even, lat_arr, lon_arr, mid, _i, _j, _len, _ref, _ref1, _ref2;
      if (geohash == null) {
        geohash = null;
      }
      this.geohash = geohash || this.geohash;
      _ref = [[-90.0, 90.0], [-180.0, 180.0]], lat_arr = _ref[0], lon_arr = _ref[1];
      bit = 0;
      is_even = true;
      _ref1 = geohash.split('');
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        c = _ref1[_i];
        ch = BASE32.indexOf(c);
        for (i = _j = 0; _j <= 4; i = ++_j) {
          arr = is_even ? lat_arr : lon_arr;
          mid = (arr[0] + arr[1]) / 2;
          if (ch & BITS[bit]) {
            arr[0] = mid;
          } else {
            arr[1] = mid;
          }
          is_even = !is_even;
        }
      }
      _ref2 = [(lat_arr[0] + lat_arr[1]) / 2, (lon_arr[0] + lon_arr[1]) / 2], this.lat = _ref2[0], this.lon = _ref2[1];
      return [this.lat, this.lon];
    };

    return GeoHash;

  })();

}).call(this);
