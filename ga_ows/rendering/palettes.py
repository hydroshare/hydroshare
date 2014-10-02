"""
Color paletting for numpy arrays.  This is more flexible than matplotlib's
color palettes, although we may eventually move to them and force
pre-computation of array inputs to matplotlib.  Depends on performance
concerns.

"""
import numpy as np
import colorsys
import logging

log = logging.getLogger(__name__)

def rgba(r=0, g=0, b=0, a=255):
    """
    A function that returns a color for integral rgba values between 0 and 255
    
    :param r: default 0.
    :type r: Integer 0-255.
    :param g: default 0.
    :type g: Integer 0-255.
    :param b: default 0.
    :type b: Integer 0-255.
    :param a: default 0.
    :type a: Integer 0-255.


    """
    return np.array((r, g, b, a), dtype=np.uint8)

def rgba1(r=0, g=0, b=0, a=1):
    """
    A function that returns a color for floating point values between 0.0 and 1.0

    :param r: default 0.0
    :type r: Float 0.0-1.0
    :param g: default 0.0
    :type g: Float 0.0-1.0
    :param b: default 0.0
    :type b: Float 0.0-1.0
    :param a: default 0.0
    :type a: Float 0.0-1.0
    """
    return np.array((r*255, g*255, b*255, a*255), dtype=np.uint8)

def rgbahex(color):
    """A function that returns a color for a hex integer"""
    return np.array((color,), dtype=np.uint32).view(dtype=np.uint8)


class NullColorEntry(object):
    """
    A palette entry that matches the null value.  Supports "in" syntax. All palette entries are callables and are generally used thusly::

        bin = NullColorEntry(rgba(0,0,0,0))

        for v in ...:
            if v in bin:
                output.append(bin(v))

    """
     
    def __init__(self, color):
        self.color = color

    def __contains__(self, value):
        return value is None

    def __call__(self, v):
        return self.color

class CatchAll(object):
    """A palette entry that matches any value"""
     
    def __init__(self, color):
        self.color = color

    def __contains__(self, value):
        return True

    def __call__(self, v):
        return self.color.view(np.uint32)[0]

class ColorBin(object):
    """
    A palette entry that presents a uniform color entry for any value between
    bounds. By default it is unbounded on either end.  To change this
    behaviour, specify "left_value" or "right_value" parameters to bound the
    bin on one side.  Additionally, by default bounding values are included as
    part of the bin.  To change this behaviour, include_right and include_left
    can be set to false in the constructor.  

    """

    def __init__(self, color, left_value=float('-Inf'), right_value=float("Inf"), include_left=True, include_right=True):
        self.l = left_value
        self.r = right_value
        self.color = color.view(np.uint32)[0]
        self.include_right = include_right
        self.include_left = include_left

    def __contains__(self, value):
        return ((value > self.l) or (value == self.l and self.include_left)) and ((value < self.r) or (value == self.r and self.include_right))

    def __call__(self, v):
        return self.color

class LinearGradient(object):
    """
    A gradient palette entry between two floating point numbers.  This works
    more or less the same way as ColorBin, except that the palette slides
    between the colors at the endpoints for intermediate values.  There is one
    additional parameter, "stops" which is the number of stops between the
    values.  The default for this is 32, which represents 32 levels of
    gradation between the endpoints.  Colors are blended using HSL blending, so
    changing hues is safe.
    """

    def __init__(self, left_color, right_color, left_value, right_value, include_left=True, include_right=True, stops=32):
        self.l = left_value
        self.r = right_value
        self.lc = np.array(colorsys.rgb_to_hls(*left_color[0:3]/255.0) + (left_color[3]/255.0,), dtype=np.float32)
        self.rc = np.array(colorsys.rgb_to_hls(*right_color[0:3]/255.0) + (right_color[3]/255.0,), dtype=np.float32)
        self.include_right = include_right
        self.include_left = include_left
        self.stops = stops
        self.delta = self.stops / (self.r-self.l)

        self.colors = np.zeros((stops,4), dtype=np.uint8)
        for stop in range(stops):
            k = float(stop)/stops
            h,l,s,a = (k*self.rc + (1-k)*self.lc)
            r,g,b = colorsys.hls_to_rgb(h,l,s)
            self.colors[stop] = 255*np.array((r,g,b,a), dtype=np.float32)
        self.colors = self.colors.view(dtype=np.uint32)

    def __contains__(self, value):
        return ((value > self.l) or (value == self.l and self.include_left)) and ((value < self.r) or (value == self.r and self.include_right))

    def __call__(self, va):
        iv = int((va-self.l) * self.delta)
        return self.colors[iv,0]

class Choices(object):
    """
    A stepped palette among logical choices, with the possibility of an "out of band" choice for None values.  
    """

    def __init__(self, choices, colors, null_color=None):
        self.choices = dict(zip(choices,colors))
        self.null_color = null_color

    def __contains__(self, value):
        return value in self.choices

    def __call__(self, value):
        return self.choices(value)

