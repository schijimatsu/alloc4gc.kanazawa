"use strict"

YOLP = 'http://reverse.search.olp.yahooapis.jp/OpenLocalPlatform/V1/reverseGeoCoder'
APPID = 'dj0zaiZpPWowM3hJMjNhNEVhSSZzPWNvbnN1bWVyc2VjcmV0Jng9ODM-'
# sample_lat = 36.55918528912932
# sample_lon = 136.6466188430786

# 菊川
# sample_lat = 36.552331
# sample_lon = 136.659911

# 小立野
# sample_lat =  36.549935
# sample_lon = 136.673368

# 暁町
sample_lat = 36.562798
sample_lon = 136.672046

# sample_json = "{\"ResultInfo\":{\"Count\":1,\"Total\":1,\"Start\":1,\"Latency\":0.0035960674285889,\"Status\":200,\"Description\":\"指定の地点の住所情報を取得する機能を提供します。\",\"Copyright\":\"Copyright (C) 2014 Yahoo Japan Corporation. All Rights Reserved.\",\"CompressType\":\"\"},\"Feature\":[{\"Property\":{\"Country\":{\"Code\":\"JP\",\"Name\":\"日本\"},\"Address\":\"石川県金沢市菊川２丁目１３\",\"AddressElement\":[{\"Name\":\"石川県\",\"Kana\":\"いしかわけん\",\"Level\":\"prefecture\",\"Code\":\"17\"},{\"Name\":\"金沢市\",\"Kana\":\"かなざわし\",\"Level\":\"city\",\"Code\":\"17201\"},{\"Name\":\"菊川\",\"Kana\":\"きくがわ\",\"Level\":\"oaza\"},{\"Name\":\"２丁目\",\"Kana\":\"２ちょうめ\",\"Level\":\"aza\"},{\"Name\":\"１３\",\"Kana\":\"１３\",\"Level\":\"detail1\"}],\"Building\":[{\"Id\":\"B@llF_pR1sI\",\"Name\":\"\",\"Floor\":\"2\",\"Area\":\"\"}]},\"Geometry\":{\"Type\":\"point\",\"Coordinates\":\"136.65982335805893,36.552413515466455\"}}]}"

String.prototype.toOneByteAlphaNumeric = ->
  return @replace /[Ａ-Ｚａ-ｚ０-９]/g, (s) ->
    return String.fromCharCode s.charCodeAt(0) - 0xFEE0

loadlib = (path) ->
  script = document.createElement 'script'
  script.setAttribute 'type', 'text/javascript'
  script.setAttribute 'src', path
  document.head.appendChild script

jsonp = (url, data, callback) ->
  # console.log "calling jsonp."
  $.ajax {
    type: 'GET',
    url: url,
    dataType: 'jsonp', 
    data: (["#{k}=#{v}"] for k, v of data).join('&'), 
    success: callback, 
  }

getLocation = (success, fail) ->
  navigator.geolocation.getCurrentPosition success, fail, {
    enableHighAccuracy: true, 
    timeout: 5000, 
  }

successGetLocation = (position) ->
  # console.log "lat: #{position.coords.latitude}, lon: #{position.coords.longitude}, accuracy: #{position.coords.accuracy}"
  reverseGeoCode position.coords.latitude, position.coords.longitude, position.coords.accuracy

failGetLocation = (error) ->
  # console.log 'Error.'
  console.log error.message

reverseGeoCode = (lat, lon, accuracy, callback=null) ->
  callback = callback || successReverseGeocode
  # console.log callback
  jsonp YOLP, {
    appid: APPID, 
    lat: lat, 
    lon: lon, 
    output: 'json', 
    datum: 'wgs', 
    callback: 'successReverseGeocode', 
    # dist: Math.floor(accuracy*1000)/1000, 
  }, callback

geo_hash_precision = 9
vertical_unit = 4.763
horizontal_unit = 3.849
bit_lat = Math.ceil geo_hash_precision * 5 / 2
bit_lon = Math.floor geo_hash_precision * 5 / 2
unit_angle_lat = 180 / 2 ** bit_lat
unit_angle_lon = 360 / 2 ** bit_lon

