(function() {
  "use strict";
  var APPID, AllocationManager, Aza, Banchi, Gaiku, Mapview, Node, SubNode, YOLP, absorbError, allocationManager, bit_lat, bit_lon, failGetLocation, generatePulldownList, geo_hash_precision, getLocation, horizontal_unit, jsonp, loadlib, reverseGeoCode, sample_lat, sample_lon, self, successGetLocation, unit_angle_lat, unit_angle_lon, vertical_unit,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  YOLP = 'http://reverse.search.olp.yahooapis.jp/OpenLocalPlatform/V1/reverseGeoCoder';

  APPID = 'dj0zaiZpPWowM3hJMjNhNEVhSSZzPWNvbnN1bWVyc2VjcmV0Jng9ODM-';

  sample_lat = 36.562798;

  sample_lon = 136.672046;

  String.prototype.toOneByteAlphaNumeric = function() {
    return this.replace(/[Ａ-Ｚａ-ｚ０-９]/g, function(s) {
      return String.fromCharCode(s.charCodeAt(0) - 0xFEE0);
    });
  };

  loadlib = function(path) {
    var script;
    script = document.createElement('script');
    script.setAttribute('type', 'text/javascript');
    script.setAttribute('src', path);
    return document.head.appendChild(script);
  };

  jsonp = function(url, data, callback) {
    var k, v;
    return $.ajax({
      type: 'GET',
      url: url,
      dataType: 'jsonp',
      data: ((function() {
        var _results;
        _results = [];
        for (k in data) {
          v = data[k];
          _results.push(["" + k + "=" + v]);
        }
        return _results;
      })()).join('&'),
      success: callback
    });
  };

  getLocation = function(success, fail) {
    return navigator.geolocation.getCurrentPosition(success, fail, {
      enableHighAccuracy: true,
      timeout: 5000
    });
  };

  successGetLocation = function(position) {
    return reverseGeoCode(position.coords.latitude, position.coords.longitude, position.coords.accuracy);
  };

  failGetLocation = function(error) {
    return console.log(error.message);
  };

  reverseGeoCode = function(lat, lon, accuracy, callback) {
    if (callback == null) {
      callback = null;
    }
    callback = callback || successReverseGeocode;
    return jsonp(YOLP, {
      appid: APPID,
      lat: lat,
      lon: lon,
      output: 'json',
      datum: 'wgs',
      callback: 'successReverseGeocode'
    }, callback);
  };

  geo_hash_precision = 9;

  vertical_unit = 4.763;

  horizontal_unit = 3.849;

  bit_lat = Math.ceil(geo_hash_precision * 5 / 2);

  bit_lon = Math.floor(geo_hash_precision * 5 / 2);

  unit_angle_lat = 180 / Math.pow(2, bit_lat);

  unit_angle_lon = 360 / Math.pow(2, bit_lon);

  absorbError = function(lat, lon, accuracy, callback) {
    var accuracy_as_angle, center_hash, diff_lat, diff_lon, east_lat, sum_of_horizontal_unit, sum_of_vertical_unit, _results;
    if (callback == null) {
      callback = null;
    }
    center_hash = new GeoHash();
    center_hash.encode(lat, lon);
    accuracy_as_angle = accuracy;
    east_lat = diff_lat = center_hash.center_lat - lat;
    diff_lon = center_hash.center_lon - lon;
    sum_of_vertical_unit = vertical_unit / 2;
    sum_of_horizontal_unit = horizontal_unit / 2;
    _results = [];
    while (accuracy < sum_of_vertical_unit && accuracy < sum_of_horizontal_unit) {
      if (accuracy > sum_of_vertical_unit) {
        _results.push(sum_of_vertical_unit += vertical_unit);
      } else {
        _results.push(void 0);
      }
    }
    return _results;
  };

  allocationManager = null;

  AllocationManager = (function() {
    function AllocationManager() {}

    AllocationManager.prototype.getAllocationData = function(address, callback) {
      if (!this.aza) {
        return $.getJSON('./allocation.json', function(data) {
          this.aza = new Aza(data);
          return this.aza.generateChikuList(address, callback);
        });
      } else {
        return this.aza.generateChikuList(address, callback);
      }
    };

    return AllocationManager;

  })();

  Node = (function() {
    function Node(allocation) {
      this.allocation = allocation;
      this.nodes = {};
      this.key = null;
    }

    return Node;

  })();

  SubNode = (function(_super) {
    __extends(SubNode, _super);

    function SubNode(parentNode, allocation, address) {
      this.parentNode = parentNode;
      this.allocation = allocation;
      this.address = address;
      SubNode.__super__.constructor.call(this, this.allocation);
    }

    return SubNode;

  })(Node);

  Aza = (function(_super) {
    __extends(Aza, _super);

    function Aza() {
      return Aza.__super__.constructor.apply(this, arguments);
    }

    Aza.generateList = function(struct, text) {
      var k, list, v;
      if (text == null) {
        text = '';
      }
      list = [];
      for (k in struct) {
        v = struct[k];
        if (typeof v === 'object') {
          list = Array.prototype.concat.apply(list, this.generateList(v, "" + text + k + ":"));
        } else {
          list.push(text + ("" + k + ":" + v));
        }
      }
      return list;
    };

    Aza.prototype.generateChikuList = function(address, callback) {
      var aza_under, m, name, struct, _;
      this.address = address;
      struct = {};
      aza_under = null;
      m = /^石川県金沢市(.*)$/.exec(this.address);
      if (m) {
        aza_under = m[1];
        m = RegExp("" + ("^(" + (((function() {
          var _ref, _results;
          _ref = this.allocation;
          _results = [];
          for (name in _ref) {
            _ = _ref[name];
            _results.push(name);
          }
          return _results;
        }).call(this)).join('|')) + ")(.*)$")).exec(aza_under);
        if (m) {
          this.key = m[1];
          this.nodes[this.key] = new Gaiku(this, this.allocation[this.key], m[2]).narrow();
        } else {
          alert('The Aza that corresponds to the allocation-data could not be found. aza :' + aza_under);
        }
      } else {
        alert('Not in Kanazawa. address :' + this.address);
      }
      return callback(this.nodes);
    };

    return Aza;

  })(Node);

  Gaiku = (function(_super) {
    __extends(Gaiku, _super);

    function Gaiku() {
      return Gaiku.__super__.constructor.apply(this, arguments);
    }

    Gaiku.prototype.narrow = function() {
      var banchi_under, k, m, number, r, v, _, _ref;
      if (this.address === '' && !this.allocation['']) {
        _ref = this.allocation;
        for (k in _ref) {
          v = _ref[k];
          this.nodes[k] = new Banchi(this, v, this.address).narrow();
        }
      } else {
        r = RegExp("" + ("^(-|－)*(" + (((function() {
          var _ref1, _results;
          _ref1 = this.allocation;
          _results = [];
          for (number in _ref1) {
            _ = _ref1[number];
            if (number !== '') {
              _results.push(number);
            }
          }
          return _results;
        }).call(this)).sort(function(a, b) {
          return b - a;
        }).join('|')) + ")(.*)$"));
        m = r.exec(this.address.toOneByteAlphaNumeric());
        if (m) {
          this.key = m[2];
          banchi_under = m[3];
        } else if (this.allocation['']) {
          this.key = '';
          banchi_under = this.address;
        } else if (this.allocation['others']) {
          this.key = 'others';
          banchi_under = null;
          this.nodes[''] = new Banchi(this, this.allocation[this.key], this.address).narrow();
        } else {
          alert("The Gaiku that corresponds to the allocation-data could not be found.\naddress :" + this.parentNode.address + " gaiku :" + this.address);
          banchi_under = null;
        }
        if (banchi_under !== null) {
          this.nodes[this.key] = new Banchi(this, this.allocation[this.key], banchi_under).narrow();
        }
      }
      return this.nodes;
    };

    return Gaiku;

  })(SubNode);

  Banchi = (function(_super) {
    __extends(Banchi, _super);

    function Banchi() {
      return Banchi.__super__.constructor.apply(this, arguments);
    }

    Banchi.prototype.bottomUp = function() {
      var banchi, bu, chiku, _i, _len, _ref;
      bu = {};
      _ref = (function() {
        var _ref, _results;
        _ref = this.allocation;
        _results = [];
        for (banchi in _ref) {
          chiku = _ref[banchi];
          _results.push(banchi.toOneByteAlphaNumeric());
        }
        return _results;
      }).call(this);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        banchi = _ref[_i];
        if (!bu[this.allocation[banchi]]) {
          bu[this.allocation[banchi]] = [banchi];
        } else {
          bu[this.allocation[banchi]].push(banchi);
        }
      }
      return bu;
    };

    Banchi.prototype.integrateBanchis = function(banchis) {
      var banchi, number, numbers, ret, temp, texts, _i, _len, _ref;
      if (banchis == null) {
        banchis = [];
      }
      temp = [];
      ret = [];
      numbers = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = banchis.length; _i < _len; _i++) {
          banchi = banchis[_i];
          if (!(banchi === '' || isNaN(banchi - 0))) {
            _results.push(banchi - 0);
          }
        }
        return _results;
      })();
      texts = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = banchis.length; _i < _len; _i++) {
          banchi = banchis[_i];
          if (banchi === '' || isNaN(banchi - 0)) {
            _results.push(banchi);
          }
        }
        return _results;
      })();
      _ref = numbers.sort(function(a, b) {
        return a - b;
      });
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        number = _ref[_i];
        number -= 0;
        if (temp.length === 0 || temp.slice(-1)[0] + 1 === number) {
          temp.push(number);
        } else {
          ret.push(this.broadOrSingle(temp));
          temp = [number];
        }
      }
      ret.push(this.broadOrSingle(temp));
      ret = Array.prototype.concat.apply(ret, texts);
      return ret;
    };

    Banchi.prototype.broadOrSingle = function(list) {
      if (list.length > 1) {
        return "" + list[0] + "〜" + (list.slice(-1)[0]);
      } else {
        return list[0];
      }
    };

    Banchi.prototype.checkMoreThan = function(banchi_under, narrowed_allocation) {
      var k, m, prefix, r, v, value;
      r = /^([^0-9]*?)([0-9]+?)〜$/;
      prefix = null;
      value = null;
      for (k in narrowed_allocation) {
        v = narrowed_allocation[k];
        m = r.exec(k);
        if (m) {
          prefix = m[1];
          value = m[2];
          break;
        }
      }
      if ((value !== null) && (banchi_under !== '')) {
        r = /^(-|－)?([^0-9]*?)([0-9]+)$/;
        m = r.exec(banchi_under);
        if (m && (m[3] - 0) >= (value.toOneByteAlphaNumeric() - 0)) {
          if (prefix !== null && prefix === m[2]) {
            return [m[3], prefix + value + '〜'];
          } else {
            return [m[3], value + '〜'];
          }
        } else {
          return null;
        }
      } else {
        return null;
      }
    };

    Banchi.prototype.narrow = function(callback) {
      var banchis, bu, chiku, m, moreThan, number, r, _;
      if (this.address === '' && !this.allocation['']) {
        if (this.parentNode.parentNode.allocation['others']) {
          this.nodes['others'] = this.parentNode.parentNode.allocation['others'];
        }
        bu = this.bottomUp();
        for (chiku in bu) {
          banchis = bu[chiku];
          this.nodes[this.integrateBanchis(banchis).join(',')] = chiku;
        }
      } else {
        r = RegExp("" + ("^(-|－)*(" + (((function() {
          var _ref, _results;
          _ref = this.allocation;
          _results = [];
          for (number in _ref) {
            _ = _ref[number];
            if (number !== '') {
              _results.push(number);
            }
          }
          return _results;
        }).call(this)).sort(function(a, b) {
          return b - a;
        }).join('|')) + ")$"));
        m = r.exec(this.address);
        if (m) {
          this.key = m[2];
          this.nodes[this.key] = this.allocation[this.key];
        } else {
          moreThan = this.checkMoreThan(this.address, this.allocation);
          if (moreThan !== null) {
            this.key = moreThan[0];
            this.nodes[this.key] = this.allocation[moreThan[1]];
          } else if (this.allocation['']) {
            this.key = '';
            this.nodes[this.key] = this.allocation[''];
          } else if (this.parentNode.allocation['others']) {
            this.nodes[''] = this.parentNode.allocation['others'];
          } else {
            alert("The Banchi that corresponds to the allocation-data could not be found.\naddress :" + this.parentNode.parentNode.address + " banchi :" + this.address);
          }
        }
      }
      return this.nodes;
    };

    return Banchi;

  })(SubNode);

  self = null;

  Mapview = (function() {
    function Mapview() {
      var latlon, opts;
      this.infowindow = new google.maps.InfoWindow();
      this.marker = null;
      self = this;
      this.geocoder = new google.maps.Geocoder();
      latlon = new google.maps.LatLng(sample_lat, sample_lon);
      opts = {
        zoom: self.zoomLevel = 18,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        center: latlon
      };
      this.map = new google.maps.Map(document.getElementById("map"), opts);
      google.maps.event.addListener(this.map, 'zoom_changed', function() {
        return self.zoomLevel = self.map.getZoom();
      });
      google.maps.event.addListener(this.map, 'click', this.codeLatLng);
    }

    Mapview.prototype.codeLatLng = function(event) {
      var lat, latlon, lon;
      lat = event.latLng.lat();
      lon = event.latLng.lng();
      latlon = new google.maps.LatLng(lat, lon);
      return reverseGeoCode.call(self, lat, lon, 10, function(result) {
        if (allocationManager === null) {
          allocationManager = new AllocationManager();
        }
        return allocationManager.getAllocationData(result['Feature'][0]['Property']['Address'], function(chiku_list) {
          var chiku, list;
          self.marker = new google.maps.Marker({
            position: latlon,
            map: self.map
          });
          list = Aza.generateList(chiku_list, "" + (Math.floor(lat * 1000000) / 1000000) + "," + (Math.floor(lon * 1000000) / 1000000) + "," + result['Feature'][0]['Property']['Address'] + ":");
          self.infowindow.setContent(window['Templates']['infowindow'].render({
            content: (function() {
              var _i, _len, _results;
              _results = [];
              for (_i = 0, _len = list.length; _i < _len; _i++) {
                chiku = list[_i];
                _results.push({
                  item: chiku
                });
              }
              return _results;
            })()
          }));
          self.infowindow.open(self.map, self.marker);
          return document.getElementById("ui").innerHTML = window['Templates']['pulldown'].render({
            'single_choices': (function() {
              var _i, _len, _ref, _results;
              _ref = generatePulldownList(chiku_list);
              _results = [];
              for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                chiku = _ref[_i];
                _results.push({
                  item: chiku
                });
              }
              return _results;
            })()
          });
        });
      });
    };

    return Mapview;

  })();

  generatePulldownList = function(struct, text) {
    var k, list, v;
    if (text == null) {
      text = '';
    }
    list = [];
    for (k in struct) {
      v = struct[k];
      if (typeof v === 'object') {
        list = Array.prototype.concat.apply(list, generatePulldownList(v, "" + text + k));
      } else {
        list.push(text + ("" + (k !== '' ? '-' : '') + k + " --- " + v));
      }
    }
    return list;
  };

  $(function() {
    loadlib("./geohash.js");
    loadlib("./template.js");
    return new Mapview();
  });

}).call(this);
