$ ->

  # @style
  #
  # This is the style that gets submitted
  ######################################################################################################################
  
  window.finishedStyle = new Backbone.Model
    "line-color" : 'default',
    "polygon-fill" : 'default',
    "line-opacity" : 'default',
    "polygon-opacity" : 'default',
    "point-width" : 'default'
    "labels" : 'default'

  # @static-data
  #
  # setup static data.
  ######################################################################################################################

  # create a collection that points to all the CSS classes in colorbrewer.css and *.casc
  # klass: the outer classname for colorbrewer.css and the filename preface for *.casc to include in Cascadenik
  # min: the minimum number of classes that we have data for.
  # max: the maximum number of classes we have colors for
  # kind: Linear|Diverging|Categorical - the kind of palette we have, relating to the kind of data we have.
  paletteNames = [
    { klass: "YlGn", name: "Yellow to Green", min: 3, max: 9, kind: "Linear" }
    { klass: "YlGnBu", name: "Yellow to Green to Blue", min: 3, max: 9, kind: "Linear" }
    { klass: "GnBu", name: "Green to Blue", min: 3, max: 9, kind: "Linear" }
    { klass: "BuGn", name: "Blue to Green", min: 3, max: 9, kind: "Linear" }
    { klass: "PuBuGn", name: "Purple to Blue to Green", min: 3, max: 9, kind: "Linear" }
    { klass: "PuBu", name: "Purple to Blue", min: 3, max: 9, kind: "Linear" }
    { klass: "BuPu", name: "Blue to Purple", min: 3, max: 9, kind: "Linear" }
    { klass: "RdPu", name: "Red to Purple", min: 3, max: 9, kind: "Linear" }
    { klass: "PuRd", name: "Purple to Red", min: 3, max: 9, kind: "Linear" }
    { klass: "OrRd", name: "Orange to Red", min: 3, max: 9, kind: "Linear" }
    { klass: "YlOrRd", name: "Yellow to Orange to Red", min: 3, max: 9, kind: "Linear" }
    { klass: "YlOrBr", name: "Yellow to Orange to Brown", min: 3, max: 9, kind: "Linear" }
    { klass: "Purples", name: "Purples", min: 3, max: 9, kind: "Linear" }
    { klass: "Blues", name: "Blues", min: 3, max: 9, kind: "Linear" }
    { klass: "Greens", name: "Greens", min: 3, max: 9, kind: "Linear" }
    { klass: "Oranges", name: "Oranges", min: 3, max: 9, kind: "Linear" }
    { klass: "Reds", name: "Reds", min: 3, max: 9, kind: "Linear" }
    { klass: "Greys", name: "Greys", min: 3, max: 9, kind: "Linear" }
    { klass: "PuOr", name: "Purples to Oranges", min: 3, max: 11, kind: "Diverging" }
    { klass: "BrBG", name: "Brown to Blue-Grey", min: 3, max: 11, kind: "Diverging" }
    { klass: "PRGn", name: "Purple-Red to Green", min: 3, max: 11, kind: "Diverging" }
    { klass: "PiYG", name: "Pink to Yellow-Green", min: 3, max: 11, kind: "Diverging" }
    { klass: "RdBu", name: "Red to Blue", min: 3, max: 11, kind: "Diverging" }
    { klass: "RdGy", name: "Red to Grey", min: 3, max: 11, kind: "Diverging" }
    { klass: "RdYlBu", name: "Red to Yellow to Blue", min: 3, max: 11, kind: "Diverging" }
    { klass: "Spectral", name: "Spectral", min: 3, max: 11, kind: "Diverging" }
    { klass: "RdYlGn", name: "Red to Yellow to Green", min: 3, max: 11, kind: "Diverging" }
    { klass: "Accent", name: "Accent", min: 3, max: 8, kind: "Categorical" }
    { klass: "Dark2", name: "Dark", min: 3, max: 8, kind: "Categorical" }
    { klass: "Paired", name: "Paired", min: 3, max: 12, kind: "Categorical" }
    { klass: "Pastel", name: "Pastels", min: 3, max: 9, kind: "Categorical" }
    { klass: "Pastel2", name: "Pastels 2", min: 3, max: 8, kind: "Categorical" }
    { klass: "Set1", name: "Set 1", min: 3, max: 9, kind: "Categorical" }
    { klass: "Set2", name: "Set 2", min: 3, max: 8, kind: "Categorical" }
    { klass: "Set3", name: "Set 3", min: 3, max: 12, kind: "Categorical" }
  ]
  # Backbone models for the above data
  BrewerPalette = Backbone.Model.extend
    fqClass: (n, k) -> ".#{this.klass} .q#{k}-#{n}"  # the name of the CSS class that it represents.
    cascadenik: () -> "#{this.klass}.casc"  # the name of the cascadenik filename that contains this palette.
    cascClass: (n, k) -> "@#{this.klass}_#{n}_#{k}"  # the name of the color in the cascadenik file to be included.
  BrewerPaletteCollection = Backbone.Collection.extend
    model: BrewerPalette

  Field = Backbone.Model.extend
    defaults:
      min: 'N/A'
      max: "N/A"
      mean: "N/A"
      top: "N/A"
      freq: "N/A"
      unique: "N/A"
      std: "N/A"

    initialize: ->
      if this.attributes.uniques?
        this.set 'unique', this.attributes.uniques.length

    # whether or not this field contains category information
    isCategorical: -> "categorical" in this.attributes.tags

    # whether or not most of the values of this field are null
    isMostlyNull: -> "mostly null" in this.attributes.tags

    # whether or not this field contains a distribution of numbers
    isContinuous: -> "open ended" in this.attributes.tags

    # whether or not this field contains mostly unique values
    isUnique: -> "unique" in this.attributes.tags

    # whether or not this field is mostly full of null values
    isRarelyNull: -> "not null" in this.attributes.tags

    # whether or not this field is usually boolean
    isBoolean: -> "boolean" in this.attributes.tags

    # whether or not this field is boolean, but also contains nulls
    isTernary: ->
      ("boolean" in this.attributes.tags) and
      ("null" in this.attributes.tags)

    # if this field is continuous, then we return an even segmentation from its minimum to its maximum
    # else if this field is categorical, then we return a grouping of values among N classes
    segment: (classes) ->
      if this.isContinuous()
        max = this.attributes.max
        min = this.attributes.min
        step = (max-min) / classes
        (y for y in [min..max] by step)
      else if this.isCategorical()
        k = Math.round (this.attributes.uniques.length / classes)
        (this.attributes.uniques[i] for i in [0..this.attributes.uniques.length] by k)
      else []


  Schema = Backbone.Collection.extend
    model: Field

  # mockup data for now
  window.schema = new Schema window.attributes

  # A global variable representing all the palettes
  window.brewerPalettes = new BrewerPaletteCollection paletteNames


  # @palettes
  #
  # Code dealing with picking color palettes
  ######################################################################################################################
  
  # view for the 24 color "standard" palette.
  StdPaletteView = Backbone.Marionette.ItemView.extend
    template: "#tpl-standard-palette"
    tagName: "div"
    className: "btn-group"

    initialize: (opts) ->
      this.model = new Backbone.Model opts

    events:
      'click button': "onChangeColor"

    onChangeColor: (evt) ->
      $("input[type=text]", this.$el).val $("i", $(evt.currentTarget)).attr('data-color')

    onRender: ->
      this.$el.attr "data-toggle", "buttons-radio"
      $("i", this.$el).each ->
        color = $(this).data "color"
        $(this).attr "style", "color: #{color}"


  
  BrewerPaletteView = Backbone.Marionette.ItemView.extend
    template: "#tpl-brewer-palette"
    tagName: "option"
    onRender: ->
      this.$el.attr 'value', this.model.attributes.name
      this.$el.data "model", this.model

  # allow someone to select from different colorbrewer palettes
  ColorStylePickerView = Backbone.Marionette.CompositeView.extend
    initialize: (options) ->
      this.selector = options.selector

    template: "#tpl-color-picker"
    collection: window.brewerPalettes
    itemView: BrewerPaletteView
    itemViewContainer: "select.brewer-palettes"
    ui:
      numClassesBox: "select.num-classes"
      selectPaletteBox: "select.brewer-palettes"
      currentPalette: "div.current-palette"

    # create a number of segments in the data
    updatePaletteSelection: ->
        n = parseInt this.ui.numClassesBox.val()
        val = this.ui.selectPaletteBox.val()
        pal = $("option[value='#{val}']", this.ui.selectPaletteBox).data 'model'
        segments = this.model.segment n
        this.ui.currentPalette.empty()
        this.ui.currentPalette.append("""
          <div class='#{pal.attributes.klass}'>
            <i class='icon-stop q#{k}-#{n}'></i>
            starting at <input type='number' value='#{segments[k]}' class='segments'>
          </div>
        """) for k in [0...n]
        this.ui.numClassesBox.empty()
        checked = "checked"
        this.ui.numClassesBox.append((if k is n
          "<option value='#{k}' selected>#{k}</option>"
        else
          "<option value='#{k}'>#{k}</option")
        ) for k in [pal.attributes.min..pal.attributes.max]

        this.updateStyle()

    updateStyle: ->
      n = parseInt this.ui.numClassesBox.val()
      val = this.ui.selectPaletteBox.val()
      pal = $("option[value='#{val}']", this.ui.selectPaletteBox).data 'model'
      segments = (parseFloat($(k).val()) for k in $("input.segments", this.$el).toArray())

      window.finishedStyle.set this.selector, {
        attribute: this.model.attributes.name
        palette: pal.attributes.klass,
        kind: 'palette'
        n: n,
        segments: segments
      }

    onRender: -> this.updatePaletteSelection()

    events:
      "render": "updatePaletteSelection"
      "change select.num-classes": "updatePaletteSelection"
      "change select.brewer-palettes": "updatePaletteSelection"
      "change input.segments": 'updateStyle'

  # @opacity
  #
  # Code dealing with opacity
  ######################################################################################################################
  
  # A picker for opacity based on attribute values
  OpacityPickerView = Backbone.Marionette.ItemView.extend
    initialize: (options) ->
      this.selector = options.selector

    template: "#tpl-opacity-picker"
    ui:
      numClassesBox: "select.num-classes"
      classValues: "div.class-values"
      minOpacity: "input.minimum-opacity"
      maxOpacity: "input.maximum-opacity"

    onRender: -> this.updateOpacitySelection()

    # create a number of segments in the data.
    # fixme: this clobbers the values already entered, even if all you changed was the minimum or maximum opacity
    updateOpacitySelection: ->
      n = this.ui.numClassesBox.val()
      mn = if this.ui.minOpacity.val()? then parseFloat this.ui.minOpacity.val() else 0
      mx = if this.ui.maxOpacity.val()? then parseFloat this.ui.maxOpacity.val() else 100
      spread = (a/100.0  for a in [mn..mx] by ((mx-mn)/n))
      segments = this.model.segment n
      this.ui.classValues.empty()
      this.ui.classValues.append("""
        <div>
          <i class='icon-stop' style='opacity:#{spread[k]}'></i>
          starting at <input type='number' value='#{segments[k]}' class='segments'>
        </div>
      """) for k in [0...n]
      this.updateStyle()
      
    updateStyle: ->
      n = this.ui.numClassesBox.val()
      minOpacity = this.ui.minOpacity.val()
      maxOpacity = this.ui.maxOpacity.val()
      segments = (parseFloat($(k).val()) for k in $("input.segments", this.$el).toArray())
      window.finishedStyle.set this.selector, {
        attribute: this.model.attributes.name
        kind: 'spread'
        min: parseFloat(minOpacity)/100.0
        max: parseFloat(maxOpacity)/100.0
        n: n
        segments: segments
      }

    events:
      "render": "updateOpacitySelection"
      "change select.num-classes": "updateOpacitySelection"
      "change input.minimum-opacity": "updateOpacitySelection"
      "change input.maximum-opacity": "updateOpacitySelection"
      "change input.segments": "updateStyle"

  UniformOpacityView = Backbone.Marionette.ItemView.extend
    template: "#tpl-uniform-opacity"

    initialize: (opts) ->
      this.model = new Backbone.Model opts


  # @labels
  #
  # Code dealing with labels
  ######################################################################################################################
  
  LabelStylerView = Backbone.Marionette.ItemView.extend
    template: "#tpl-label-styler"
    ui:
      font: 'select[name=font]'
      textColor: 'select[name=text-color]'
      textSize: 'select[name=text-size]'

    events:
      'change select' : "updateStyle"

    onRender: -> this.updateStyle()
    updateStyle: ->
      console.log 'update style'
      window.finishedStyle.set 'labels',
        attribute: this.model.attributes.name
        kind: 'labels'
        font: this.ui.font.val()
        textColor: this.ui.textColor.val()
        textSize: this.ui.textSize.val()

  # @point-size
  #
  # Code dealing with point sizes
  ######################################################################################################################
  
  PointSizePickerView = Backbone.Marionette.ItemView.extend
    template: "#tpl-point-size-picker"
    ui:
      numClassesBox: "select.num-classes"
      classValues: "div.class-values"
      minSize: "input.minimum-size"
      maxSize: "input.maximum-size"

    onRender: -> this.updateSizeSelection()

    # create a number of segments in the data.
    # fixme: this clobbers the values already entered, even if all you changed was the minimum or maximum opacity
    updateSizeSelection: ->
      n = this.ui.numClassesBox.val()
      mn = if this.ui.minSize.val()? then parseFloat this.ui.minSize.val() else 1
      mx = if this.ui.maxSize.val()? then parseFloat this.ui.maxSize.val() else 24
      spread = (a  for a in [mn..mx] by ((mx-mn)/n))
      segments = this.model.segment n
      this.ui.classValues.empty()
      this.ui.classValues.append("""
        <div>
          <i class='icon-circle' style='font-size:#{spread[k]}px'></i>
          starting at <input type='number' value='#{segments[k]}' class='segments'>
        </div>
      """) for k in [0...n]
      this.updateStyle()
      
    updateStyle: ->
      n = parseInt(this.ui.numClassesBox.val())
      minSize = this.ui.minSize.val()
      maxSize = this.ui.maxSize.val()
      segments = (parseFloat($(k).val()) for k in $("input.segments", this.$el).toArray())
      window.finishedStyle.set "point-width", {
        attribute: this.model.attributes.name
        kind: 'spread'
        min: parseFloat(minSize)
        max: parseFloat(maxSize)
        n: n
        segments: segments
      }

    events:
      "render": "updateSizeSelection"
      "change select.num-classes": "updateSizeSelection"
      "change input.minimum-size": "updateSizeSelection"
      "change input.maximum-size": "updateSizeSelection"
      "change input.segments": "updateStyle"

  UniformPointSizeView = Backbone.Marionette.ItemView.extend
    template: "#tpl-uniform-point-size"

    initialize: (opts) ->
      this.model = new Backbone.Model opts


  # @attr-styler
  #
  # Code to render the attribute-styler table at the top of the page
  ######################################################################################################################
  
  AttributeStylerItemView = Backbone.Marionette.ItemView.extend
    template: "#tpl-style-by-attribute"
    tagName: 'tr'

  # for the next view - an event handler that shows a view whenever the attribute to style changes
  showView = (region, selector, uniformView, attributedView) -> () ->
    attribute = $(a).val() for a in $("input[name=#{selector}]", this.$el).toArray() when a.checked
    console.log attribute
    window.styler[region].reset()
    if attribute isnt 'default'
      window.styler[region].show if attribute is 'uniform'
        new uniformView
          attribute: selector
          selector: selector
      else
        new attributedView
          model: (window.schema.find (k) -> k.attributes.name is attribute)
          selector: selector
    else
      window.styler[region].close()

  AttributeStylerView = Backbone.Marionette.CompositeView.extend
    template: "#tpl-attribute-styler"
    itemView: AttributeStylerItemView
    collection: window.schema
    itemViewContainer: "tbody"
    tagName: "table"
    className: "table table-striped table-hover"

    events:
      'change input[name=labels]': showView("labelStyler", "labels", null, LabelStylerView)
      'change input[name=line-color]': showView("lineColorStyler", "line-color", StdPaletteView, ColorStylePickerView)
      'change input[name=polygon-fill]': showView("polygonColorStyler", "polygon-fill", StdPaletteView, ColorStylePickerView)
      'change input[name=line-opacity]': showView("lineOpacityStyler", "line-opacity", UniformOpacityView, OpacityPickerView)
      'change input[name=polygon-opacity]': showView("polygonOpacityStyler", "polygon-opacity", UniformOpacityView, OpacityPickerView)
      'change input[name=point-size]': showView("pointSizeStyler", "point-size", UniformPointSizeView, PointSizePickerView)

  # @attr-report
  #
  # Code to render the attribute value report at the top of the page
  ######################################################################################################################

  # view to allow a user to see a report on the characteristics of the attributes in a file
  AttributeCharacteristicsItemView = Backbone.Marionette.ItemView.extend
    template: "#tpl-attribute-characteristics"
    tagName: 'tr'
  AttributeReportView = Backbone.Marionette.CompositeView.extend
    template: "#tpl-attribute-report"
    itemView: AttributeCharacteristicsItemView
    collection: window.schema
    itemViewContainer: "tbody"
    tagName: "table"
    className: "table table-striped"

  # @app
  #
  # The application itself
  ######################################################################################################################

  window.styler = new Backbone.Marionette.Application

  window.styler.addInitializer (options) ->
    window.styler.addRegions
      attributeReport: "#attribute-report"
      attributeStyler: "#attribute-styler"
      lineOpacityStyler: "#line-opacity-styler"
      polygonOpacityStyler: "#polygon-opacity-styler"
      lineColorStyler: "#line-color-styler"
      polygonColorStyler: "#polygon-fill-styler"
      pointSizeStyler: "#point-size-styler"
      labelStyler: "#label-styler"

    window.styler.attributeReport.show new AttributeReportView
    window.styler.attributeStyler.show new AttributeStylerView

    $("#save-style").on 'click', ->
      value = JSON.stringify window.finishedStyle.toJSON()
      $.ajax
        url: '/ga_resources/save_style/'
        type: 'POST'
        data:
          stylesheet: value
          existing_or_new: $("#user-inputs input[name=layer-type]").val()
          existing_layer_name: $("#user-inputs select[name=existing-layers]").val()
          new_layer_name: $('#new-layer-name').val()
          style_name: $('#style-name').val()
          resource: $('#resource').val()

        success: (data) ->
          window.location = data.url

        error: (data) ->
          alert "an error occurred"


  window.styler.start()
