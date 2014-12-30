window.StyleAttribute = Backbone.Model.extend
  defaults:
    name : ""
    cssName : ''
    datatype : ''
    linkToData : false
    choices : null
    defaultValue : null
    value : null


StyleAttributeCollection = Backbone.Collection.extend
  model : StyleAttribute

AttributeView = Backbone.Marionette.ItemView.extend
  template: (jsn) ->
    html = this.templates[jsn.datatype][if jsn.linkToData then "linked" else "unlinked"]
    _.template html, jsn

  templates:
    opacity:
      linked: $ "tpl-opacity-by-data"
      unlinked: $ "#tpl-opacity-by-val"
    value:
      linked: $ "#tpl-value-by-data"
      unlinked: $ "#tpl-value-by-val"
    float:
      linked: $ "#tpl-float-by-data"
      unlinked: $ "#tpl-float-by-val"
    integer:
      linked: $ "#tpl-integer-by-data"
      unlinked: $ "#tpl-integer-by-val"
    string:
      linked: $ "#tpl-string-by-data"
      unlinked: $ "#tpl-string-by-val"
    file:
      linked: $ "#tpl-file-by-data"
      unlinked: $ "#tpl-file-by-val"
    color:
      linked: $ "#tpl-color-by-data"
      unlinked: $ "#tpl-color-by-val"
    font:
      linked: $ "#tpl-font-by-data"
      unlinked: $ "#tpl-font-by-val"



mapAttributes = new StyleAttributeCollection [
  { name : 'Base opacity', cssName: 'opacity', datatype: 'opacity', linkToData: false, defaultValue: 1.0 }
]

polygonAttributes = new StyleAttributeCollection [
  { name : 'Fill color', cssName : 'polygon-fill', datatype: 'color', linkToData: true, defaultValue: "#fcfc66" }
  { name : 'Fill opacity', cssName : 'polygon-opacity', datatype: 'opacity', linkToData: true, defaultValue: 0.6 }
]

lineAttributes = new StyleAttributeCollection [
  { name: 'Line color', cssName: 'line-color', datatype: 'color', linkToData: true, defaultValue: "#000000" }
  { name: 'Line opacity', cssName: 'line-opacity', datatype: 'opacity', linkToData: true, defaultValue: 1.0 }
  { name: 'Line width', cssName: 'line-width', datatype: 'float', linkToData: true, defaultValue: 1.0 }
  { name: 'Line join', cssName: 'line-join', datatype: 'value', linkToData: false, choices: ['miter','round','bevel'], defaultValue: 'miter' }
  { name: 'Line cap', cssName: 'line-cap', datatype: 'value', linkToData: false, choices: ['butt','round','square'], defaultValue: 'miter' }
]

markerAttributes = new StyleAttributeCollection [
  { name: 'Icon file', cssName: 'marker-file', datatype: 'file', linkToData: true, defaultValue: null }
  { name: 'Overall opacity', cssName: 'marker-opacity', datatype: 'opacity', linkToData: true, defaultValue: 0.6 }
  { name: 'Outline opacity', cssName: 'marker-line-opacity', datatype: 'opacity', linkToData: true, defaultValue: 0.6 }
  { name: 'Outline color', cssName: 'marker-line-color', datatype: 'color', linkToData: true, defaultValue: "#000000" }
  { name: 'Outline width', cssName: 'marker-line-width', datatype: 'float', linkToData: true, defaultValue: 1.0 }
  { name: 'Fill opacity', cssName: 'marker-fill-opacity', datatype: 'opacity', linkToData: true, defaultValue: 0.6 }
  { name: 'Fill color', cssName: 'marker-fill', datatype: 'color', linkToData: true, defaultValue: "#fcfc66" }
  { name: 'Placement', cssName: 'marker-placement', datatype: 'value', choices: ["point","line","interior"], linkToData: false, defaultValue: "point" }
  { name: 'Type', cssName: 'marker-type', datatype: 'value', choices: ["arrow","ellipse"], linkToData: false, defaultValue: "ellipse" }
  { name: 'Width', cssName: 'marker-width', datatype: 'float', linkToData: true, defaultValue: 6.0 }
  { name: 'Height', cssName: 'marker-height', datatype: 'float', linkToData: true, defaultValue: 6.0 }
  { name: 'Allow overlap', cssName: 'marker-allow-overlap', datatype: 'boolean', linkToData: false, defaultValue: false }
]