class Lambda(object):
    """An imputed gradient that maps from a function of keyword args to a null, 0.0 - 1.0 value"""

    def __init__(self, fn, left_color, right_color, null_color=None, stops=32):
        self.fn = fn
        self.left_color = left_color
        self.right_color = right_color
        self.null_color = null_color
        self.lc = np.array(colorsys.rgb_to_hls(*left_color[0:3]/255.0) + (left_color[3]/255.0,), dtype=np.float32)
        self.rc = np.array(colorsys.rgb_to_hls(*right_color[0:3]/255.0) + (right_color[3]/255.0,), dtype=np.float32)
        self.stops = stops

    def __contains__(self, value):
        v = self.fn(value)
        return v is not None and v >= 0.0 and v <= 1.0

    def __call__(self, value):
        if self.null_color and value is None:
            return self.null_color
        else:
            a = int(self.stops*self.fn(value))
            return self.colors[a]

# a callable function that can be vectorized to operate on a single array
class _Palette(object):
    def __init__(self, *bands):
        self.bands = bands

    def __call__(self, value):
        for band in self.bands:
            if value in band:
                return band(value)
        return 0

# a callable function that can be vectoried to operate on a number or arrays
class _LambdaPalette(object):
    def __init__(self, *bands):
        self.bands = bands

    def __call__(self, *value):
        for band in self.bands:
            if value in band:
                return band(*value)
        return 0

class Palette(object):
    """
    A Palette is used in geoanalytics to take a value raster and turn it into a
    color raster::
    
        p = Palette(
            ColorBin(rgba(0,0,0), 0.0, 30.0),
            ColorBin(rgba(255,0,0), 30.0, 60.0),
            ColorBin(rgba(0,255,0), 60.0, 90.0),
            ColorBin(rgba(0,0,255), 90.0, 120.0),
            CatchAll(rgba(255,255,255,0))
        )

        ds = gdal.Open('foo.bin')
        scipy.imsave('foo.png', p(ds.ReadAsArray()))

    Palettes can contain objects of type ColorBin, LinearGradient, CatchAll,
    Choices, and NullColorEntry.  Palettes can also take Lambda objects so long
    as the functions only expect one parameter.  A CatchAll, if provided,
    should always be the last object.
    """

    def __init__(self, *palette):
        """A behaviour that takes a single array and a palette and transfers to a colored array"""
        self.palette = np.vectorize(_Palette(*palette), otypes=[np.uint32])

    def __call__(self, value):
        p = self.palette(value)
        shape = value.shape + (4,)
        return p.view(dtype=np.uint8).reshape(*shape)

            
class MultiKeyPalette(object):
    """
    A MultiKeyPalette is used in geoanalytics to take a series of layers and
    turn them into a single color raster::

        def freezing_precip(qpf, temp):
            if temp <= 32 and qpf > 0:
                return 0.5
            else:
                return None

        def liquid_precip(qpf, temp):
            if temp > 32 and qpf > 0:
                return 0.5
            else:
                return None

        def catch_all(**_0):
            return 0.5

        p = MultiKeyPalette(('qpf','temp')
            Lambda(rgba(0,0,255), freezing_precip),
            Lambda(rgba(0,255,0), liquid_precip),
            Lambda(rgba(0,0,0,0), catch_all)
        )

        # use the palette 
        temp = gdal.Open('ds.temp.bin')
        qpf = gdal.Open('ds.qpf.bin')
        scipy.imsave('foo.png', p(temp=temp.ReadAsArray(), qpf=qpf.ReadAsArray()))

    MultiKeyPalettes can contain only objects of type Lambda.  These can take
    either arbitrary keyword arguments or can take specific ones.
    """

    def __init__(self, ordering, *palette):
        """A behaviour that takes a dictionary of arrays and a lambda palette"""
        self.palette = np.vectorize(_LambdaPalette(palette), otypes=[np.uint32])
    
    def __call__(self, **value):
        self.palette(*[value[v] for v in self.ordering]).view(dtype=np.uint8).reshape(value.values()[0].shape[0], value[0].values()[0].shape[1], 4)

class LayeredColorTransfer(object):
    """
    TODO currently unimplemented.  This will work as a sort of hybrid between
    MultiKeyPalette and Palette::

        p = LayeredColorTransfer(('landuse', 'dem')
            landuse = (LayeredColorTransfer.NORMAL,  # bottom layer
                (ColorBin(...), 
                LinearGradient(...),
                LinearGradient(...))),
            dem = (LayeredColorTransfer.VALUE, 
                (LinearGradient(...),))
        )
        
        landuse = gdal.Open('landuse.tiff')
        dem = gdal.Open('land-topographically-shaded.tiff')
        scipy.misc.imsave('shaded-land.tiff', p(landuse=landuse, dem=dem))

    For more information on what the color transfer modes named here do, see
    Photoshop or Gimp documentation.
    """

    NORMAL = -1
    """Translucent replace layering mode"""

    ADD = 0
    """Add layering mode"""

    SUBTRACT = 1
    """Difference layering mode"""

    DODGE = 2
    """Dodge layering mode"""

    BURN = 3
    """Burn layering mode"""

    MULTIPLY = 4
    """Multiply layering mode"""

    SOFT_LIGHT = 5
    """Soft light layering mode"""

    HARD_LIGHT = 6 
    """Hard light layering mode"""

    OVERLAY = 7
    """Overlay layering mode"""

    SCREEN = 8
    """Screen layering mode"""

    COLOR = 9
    """Color layering mode"""

    VALUE = 10
    """Value layering mode"""

    HUE = 11
    """Hue layering mode"""

    SATURATION = 12
    """Saturation layering mode"""

    def __init__(self, ordering, **palette):
        pass
