"""Parse SLD and make stylesheets from it"""
import re
import math
from datetime import datetime
import numpy as np
import colorsys

SLD_NS = '{http://www.opengis.net/sld}'

def _parseHexColor(value):
    red = 0.0
    green = 0.0
    blue = 0.0
    alpha = 1.0
    if len(value) == 3:
        red = green = blue = int(value[1:3], 16) / 255.0
    elif len(value) >= 7:
        red = int(value[1:3],16) / 255.0
        green = int(value[3:5], 16) / 255.0
        blue = int(value[5:7], 16) / 255.0
    if len(value) == 9:
        alpha = int(value[7:9], 16) / 255.0

    return np.array((red,green,blue,alpha), dtype=np.float32)

def _isHexColor(value):
    return (len(value) == 7 or len(value) == 9) and value.startswith('#')


class Rule(object):
    """Represents an SLD rule"""
    def __init__(self):
        self.min_scale = None
        self.max_scale = None
        self.clauses = []
        self.point_symbolizer = None
        self.polygon_symbolizer = None
        self.raster_symbolizer = None
        self.line_symbolizer = None
        self.text_symbolizer = None

    def __call__(self, data, pxsize):
        if (not self.min_scale or pxsize > self.min_scale) and (not self.max_scale or pxsize < self.max_scale):
            return self.test(data)

    def test(self, data):
        return all(clause(data) for clause in self.clauses)

######### data accessors and literals ####################

class PA(object):
    """Represents a property accessor"""
    @classmethod
    def parse_as_operator(cls, property):
        return cls(property.text)

    @classmethod
    def parse_as_function(cls, property):
        return cls(property.text)

    def __init__(self, field):
        self.field = field

    def call(self, data):
        k = data[self.field]
        k = float(k) if isinstance(k, int) else k
        k = _parseHexColor(k) if _isHexColor(k) else k
        return k

class L(object):
    """Represents a literal"""

    @classmethod
    def parse_as_operator(cls, literal):
        return cls(literal.text)

    @classmethod
    def parse_as_function(cls, literal):
        return cls(literal.text)

    def __init__(self, value):
        try:
            self.value = float(value)
        except:
            self.value = value
        self.value = _parseHexColor(value) if _isHexColor(value) else value

    def __call__(self, data):
        return self.value


DATA_ACCESSORS = {
    SLD_NS + "Literal" : L,
    SLD_NS + "Property" : PA,
    SLD_NS + "PropertyName" : PA,
}

######### comparison operators ##########################

class Gt(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) > self.e2(data)

class Ge(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) >= self.e2(data)

class Lt(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) < self.e2(data)

class Le(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) <= self.e2(data)

class Ne(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) != self.e2(data)

class Eq(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data) == self.e2(data)

class Null(object):
    def __init__(self, e1):
        self.e1 = e1

    def __call__(self, data):
        return self.e1(data) is None

class Btw(object):
    def __init__(self, e, l, r):
        self.e = e
        self.l = l
        self.r = r

    def __call__(self, data):
        v = self.e(data)
        return v <= self.r(data) and v >= self.e(data)

class Like(object):
    def __init__(self, e, value):
        self.e = e
        self.value = value

    def __call__(self, data):
        v = self.e(data)
        if self.value.startswith('%') and self.value.endswith('%'):
            return self.value in v
        elif self.value.startswith('%'):
            return v.endswith(self.value)
        elif self.value.endswith('%'):
            return v.startswith(self.value)
        else:
            return re.match(self.value, v)

class In(object):
    def __init__(self, e, *args):
        self.e = e
        self.values = args

    def __call__(self, data):
        v = self.e(data)
        values = set(x(data) for x in self.values)
        return v in values

class NotIn(object):
    def __init__(self, e, *args):
        self.e = e
        self.values = args

    def __call__(self, data):
        v = self.e(data)
        values = set(x(data) for x in self.values)
        return v not in values

COMPARISON_OPERATORS = {
    SLD_NS + "PropertyIsGreaterThan" : Gt,
    SLD_NS + "PropertyIsGreaterThanOrEqualTo" : Ge,
    SLD_NS + "PropertyIsLessThan" : Lt,
    SLD_NS + "PropertyIsLessThanOrEqualTo" : Le,
    SLD_NS + "PropertyIsEqualTo" : Eq,
    SLD_NS + "PropertyIsNotEqualTo" : Ne,
    SLD_NS + "PropertyIsNull" : Null,
    SLD_NS + "PropertyIsBetween" : Btw,
    SLD_NS + "PropertyIsLike" : Like,
}

######### Control flow operators ##############################

class IfThenElse(object):
    def __init__(self, c, t, f):
        self.c = c
        self.t = t
        self.f = f

    def __call__(self, data):
        return self.t(data) if self.c(data) else self.f(data)

