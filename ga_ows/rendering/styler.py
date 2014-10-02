import numpy as np

def _parseHexColor(self, value):
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



class Stylesheet(object):
    """A symbolizer for features.

    The constructor creates a new stylesheet.  Any of the properties available in the stylesheet can
    be set by passing its name as a keyword parameter along with a constant, a callable, or a dictionary of
    ``{ 'val' : val, 'fun' : fun }`` to the constructor.
    
    In general, methods can be sent a "val" parameter, a "fun" parameter, or both.
    If the method has a val parameter, then this value is passed directly to the rasterizer.
    If the method has a fun parameter, then the function is called with the record (a dict 
    object) and the result is passed to the rasterizer.  If both are passed, then a value 
    lookup is performed on the data record and the result of the lookup is passed to the
    function as the first argument, and the result of that is passed to the rasterizer.

    If a function is specified, the second argument will always be the number of horizontal units in the target coordinate
    system that a pixel takes up::

        def county_label(data, pxlsz):
            if pxlsz > 0.1:
                return None
            else:
                return data.name10

        def stroke_width(_, pxlsz):
            k = 1./pxlsz
            if k > 1:
                return 1
            elif k < 0.3:
                return 0.3
            else:
                return k

        sheet = styler.Stylesheet(
            label = county_label,
            label_color = (0.,0.,0.,1.),
            font_face = 'Helvetica',
            label_halo_size = 1.,
            label_halo_color = (1.,1.,0.7,0.7),
            label_align = 'center',
            label_offsets = (0, 5),
            stroke_color = (31./255, 120./255, 180./255, 1.0),
            stroke_width = stroke_width,
            fill_color = (166./255, 206./255, 227./255, 1.0)
        )

    The following properties are defined.  Any or all of these can be absolute values that are constant or can be returned
    from functions that accept the data instance and a pixel-size.

        * stroke_width : **float**. pixel width of line segments and outlines.
        * stroke_color : four-tuples normalized to 1.0 r,g,b, and a channels
        * stroke_dash : see `http://www.cairographics.org`_ for more information on how to specify a dash pattern
        * stroke_cap : **string**. butt, round, or square
        * stroke_join : **string**. bevel, round, or miter
        * fill_color : same as stroke color.
        * fill_pattern : the absolute path to a PNG file to use as a fill pattern
        * label : **string**. the label text for a particular geometry.
        * font_family : **string**. The font family. See your system for more details.
        * font_weight : normal or bold
        * font_slant : **string** normal or italic
        * font_size : **float** the font size in pixels
        * font_options : other Cairo specific font options.
        * label_halo_size : the width of the halo around a label
        * label_halo_color : the color of the halo around a label.
        * label_color : the color of the label text.
        * point_size : the size in pixels of a point.
        * point_shape : **string**. circle, square, diamond, cross, x, triangle, star.
        * point_icon : the absolute path to a png file to use as a fill pattern.
        * compositing_operator : **string**. **powerful** when used in the context of multiple layers.
          Can change the way pixels are rendered on top of others.  See Cairo's documentation for more details.
          Possibilties are:
                add, atop, clear, dest, dest atop, dest in, dest out, dest over, in, out, over, saturate, source, and xor

        Also, stylesheets can inherit by passing a 'parent' or 'parents' parameter' to the constructor with other stylesheet instances

    """

    FeatureProperties = frozenset([
        'stroke_width', 'stroke_color', 'stroke_dash', 'stroke_cap', 'stroke_join',
        'fill_color','fill_pattern',
        'point_size','point_shape','point_icon',
        'compositing_operator', 'lod'
    ])

    LabelProperties = frozenset([
        'label','label_color','font_face','font_weight','font_slant','font_size','font_options','font_align',
        'label_halo_size','label_halo_color','label_align', 'label_offsets'
    ])

    def _condprop(self, p, data, pxlsz, callback=None):
        ret = None
        if p in self._props:
            if 'fun' in  self._props[p] and self._props[p]['fun'] is not None:
                if 'val' in self._props[p] and self._props[p]['val'] is not None:
                    ret = self._props[p]['fun'](data[ self._props[p]['val'] ], pxlsz)
                else:
                    ret = self._props[p]['fun'](data, pxlsz)
            else:
                ret = self._props[p]['val']

        if ret and callback:
            return callback(ret)
        else:
            return ret

    @classmethod
    def from_module(cls, modname):
        """allow a python module to be used as a stylesheet. scans the module
        for useful properties and adds them to the sheet
        
        """
        m = __import__(modname)
        d = dict(filter(lambda x: not x[0].startswith('__'), m.__dict__.items()))
        ss = cls(**d)
        return ss


    def __init__(self, name=None, required_fields=tuple(), **options):
        """"""

        self.required_fields = required_fields
        self.name = name

        self._props = {
            'stroke_width' : { 'val' : 1.0 },
            'stroke_color' : { 'val' : (0.0,0.0,0.0,1.0) },
            'fill_color' : { 'val' : (1.0,1.0,0.0,0.5) },
            'compositing_operator' : { 'val' : 'over' },
        }

        if 'parent' in options:
            for key, item in options['parent']._props:
                self._props[key] = item

        if 'parents' in options:
            for parent in options['parents']:
                for key, item in parent._props:
                    self._props[key] = item


        for option, value in options.items():
            if type(value) is dict:
                self._props[option] = value
            elif callable(value):
                self._props[option] = { 'fun' : value }
            else:
                self._props[option] = { 'val' : value }

    ### Styling methods

    def styles(self, data, pxlsz):
        """Get all the styles for a particular piece of data.  This is a mostly internal method used by a RenderingContext"""
        return frozenset([(p, self._condprop(p, data, pxlsz)) for p in Stylesheet.FeatureProperties])

    def label(self, data, pxlsz):
        """Labels are handled a little bit special.  This is a mostly internal method used by the RenderingContext"""
        if 'label' in self._props:
            if 'fun' in self._props['label']:
                if 'val' in self._props['label']:
                    return (self._props['label']['fun'](data[self.label['val']]), frozenset([(p, self._condprop(p, data, pxlsz)) for p in Stylesheet.LabelProperties]))
                else:
                    return (self._props['label']['fun'](data, pxlsz), frozenset([(p, self._condprop(p, data, pxlsz)) for p in Stylesheet.LabelProperties]))
            elif 'val' in self._props['label']:
                if self._props['label']['val'] in data:
                    return (data['val'], frozenset([(p, self._condprop(p, data, pxlsz)) for p in Stylesheet.LabelProperties]))
                else:
                    return None, None
            else:
                return None, None
        else:
            return None, None

    def s(self, prop, value=None, fun=None):
        """**deprecated**. declare a style for a particular property"""
        self._props[prop] = { 'val' : value, 'fun' : fun }
            