absorbError = (lat, lon, accuracy, callback=null) ->
  center_hash = new GeoHash()
  center_hash.encode(lat, lon)
  accuracy_as_angle = accuracy
  east_lat = 
  diff_lat = center_hash.center_lat - lat
  diff_lon = center_hash.center_lon - lon
  sum_of_vertical_unit = vertical_unit / 2
  sum_of_horizontal_unit = horizontal_unit / 2
  while accuracy < sum_of_vertical_unit and accuracy < sum_of_horizontal_unit
    if accuracy > sum_of_vertical_unit
      sum_of_vertical_unit += vertical_unit

# @successReverseGeocode = (result) ->
#   # document.body.innerHTML = JSON.stringify result
#   address = result['Feature'][0]['Property']['Address']
#   getAllocationData.call @, address, (chiku_list) ->
#     for chiku in chiku_list
#       document.body.innerHTML += '*&nbsp;'+chiku+'<br/>'

allocationManager = null

class AllocationManager
  getAllocationData: (address, callback) ->
    if not @aza
      $.getJSON './allocation.json', (data) ->
        @aza = new Aza data
        @aza.generateChikuList address, callback
    else
      @aza.generateChikuList address, callback

class Node
  constructor: (@allocation) ->
    @nodes = {}
    @key = null

class SubNode extends Node
  constructor: (@parentNode, @allocation, @address) ->
    super(@allocation)

class Aza extends Node

  @generateList = (struct, text='') ->
    list = []
    for k, v of struct
      if typeof v == 'object'
        list = Array.prototype.concat.apply list, @generateList(v, "#{text}#{k}:")
      else
        list.push text+"#{k}:#{v}"
    
    return list

  generateChikuList: (@address, callback) ->
    struct = {}
    aza_under = null
    m = ///^石川県金沢市(.*)$///.exec @address
    if m
      aza_under = m[1]
      m = ///#{"^(#{(name for name, _ of @allocation).join('|')})(.*)$"}///.exec aza_under
      if m
        @key = m[1]
        @nodes[@key] = new Gaiku(@, @allocation[@key], m[2]).narrow()
      else
        alert 'The Aza that corresponds to the allocation-data could not be found. aza :'+aza_under
    else
      alert 'Not in Kanazawa. address :'+@address
    
    callback @nodes

class Gaiku extends SubNode
  narrow: () ->
    if @address == '' and not @allocation['']
      for k, v of @allocation
        @nodes[k] = new Banchi(@, v, @address).narrow()
    else
      r = ///#{"^(-|－)*(#{(number for number, _ of @allocation when number != '').sort((a, b) -> return b - a).join('|')})(.*)$"}///
      m = r.exec @address.toOneByteAlphaNumeric()
      if m
        @key = m[2]
        banchi_under = m[3]
      else if @allocation['']
        @key = ''
        banchi_under = @address
      else if @allocation['others']
        @key = 'others'
        banchi_under = null
        @nodes[''] = new Banchi(@, @allocation[@key], @address).narrow()
      else
        alert "The Gaiku that corresponds to the allocation-data could not be found.\naddress :#{@parentNode.address} gaiku :#{@address}"
        banchi_under = null
    
      if banchi_under != null
        @nodes[@key] = new Banchi(@, @allocation[@key], banchi_under).narrow()

    return @nodes

