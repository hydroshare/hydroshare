


# create a proxy layer class... possibly an OpenLayers derivate

imageLayer = (mp, lyr) ->
  src = mp.displayProjection
  dst = mp.projection

  sw = new OpenLayers.Geometry.Point lyr.west, lyr.south
  ne = new OpenLayers.Geometry.Point lyr.east, lyr.north
  sw = sw.transform src, dst
  ne = ne.transform src, dst

  bounds = new OpenLayers.Bounds(sw.x, sw.y, ne.x, ne.y)

  new OpenLayers.Layer.Image(
    lyr.name
    lyr.href
    bounds
    new OpenLayers.Size(lyr.width, lyr.height)
    { isBaseLayer: false, alwaysInRange: true }
  )


addlayers = (obj) -> (layers) ->
  obj.layers = (imageLayer obj.map, l for l in layers)
  obj.map.addLayers obj.layers
  (l.setVisibility obj.visibility for l in obj.layers)


class KmzLayerSet
  constructor: (@map, @identifier, @name) ->
    @opacity = 1.0
    @layers = []
    @isCompound = true
    @visibility = true

    @kml = new OpenLayers.Layer.Vector(
      name
      projection: @map.displayProjection
      strategies: [new OpenLayers.Strategy.Fixed]
      protocol: new OpenLayers.Protocol.HTTP
        url: "/ga_resources/kmz-features/#{@identifier}/"
        format: new OpenLayers.Format.KML
          extractStyles: true
          extractAttributes: true
    )
    @map.addLayers [@kml]
    $.getJSON "/ga_resources/kmz-coverages/#{@identifier}/", addlayers(this)

  setVisibility: (tf) ->
    if @layers.length then (l.setVisibility tf for l in @layers)
    @kml.setVisibility tf
    @visibility = tf

  setOpacity: (tf) ->
    if @layers.length then (l.setOpacity tf for l in @layers)
    @kml.setVisibility tf
    @opacity = tf


window.KmzLayerSet = KmzLayerSet