shieldAttributes = new StyleAttributeCollection [
  { name: "Label", "cssName" : "shield-name", datatype: "string", linkToData: true, defaultValue: null}
  { name: 'Icon file', cssName: 'shield-file', datatype: 'file', linkToData: true, defaultValue: null }
  { name: 'Font', cssName: 'shield-face-name', datatype: 'font', linkToData: false, defaultValue: "DejaVu Sans" }
  { name: 'Text next to image', cssName: 'shield-unlock-image', datatype: 'boolean', linkToData: false, defaultValue: null }
  { name: "Text size", cssName: "shield-size", datatype: 'float', linkToData: true, defaultValue: 12 }
  { name: 'Fill color', cssName: 'shield-fill', datatype: 'color', linkToData: true, defaultValue: "#fcfc66" }
  { name: 'Placement', cssName: 'shield-placement', datatype: 'value', choices: ["point", "line", "interior"], linkToData: false, defaultValue: "point" }
  { name: 'Allow overlap', cssName: 'shield-allow-overlap', datatype: 'boolean', linkToData: false, defaultValue: false }
  { name: "Min distance between markers", cssName: "shield-min-distance", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Min padding", cssName: "shield-min-padding", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Wrap width", cssName: "shield-wrap-width", datatype: "integer", linkToData: false, defaultValue: 0 }
  { name: "Wrap before edge", cssName: "shield-min-padding", datatype: "boolean", linkToData: false, defaultValue: false }
  { name: "Wrap character (if not space)", cssName: "shield-wrap-character", datatype: "string", linkToData: false, defaultValue: null }
  { name: "Halo color", cssName: "shield-halo-fill", datatype: "color", linkToData: false, defaultValue: null }
  { name: "Halo radius", cssName: "shield-halo-radius", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Character spacing", cssName: "shield-character-spacing", datatype: "integer", linkToData: false, defaultValue: 0 }
  { name: "Line spacing", cssName: "shield-line-spacing", datatype: "integer", linkToData: false, defaultValue: null }
  { name: "Horizontal offset", cssName: "shield-text-dx", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Vertical offset", cssName: "shield-text-dy", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Opacity", cssName: "shield-opacity", datatype: "opacity", linkToData: true, defaultValue: 1.0 }
  { name: "Text opacity", cssName: "shield-text-opacity", datatype: "opacity", linkToData: true, defaultValue: 1.0 }
  { name: "Horizontal alignment", cssName: "shield-horizontal-alignment", datatype: "value", linkToData: false, choices : ['left','middle','right','auto'], defaultValue: 'auto'}
  { name: "Vertical alignment", cssName: "shield-vertical-alignment", datatype: "value", linkToData: false, choices : ['left','middle','right','auto'], defaultValue: 'auto'}
  { name: "Capitalization", cssName: "shield-text-transform", datatype: "value", linkToData: false, choices: ['none','uppercase','lowercase','capitalize'], defaultValue: 'none' }
  { name: "Text justification", cssName: "shield-justify-alignment", datatype: "value", linkToData: false, choices: ['left','center','right','auto'], defaultValue: 'auto' }
]

rasterAttributes = new StyleAttributeCollection [
  { name: 'Opacity', cssName: "raster-opacity", datatype: 'opacity', linkToData: false, defaultValue: 1.0 }
  { name: 'Scaling method', cssName: "raster-scaling", datatype: 'value', linkToData: false, defaultValue: 'near', choices:[
      "near"
      "fast"
      "bilinear"
      "bilinear8"
      "bicubic"
      "spline16"
      "spline36"
      "hanning"
      "hamming"
      "hermite"
      "kaiser"
      "quadric"
      "catrom"
      "gaussian"
      "bessel"
      "mitchell"
      "sinc"
      "lanczos"
      "blackman"
  ]}
]

pointAttributes = new StyleAttributeCollection [
  { name: 'File', cssName: "point-file", datatype: 'file', linkToData: true, defaultValue: null }
  { name: 'Allow overlap', cssName: "point-file", datatype: 'file', linkToData: true, defaultValue: null }
  { name: 'Opacity', cssName: "point-opacity", datatype: 'opacity', linkToData: true, defaultValue: 1.0 }
  { name: 'Placement', cssName: "point-placement", datatype: 'value', linkToData: true, defaultValue: 'centroid', choices: ['centroid','interior'] }
]

textAttributes = new StyleAttributeCollection [
  { name: "Label", "cssName": "text-name", datatype: "string", linkToData: true, defaultValue: null}
  { name: 'Font', cssName: 'text-face-name', datatype: 'font', linkToData: false, defaultValue: "DejaVu Sans" }
  { name: "Text size", cssName: "text-size", datatype: 'float', linkToData: true, defaultValue: 12 }
  { name: "Wrap ratio", cssName: "text-ratio", datatype: 'float', linkToData: true, defaultValue: 0 }
  { name: "Wrap width", cssName: "text-wrap-width", datatype: "integer", linkToData: false, defaultValue: 0 }
  { name: "Wrap before edge", cssName: "text-min-padding", datatype: "boolean", linkToData: false, defaultValue: false }
  { name: "Wrap character (if not space)", cssName: "text-wrap-character", datatype: "string", linkToData: false, defaultValue: null }
  { name: "Character spacing", cssName: "text-character-spacing", datatype: "integer", linkToData: false, defaultValue: 0 }
  { name: "Line spacing", cssName: "text-line-spacing", datatype: "integer", linkToData: false, defaultValue: null }
  { name: 'Fill color', cssName: 'text-fill', datatype: 'color', linkToData: true, defaultValue: "#fcfc66" }
  { name: "Opacity", cssName: "text-opacity", datatype: "opacity", linkToData: true, defaultValue: 1.0 }
  { name: "Halo color", cssName: "text-halo-fill", datatype: "color", linkToData: false, defaultValue: null }
  { name: "Halo radius", cssName: "text-halo-radius", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Horizontal alignment", cssName: "text-horizontal-alignment", datatype: "value", linkToData: false, choices: ['left', 'middle', 'right', 'auto'], defaultValue: 'auto' }
  { name: "Min distance between markers", cssName: "text-min-distance", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: "Min padding", cssName: "text-min-padding", datatype: "float", linkToData: false, defaultValue: 0 }
  { name: 'Placement', cssName: 'text-placement', datatype: 'value', choices: ["point", "line","interior"], linkToData: false, defaultValue: "point" }
  { name: 'Allow overlap', cssName: 'text-allow-overlap', datatype: 'boolean', linkToData: false, defaultValue: false }
  { name: "Capitalization", cssName: "text-text-transform", datatype: "value", linkToData: false, choices: ['none','uppercase','lowercase','capitalize'], defaultValue: 'none' }
  { name: "Text justification", cssName: "text-justify-alignment", datatype: "value", linkToData: false, choices: ['left', 'center', 'right', 'auto'], defaultValue: 'auto' }
  { name: "Rotation", cssName: 'text-orientation', datatype: "float", linkToData: true, defaultValue : 0}
]

buildingAttributes = new StyleAttributeCollection [
  { name: 'Fill color', cssName: 'building-fill', datatype: 'color', linkToData: true, defaultValue: "#fcfc66" }
  { name: "Opacity", cssName: "building-fill-opacity", datatype: "opacity", linkToData: true, defaultValue: 1.0 }
  { name: "Height", cssName: "building-height", datatype: "float", linkToData: true, defaultValue: 0 }
]