######### Logical operators ##################################

class And(object):
    def __init__(self, *es):
        self.es = es

    def __call__(self, data):
        return all(e(data) for e in self.es)

class Or(object):
    def __init__(self, *es):
        self.es = es

    def __call__(self, data):
        return any(e(data) for e in self.es)

class Not(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return not self.e(data)


CONJUNCTION_OPERATORS = {
    SLD_NS + "And" : And,
    SLD_NS + "Or" : Or,
    SLD_NS + "Not" : Not,
    }


####### Math functions  #######################################

class Add(object):
    def __init__(self, exp1, exp2, *args):
        self.exp1 = exp1
        self.exp2 = exp2
        self.rest = args

    def __call__(self, data):
        reduce(float.__add__, (exp(data) for exp in self.rest), self.exp1(data) + self.exp2(data))

class Subtract(object):
    def __init__(self, exp1, exp2, *args):
        self.exp1 = exp1
        self.exp2 = exp2
        self.rest = args

    def __call__(self, data):
        reduce(float.__sub__, (exp(data) for exp in self.rest), self.exp1(data) - self.exp2(data))

class Multiply(object):
    def __init__(self, exp1, exp2, *args):
        self.exp1 = exp1
        self.exp2 = exp2
        self.rest = args

    def __call__(self, data):
        reduce(float.__mul__, (exp(data) for exp in self.rest), self.exp1(data) * self.exp2(data))

class Divide(object):
    def __init__(self, exp1, exp2, *args):
        self.exp1 = exp1
        self.exp2 = exp2
        self.rest = args

    def __call__(self, data):
        reduce(float.__div__, (exp(data) for exp in self.rest), self.exp1(data) / self.exp2(data))

class Abs(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return abs(self.e(data))

class Sin(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.sin(self.e(data))


class Sin(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.sin(self.e(data))

class Cos(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.cos(self.e(data))

class Tan(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.sin(self.e(data))

class Asin(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.asin(self.e(data))

class Acos(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.acos(self.e(data))

class Atan(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.atan(self.e(data))

class Ceil(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.ceil(self.e(data))

class Floor(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.floor(self.e(data))

class Round(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return round(self.e(data))

class Log10(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.log10(self.e(data))

class Ln(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.log(self.e(data))

class Exp(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.exp(self.e(data))

class Deg(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.degrees(self.e(data))

class Rad(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.radians(self.e(data))

class Sqrt(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return math.sqrt(self.e(data))

class Pow(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return math.pow(self.e1(data), self.e2(data))

class Atan2(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return math.atan2(self.e1(data), self.e2(data))

MATH_FUNCTIONS = {
    SLD_NS + "abs" : Abs,
    SLD_NS + "acos" : Acos,
    SLD_NS + "atan" : Atan,
    SLD_NS + "asin" : Asin,
    SLD_NS + "sin" : Sin,
    SLD_NS + "cos" : Cos,
    SLD_NS + "tan" : Tan,
    SLD_NS + "atan2" : Atan2,
    SLD_NS + "ceil" : Ceil,
    SLD_NS + "floor" : Floor,
    SLD_NS + "round" : Round,
    SLD_NS + "log" : Ln,
    SLD_NS + "log10" : Log10,
    SLD_NS + "rint" : Round,
    SLD_NS + "toDegrees" : Deg,
    SLD_NS + "toRadians" : Rad,
}

########## String functions #######################################

class Concat(object):
    def __init__(self, e1, e2, *es):
        self.e1 = e1
        self.e2 = e2
        self.es = es

    def __call__(self, data):
        return reduce(str.__add__, (e(data) for e in self.es), self.e1(data) + self.e2(data))

class Capitalize(object):
    def __init__(self, e):
        self.e =e

    def __call__(self, data):
        return self.e(data).title()

class Trim(object):
    def __init__(self, e):
        self.e =e

    def __call__(self, data):
        return self.e(data).strip()

class IndexOf(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data).index(self.e2(data))

class LastIndexOf(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data).rindex(self.e2(data))

class Substring(object):
    def __init__(self, e, start, end):
        self.e = e
        self.start = start
        self.end = end

    def __call__(self, data):
        return self.e(data)[ self.start(data) : self.end(data) ]

class SubstringStart(object):
    def __init__(self, e, start):
        self.e = e
        self.start = start

    def __call__(self, data):
        return self.e(data)[ self.start(data) : ]

class Upper(object):
    def __init__(self, e):
        self.e =e

    def __call__(self, data):
        return self.e(data).upper()

class Lower(object):
    def __init__(self, e):
        self.e =e

    def __call__(self, data):
        return self.e(data).lower()

class StringLength(object):
    def __init__(self, e):
        self.e =e

    def __call__(self, data):
        return len(self.e(data))

class EndsWith(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data).endswith(self.e2(data))

class EqualsIgnoreCase(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return self.e1(data).lower() == self.e2(data).lower()

class Matches(object):
    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __call__(self, data):
        return re.match(self.e2(data), self.e1(data))


STRING_FUNCTIONS = {
    "concatenate" : Concat,
    "capitalize" : Capitalize,
    "trim" : Trim,
    "indexOf" : IndexOf,
    "lastIndexOf" : LastIndexOf,
    "substring" : Substring,
    "substringStart" : SubstringStart,
    "upper" : Upper,
    "lower" : Lower,
    "stringLength" : StringLength,
    "endsWith" : EndsWith,
    "equalsIgnoreCase" : EqualsIgnoreCase,
    "matches" : Matches,
}

########### Parsing and data format functions ##########################################################################

class DateFormat(object):
    def __init__(self, e, fmt):
        self.e = e
        self.fmt = fmt

    def __call__(self, data):
        return self.e(data).strftime(self.fmt)

class DateParse(object):
    def __init__(self, e, fmt):
        self.e= e
        self.fmt = fmt

    def __call__(self, data):
        return datetime.strptime(self.e(data), self.fmt)

class NumberFormat(object):
    def __init__(self, e, fmt):
        self.e = e
        self.fmt = fmt

    def __call__(self, data):
        return self.fmt % (self.e(data), )

class ParseBoolean(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return bool(self.e(data))


class ParseInt(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return int(self.e(data))


class ParseFloat(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return float(self.e(data))


class ParseLong(object):
    def __init__(self, e):
        self.e = e

    def __call__(self, data):
        return long(self.e(data))

PARSING_FUNCTIONS = {
    "dateFormat" : DateFormat,
    "dateParse" : DateParse,
    "numberFormat" : NumberFormat,
    "parseBoolean" : ParseBoolean,
    "parseInt" : ParseInt,
    "parseFloat" : ParseFloat,
    "parseLong" : ParseLong,
}

############# Data transformation functions ############################################################################

class PropertyExists(object):
    def __init__(self, prop):
        self.prop = prop

    def __call__(self, data):
        return self.prop in data


class Recode(object):
    def __init__(self, e, default, **kwargs):
        self.e = e
        self.default = default
        self.code = kwargs

    def __call__(self, data):
        v = self.e(data)
        return self.code[v] if v in self.code else self.default

class Categorize(object):
    def __init__(self, e, *args):
        self.e = e
        self.pairs = args

    def __call__(self, data):
        v = self.e(data)
        for value, threshold in self.pairs:
            if threshold is None:
                return value
            elif v >= threshold:
                return value

class Interpolate(object):
    LINEAR = 'linear'
    CUBIC = 'cubic'
    COSINE = "cosine"

    NUMERIC = 'numeric'
    COLOR = "color"

    def __init__(self, e, mode=NUMERIC, method=LINEAR, default=None, *args):
        self.e = e
        self.method=method
        self.mode = mode
        self.pairs = args

    def __call__(self, data): # TODO support color, support cubic spline interpolation
        v = self.e(data)
        for i, (value, threshold) in enumerate(self.pairs):
            if threshold is None:
                return value
            elif v >= threshold:
                xmin = threshold
                xmax = self.pairs[i+1][1]
                xspn = xmax-xmin
                y = (v-xmin)/xspn

                if self.method == Interpolate.CUBIC:
                    pass
                elif self.method == Interpolate.COSINE:
                    y = math.cos(math.pi*y)

                if self.mode == Interpolate.NUMERIC:
                    return y*value + (1-y)*self.pairs[i+1][0]
                elif self.mode == Interpolate.COLOR:
                    lc = np.array(colorsys.rgb_to_hls(*value[0:3]/255.0), dtype=np.float32)
                    rc = np.array(colorsys.rgb_to_hls(*self.pairs[i+1][0][0:3]/255.0), dtype=np.float32)
                    fc = y*lc + (1-y)*rc
                    return tuple(fc)
                else:
                    raise NotImplementedError()



FUNCTIONS = {
    SLD_NS + "between" : Btw,
    SLD_NS + "equalTo" : Eq,
    SLD_NS + "greaterEqualThan" : Ge,
    SLD_NS + "greaterThan" : Gt,
    SLD_NS + "in" : In,
    SLD_NS + "notIn" : NotIn,
    SLD_NS + "isLike" : Like,
    SLD_NS + "isNull" : Null,
    SLD_NS + "lessThan" : Lt,
    SLD_NS + "lessEqualThan" : Le,
    SLD_NS + "not" : Not,
    SLD_NS + "notEqual" : Ne,

    SLD_NS + "if_then_else" : IfThenElse,

    SLD_NS + "propertyExists" : PropertyExists,
    SLD_NS + "property" : PA,


    SLD_NS + "interpolate" : Interpolate,
    SLD_NS + "categorize" : Categorize,
    SLD_NS + "recode" : Recode,
}

from lxml import etree
from cStringIO import StringIO

TEST_SLD="""<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>medford:library</Name>
    <UserStyle>
      <Title>Medford, OR - Library</Title>
      <Abstract>Point style with external graphic for Medford city libraries</Abstract>

      <FeatureTypeStyle>
<!--140K-70K-->
        <Rule>
          <Name>Library</Name>
          <Title>Library 140K-70K</Title>

          <MinScaleDenominator> 70000 </MinScaleDenominator>
          <MaxScaleDenominator> 140000 </MaxScaleDenominator>

          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"
                  xlink:href="graphics/library.svg"/>
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Mark/>
              <Size>10</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>

 <!--70-35K-->
        <Rule>
         <Name>Library</Name>
         <Title>Library 70K-25K</Title>

         <MinScaleDenominator> 35000 </MinScaleDenominator>
         <MaxScaleDenominator> 70000 </MaxScaleDenominator>

         <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"
                 xlink:href="graphics/library.svg"/>
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Mark/>
              <Size>13</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>

<!--35K-17.5-->
        <Rule>
          <Name>Library</Name>
          <Title>Library 35K-17.5</Title>

          <MinScaleDenominator> 17500 </MinScaleDenominator>
          <MaxScaleDenominator> 35000 </MaxScaleDenominator>

          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"
                xlink:href="graphics/library.svg"/>
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Mark/>
              <Size>16</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>

<!--< 17.5-->
        <Rule>
          <Name>library</Name>
          <Title>library &lt; 17.5</Title>

          <MaxScaleDenominator> 17500 </MaxScaleDenominator>

          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"
                  xlink:href="graphics/library.svg"/>
                <Format>image/svg</Format>
              </ExternalGraphic>
              <Mark/>
              <Size>20</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>

      </FeatureTypeStyle>

    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""

class SLDParser(object):

    def __init__(self, stylesheet=None):
        self.stylesheet=stylesheet

    def __call__(self, sld):
        parser = etree.XMLParser(ns_clean=True)
        xml = etree.fromstring(StringIO(sld), parser)
        self.parse_FeatureTypeStyle(xml)

    def parse_StyledLayerDescriptor(self, styled_layer_descriptor):
        for child in styled_layer_descriptor.iterchildren():
            if child.tag.endswith('}NamedLayer'):
                self.parse_NamedLayer(child)

    def parse_NamedLayer(self, named_layer):
        for child in named_layer.iterchildren():
            if child.tag.endswith('}UserStyle'):
                self.parse_UserStyle(child)

    def parse_UserStyle(self, user_style):
        for child in user_style.iterchildren():
            if child.tag.endswith('}FeatureTypeStyle'):
                self.parse_FeatureTypeStyle(child)

    def parse_FeatureTypeStyle(self, feature_type_style):
        for child in feature_type_style.iterchildren():
            if child.tag.endswith('}Rule'):
                self.parse_Rule(child)

    def parse_Rule(self, rule):
        working_rule = Rule()
        for child in rule.iterchildren():
            if child.tag.endswith('}PointSymbolizer'):
                self.parse_PointSymbolizer(working_rule, child)
            elif child.tag.endswith('}PolygonSymbolizer'):
                self.parse_PolygonSymbolizer(working_rule, child)
            elif child.tag.endswith('}LineSymbolizer'):
                self.parse_LineSymbolizer(working_rule, child)
            elif child.tag.endswith('}RasterSymbolizer'):
                self.parse_RasterSymbolizer(working_rule, child)
            elif child.tag.endswith('}TextSymbolizer'):
                self.parse_TextSymbolizer(working_rule, child)
            elif child.tag.endswith('}MaxScaleDenominator'):
                pass
            elif child.tag.endswith('}MinScaleDenominator'):
                pass
            elif child.tag.endswith('}Filter'):
                self.parse_Filter(working_rule, child)

    def parse_Filter(self, working_rule, filter):
        pass

    def parse_PointSymbolizer(self, working_rule, point_symbolizer):
        pass

    def parse_LineSymbolizer(self, working_rule, line_symbolizer):
        pass

    def parse_PolygonSymbolizer(self, working_rule, polygon_symbolizer):
        pass

    def parse_TextSymbolizer(self,working_rule,  text_symbolizer):
        pass

    def parse_RasterSymbolizer(self,working_rule,  raster_symbolizer):
        pass

    def parse_FilterFunction(self,working_rule,  filter_function):
        pass

    def parse_Function(self, working_rule, function):
        pass