class Banchi extends SubNode

  bottomUp: () ->
    bu = {}
    for banchi in (banchi.toOneByteAlphaNumeric() for banchi, chiku of @allocation)
      if not bu[@allocation[banchi]]
        bu[@allocation[banchi]] = [banchi]
      else
        bu[@allocation[banchi]].push banchi
    
    return bu

  integrateBanchis: (banchis=[]) ->
    temp = []
    ret = []
    numbers = (banchi-0 for banchi in banchis when not (banchi == '' or isNaN (banchi-0)))
    texts = (banchi for banchi in banchis when banchi == '' or isNaN (banchi-0))
    for number in numbers.sort((a, b) -> return a - b)
      number -= 0
      if temp.length == 0 or temp.slice(-1)[0]+1 == number
        temp.push number
      else
        ret.push @broadOrSingle temp
        temp = [number]

    ret.push @broadOrSingle temp
    ret = Array.prototype.concat.apply ret, texts

    return ret

  broadOrSingle: (list) ->
    if list.length > 1
      return "#{list[0]}〜#{list.slice(-1)[0]}"
    else
      return list[0]

  checkMoreThan: (banchi_under, narrowed_allocation) ->
    r = ///^([^0-9]*?)([0-9]+?)〜$///
    prefix = null
    value = null
    for k, v of narrowed_allocation
      m = r.exec k
      if m
        prefix = m[1]
        value = m[2]
        break

    if (value != null) and (banchi_under != '')
      r = ///^(-|－)?([^0-9]*?)([0-9]+)$///
      m = r.exec banchi_under
      if m and (m[3]-0) >= (value.toOneByteAlphaNumeric()-0)
        if prefix != null and prefix == m[2]
          return [m[3], prefix+value+'〜']
        else
          return [m[3], value+'〜']
      else
        return null
    else
      return null

  narrow: (callback) ->
    if @address == '' and not @allocation['']
      if @parentNode.parentNode.allocation['others']
        @nodes['others'] = @parentNode.parentNode.allocation['others']

      bu = @bottomUp()
      for chiku, banchis of bu
        @nodes[@integrateBanchis(banchis).join ','] = chiku
    else
      r = ///#{"^(-|－)*(#{(number for number, _ of @allocation when number != '').sort((a, b) -> return b - a).join('|')})$"}///
      m = r.exec @address
      if m
        @key = m[2]
        @nodes[@key] = @allocation[@key]
      else
        moreThan = @checkMoreThan(@address, @allocation)
        if moreThan != null
          @key = moreThan[0]
          @nodes[@key] = @allocation[moreThan[1]]
        else if @allocation['']
          @key = ''
          @nodes[@key] = @allocation['']
        else if @parentNode.allocation['others']
          @nodes[''] = @parentNode.allocation['others']
        else
          alert "The Banchi that corresponds to the allocation-data could not be found.\naddress :#{@parentNode.parentNode.address} banchi :#{@address}"

    return @nodes

self = null
class Mapview
  constructor: () ->
    @infowindow = new google.maps.InfoWindow()
    @marker = null

    self = @
    @geocoder = new google.maps.Geocoder();
    latlon = new google.maps.LatLng(sample_lat, sample_lon)
    opts = {
      zoom: self.zoomLevel = 18, 
      mapTypeId: google.maps.MapTypeId.ROADMAP, 
      center: latlon, 
    }

    @map = new google.maps.Map(document.getElementById("map"), opts)

    google.maps.event.addListener @map, 'zoom_changed', ->
      self.zoomLevel = self.map.getZoom()

    google.maps.event.addListener @map, 'click', @codeLatLng

  codeLatLng: (event) ->
    lat = event.latLng.lat()
    lon = event.latLng.lng()
    latlon = new google.maps.LatLng lat, lon
    reverseGeoCode.call self, lat, lon, 10, (result) ->
      # console.log result
      if allocationManager == null
        allocationManager = new AllocationManager()
      allocationManager.getAllocationData result['Feature'][0]['Property']['Address'], (chiku_list) ->
        # self.map.setZoom self.zoomLevel
        self.marker = new google.maps.Marker {
          position: latlon, 
          map: self.map, 
        }
        list = Aza.generateList chiku_list, "#{Math.floor(lat*1000000)/1000000},#{Math.floor(lon*1000000)/1000000},#{result['Feature'][0]['Property']['Address']}:"
        self.infowindow.setContent window['Templates']['infowindow'].render {
          content: ({item: chiku} for chiku in list)
        }
        self.infowindow.open self.map, self.marker
        document.getElementById("ui").innerHTML = window['Templates']['pulldown'].render {
          'single_choices': ({item: chiku} for chiku in generatePulldownList chiku_list)
        }

generatePulldownList = (struct, text='') ->
  list = []
  for k, v of struct
    if typeof v == 'object'
      list = Array.prototype.concat.apply list, generatePulldownList(v, "#{text}#{k}")
    else
      list.push text+"#{if k != '' then '-' else ''}#{k} --- #{v}"
  
  return list

$(() ->
  loadlib "./geohash.js"
  loadlib "./template.js"
  new Mapview()
)
