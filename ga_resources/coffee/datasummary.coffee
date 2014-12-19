window.Field = Backbone.Model.extend
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
  isCategorical: ->
    "categorical" in this.attributes.tags

# whether or not most of the values of this field are null
  isMostlyNull: ->
    "mostly null" in this.attributes.tags

# whether or not this field contains a distribution of numbers
  isContinuous: ->
    "open ended" in this.attributes.tags

# whether or not this field contains mostly unique values
  isUnique: ->
    "unique" in this.attributes.tags

# whether or not this field is mostly full of null values
  isRarelyNull: ->
    "not null" in this.attributes.tags

# whether or not this field is usually boolean
  isBoolean: ->
    "boolean" in this.attributes.tags

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
      step = (max - min) / classes
      (y for y in [min..max] by step)
    else if this.isCategorical()
      k = Math.round (this.attributes.uniques.length / classes)
      (this.attributes.uniques[i] for i in [0..this.attributes.uniques.length] by k)
    else []


window.Schema = Backbone.Collection.extend
  model: Field

# @attr-report
#
# Code to render the attribute value report at the top of the page
######################################################################################################################

# view to allow a user to see a report on the characteristics of the attributes in a file
window.AttributeCharacteristicsItemView = Backbone.Marionette.ItemView.extend
  template: "#tpl-attribute-characteristics"
  tagName: 'tr'
window.AttributeReportView = Backbone.Marionette.CompositeView.extend
  template: "#tpl-attribute-report"
  itemView: AttributeCharacteristicsItemView
  collection: window.schema
  itemViewContainer: "tbody"
  tagName: "table"
  className: "table table-striped"


# mockup data for now
window.schema = new Schema window.attributes
