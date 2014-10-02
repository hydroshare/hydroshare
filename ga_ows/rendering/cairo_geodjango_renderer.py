"""This is the rendering module to use if you expect to have Django's GEOS geometries.  All the renderers are exactly the same
except in the class of geometry they expect.  This class is not directly used, generally, but is rather used by a WMS
adapter to render.  If you're interested, see :class:`ga_ows.views.wms.GeoDjangoWMSAdapter` and it's get_2d_dataset method.
"""
import cairo as cr
import math

#: These operators can be used in stylesheets to change the way a layer is rendered.  For more information on their usage,
#: check out `Cairo's website`_
#:
#: Operators are: add, atop, clear, dest, dest atop, dest in, dest out, dest over, in, out, over, saturate, source, and xor
#:
#: .. _`Cairo's website`: http://www.cairographics.org
OPERATORS = {
    'add' : cr.OPERATOR_ADD,
    'atop' : cr.OPERATOR_ATOP,
    'clear' : cr.OPERATOR_CLEAR,
    'dest' : cr.OPERATOR_DEST,
    'dest atop':cr.OPERATOR_DEST_ATOP,
    'dest in':cr.OPERATOR_DEST_IN,
    'dest out':cr.OPERATOR_DEST_OUT,
    'dest over':cr.OPERATOR_DEST_OVER,
    'in':cr.OPERATOR_IN,
    'out':cr.OPERATOR_OUT,
    'over':cr.OPERATOR_OVER,
    'saturate':cr.OPERATOR_SATURATE,
    'source':cr.OPERATOR_SOURCE,
    'xor':cr.OPERATOR_XOR
}

#: These operators can be used in stylesheets to change the way linesegments are joined.  For more information on their usage,
#: check out `Cairo's website`_
#:
#: Operators are: bevel, round, and join
#:
#: .. _`Cairo's website`: http://www.cairographics.org
STROKEJOINS = {
    "bevel" : cr.LINE_JOIN_BEVEL, 
    "round" : cr.LINE_JOIN_ROUND,
    "miter" : cr.LINE_JOIN_MITER
}

#: These operators can be used in stylesheets to change the way a line ends are rendered.  For more information on their usage,
#: check out `Cairo's website`_
#:
#: Operators are: butt, round, and square
#:
#: .. _`Cairo's website`: http://www.cairographics.org
STROKECAPS = { 
    "butt" : cr.LINE_CAP_BUTT,
    "round" : cr.LINE_CAP_ROUND,
    "square" : cr.LINE_CAP_SQUARE
}

#: These are point shapes that can be rendered by the renderer.  They can be used as point_shape in the stylesheet.
#:
#: Operators are: circle, square, cross, x, diamond, and star
#:
#: .. _`Cairo's website`: http://www.cairographics.org
POINTSHAPES = {
    'circle' : 0,
    'square' : 1,
    'cross' : 2,
    'x' : 3,
    'diamond' : 4,
    'star' : 5
}

#: These operators can be used in stylesheets to change the way text is rendered.
#:
#: Operators are: normal and italic
#:
#: .. _`Cairo's website`: http://www.cairographics.org
FONTSLANTS = {
    'normal' : cr.FONT_SLANT_NORMAL,
    'italic' : cr.FONT_SLANT_ITALIC
}

#: These operators can be used in stylesheets to change the way text is rendered.
#:
#: Operators are: normal and bold
#:
#: .. _`Cairo's website`: http://www.cairographics.org
FONTWEIGHTS = {
    'normal' : cr.FONT_WEIGHT_NORMAL,
    'bold' : cr.FONT_WEIGHT_BOLD
}

class RenderingContext(object):
    """Renders geometry to a Cairo surface"""

    def __init__(self, ss, minx, miny, maxx, maxy, width, height, surfdata=None):
        """
        :param ss: stylesheet to use for this geometry.  A :class:`ga_ows.rendering.styler.Stylesheet`
        :param minx: the minx to render in the geometry's coordinate system
        :param miny: the miny to render
        :param maxx: the maxx to render
        :param maxy: the maxy to render
        :param width: the width of the image in pixels
        :param height: the height of the image in pixels
        :param surfdata: if we have pre-rendered surface data (like another layer), pass it in so a new surface isn't created.
        :return:
        """
        self.ss = ss
        
        self.minx=minx
        self.miny=miny
        self.maxx=maxx
        self.maxy=maxy

        if surfdata:
            self.surface = cr.ImageSurface.create_for_data(surfdata, cr.FORMAT_ARGB32, width, height)
        else:
            self.surface = cr.ImageSurface(cr.FORMAT_ARGB32, width, height)
        self.ctx = cr.Context(self.surface)
        self.width = width
        self.height = height
        self.pixel_w = (maxx-minx) / width
        self.pixel_h = (maxy-miny) / height
        self._cache = {}

    def _xy(self, x, y):
        return ((x-self.minx) / self.pixel_w,
                -(y-self.maxy) / self.pixel_h)

    def cleanslate(self):
        """Clear the slate for new rendering.
        """
        self.ctx.set_source_rgba(1,1,1,0)
        self.ctx.set_operator(cr.OPERATOR_SOURCE)
        self.ctx.paint()

    def render(self, data, geometry_accessor):
        """
        :param data: The data to use.  This will be passed to the styler wholesale.
        :param geometry_accessor: The accessor to get at the data's geometry.  It is applied to the data object and should return a Geometry object.
        :return: None
        """
        label_queue = []

        s0 = frozenset()
        stroke_pending = False
        fill_pending = False
        for datum in data:
            g = geometry_accessor(datum)#.simplify(self.pixel_w, preserve_topology=True)
            s = self.ss.styles(datum, self.pixel_w)
            s1 = s0 ^ s
            s0 = s
            l, ls = self.ss.label(datum, self.pixel_w)
            if l:
                label_queue.append((g,l,ls))

            if s1 is not None and len(s1) > 0:
                if stroke_pending and fill_pending:
                    self.ctx.set_source_rgba(*self.fill_color)
                    self.ctx.fill_preserve()
                    self.ctx.set_source_rgba(*self.stroke_color)
                    self.ctx.stroke()
                elif stroke_pending:
                    self.ctx.set_source_rgba(*self.stroke_color)
                    self.ctx.stroke()
                elif fill_pending:
                    self.ctx.set_source_rgba(*self.fill_color)
                    self.ctx.fill()
                
                if stroke_pending or fill_pending:
                    fill_pending = False
                    stroke_pending = False
                    self.ctx.restore()
                
                stroke_pending, fill_pending = self._change_styles(s)

            self._sketch_feature(g)

        if stroke_pending and fill_pending:
            self.ctx.set_source_rgba(*self.fill_color)
            self.ctx.fill_preserve()
            self.ctx.set_source_rgba(*self.stroke_color)
            self.ctx.stroke()
            self.ctx.restore()
        elif stroke_pending:
            self.ctx.set_source_rgba(*self.stroke_color)
            self.ctx.stroke()
            self.ctx.restore()
        elif fill_pending:
            self.ctx.set_source_rgba(*self.fill_color)
            self.ctx.fill()
            self.ctx.restore()
    
        self._draw_labels(label_queue)

    def _sketch_feature(self, g):
        """check the feature type and delegate ot the other sketch methods"""
        if g.geom_type == 'Point':
            self._sketch_point(g)
        elif g.geom_type == 'LineString':
            self._sketch_linestring(g)
        elif g.geom_type == 'MultiLineString':
             self._sketch_multilinestring(g)
        elif g.geom_type == 'Polygon':
            self._sketch_polygon(g)
        elif g.geom_type == 'MultiPolygon':
             self._sketch_multipolygon(g)
        elif g.geom_type == 'GeometryCollection':
            self._sketch_collection(g)
        elif g.geom_type == 'LinearRing':
            self._sketch_linearring(g)
        else:
            raise Exception('unsupported feature type ' + g.geom_type)

    def _sketch_linestring(self, g):
        xys = [self._xy(x,y) for x, y in g.coords]
        self.ctx.move_to(*xys[0])
        for x, y in xys[1:]:
            self.ctx.line_to(x,y)

    def _sketch_multilinestring(self, g):
        for linestring in g.coords:
            xys = [self._xy(x,y) for x, y in linestring]
            self.ctx.move_to(*xys[0])
            for x, y in xys[1:]:
                self.ctx.line_to(x,y)

    def _sketch_linearring(self, g):
        self._sketch_linestring(g)
        self.ctx.close_path()

    def _sketch_polygon(self, g):
        xys = [self._xy(x,y) for x, y in g.coords[0]]
        if xys:
            self.ctx.move_to(*xys[0])
            for x, y in xys[1:]:
                self.ctx.line_to(x,y)
            self.ctx.close_path()

            if len(g.coords) > 1:
                for interior in g.coords[1:]:
                    ixys = [self._xy(x,y) for x, y in interior]
                    self.ctx.new_sub_path()
                    self.ctx.move_to(*ixys[0])
                    for x, y in ixys[1:]:
                        self.ctx.line_to(x,y)
                    self.ctx.close_path()
    
    def _sketch_multipolygon(self, g):
        for polygon in g.coords:
            xys = [self._xy(x,y) for x, y in polygon[0]]
            self.ctx.move_to(*xys[0])
            for x, y in xys[1:]:
                self.ctx.line_to(x,y)
                #self.ctx.close_path()

            if len(polygon) > 1:
                for interior in polygon[1:]:
                    ixys = [self._xy(x,y) for x, y in interior]
                    self.ctx.new_sub_path()
                    self.ctx.move_to(*ixys[0])
                    for x, y in ixys[1:]:
                        self.ctx.line_to(x,y)
                        #self.ctx.close_path()

    def _sketch_collection(self, gs):
        for g in gs:
            if g.type == 'Point':
                self._sketch_point(self, g)
            elif g.type == 'LineString':
                self._sketch_linestring(self, g)
            elif g.type == 'MultiLineString':
                self._sketch_multilinestring(g)
            elif g.type == 'Polygon':
                self._sketch_polygon(g)
            elif g.type == 'MultiPolygon':
                self._sketch_multipolygon(g)
            elif g.type == 'GeometryCollection':
                self._sketch_collection(g)
            elif g.type == 'LinearRing':
                self._sketch_linearring(g)

    def _sketch_point(self, g):
        x,y = self._xy(g.x, g.y)
        self.ctx.move_to(x,y)
        r = self._pointsize
        if self._shape is 'circle':
            self.ctx.arc(x, y, r, 0, 2*math.pi)
        elif self._shape is 'square':
            self.ctx.rel_line_to(0,r)
            self.ctx.rel_line_to(r,0)
            self.ctx.rel_line_to(0,-r)
            self.ctx.close_path()
        elif self._shape is 'cross':
            self.ctx.rel_line_to(0,r)
            self.ctx.rel_line_to(0,-2*r)
            self.ctx.rel_line_to(0,r)
            self.ctx.rel_line_to(-r,0)
            self.ctx.rel_line_to(2*r,0)
        elif self._shape is 'x':
            self.ctx.rel_line_to(r,r)
            self.ctx.rel_line_to(-2*r,-2*r)
            self.ctx.rel_line_to(r,r)
            self.ctx.rel_line_to(-r,-r)
            self.ctx.rel_line_to(2*r,2*r)
        elif self._shape is 'triangle':
            self.ctx.move_to(x, y+r)
            self.ctx.rel_line_to(
                r*math.cos(2*math.pi/3), 
                r*math.sin(2*math.pi/3) - r)
            self.ctx.rel_line_to(-2*r*math.cos(2*math.pi/3), 0)
            self.ctx.close_path()
        elif self._shape is 'star':
            coords = []
            o = (0,0)
            for x in range(0,5):
                o = (r*math.cos(2*x*math.pi/5) - o[0], r*math.sin(2*math.pi/5) - o[1])
                coords.append(o)
                o = (r*math.cos(math.pi + 2*x*math.pi/5) - o[0], 
                     r*math.sin(math.pi + 2*math.pi/5) - o[1])
                coords.append(o)
            self.ctx.move_to(*coords[0])
            for xy in coords[1:]:
                self.ctx.rel_line_to(xy)
            self.ctx.close_path()
        elif self._imagefile:
            surf = self._cache[self._imagefile]
            self.ctx.set_source_surface(surf)
            self.ctx.save()
            self.ctx.translate(x,y)
            self.ctx.paint()
            self.ctx.restore()

    def _reckon(self, geom):
        """analyze a geometry to figure out where the label should go"""
        try:
            if geom.geom_type == 'Point':
                x, y = self._xy(geom.x, geom.y)
                return x+5, y-5, 0
            elif geom.geom_type in ('MultiPoint', 'Polygon', 'MultiPolygon', 'LinearRing'):
                p = geom.centroid
                x, y = self._xy(p.x, p.y)
                return x, y, 0
            elif geom.geom_type == 'LineString' and len(geom.coords) >= 2:
                p1x, p1y = geom.coords[len(geom.coords)/2]
                p2x, p2y = geom.coords[len(geom.coords)/2+1]
                rise = p2y-p1y
                run = p2x-p1x
                if run == 0:
                    run = 0.01*math.pi
                theta = math.atan(rise/run)
                x, y = self._xy(p1x, p1y)
                return x, y, theta
            elif geom.geom_type == 'MultiLineString' and len(geom.geoms[0].coords) >= 2:
                p1x, p1y = geom.geoms[0].coords[len(geom.coords)/2]
                p2x, p2y = geom.geoms[0].coords[len(geom.coords)/2+1]
                rise = p2y-p1y
                run = p2x-p1x
                if run == 0:
                    run = 0.01*math.pi
                theta = math.atan(rise/run)
                x, y = self._xy(p1x, p1y)
                return x, y, theta
            else:
                p = geom.centroid
                x, y = self._xy(p.x, p.y)
                return x, y, 0
        except:
            print geom.centroid

        return 0,0,0

    def _draw_labels(self, lbls):
        prevstyle = frozenset()
        pending = False
        haloes = False

        for geom, label, style in lbls:
            if label and len(label) > 0: 
                x, y, theta = self._reckon(geom)
                
                if len(prevstyle ^ style) > 0:
                    if pending:
                        if haloes: 
                            self.ctx.set_source_rgba(*self.halo_color)
                            self.ctx.set_line_width(self.halo_size)
                            self.ctx.stroke_preserve()
                        self.ctx.set_source_rgba(*self.label_color)
                        self.ctx.fill()
                        self.ctx.restore()
                        pending = False
                    self._style_labels(style)
                    haloes = self._style_haloes(style)
                    prevstyle = style
                
            self.ctx.save()
            self.ctx.translate(x,y)
            self.ctx.rotate(-theta)
            self.ctx.translate(*self.label_offsets)
            if self.label_align is 'right':
                xb,yb,w,h,_0,_1 = self.ctx.text_extents(label)
                self.ctx.translate(-w, 0)
            elif self.label_align is 'center':
                xb,yb,w,h,_0,_1 = self.ctx.text_extents(label)
                self.ctx.translate(-w/2, 0)

            self.ctx.text_path(label)
            self.ctx.restore()
            pending = True

        if pending:
            if haloes: 
                self.ctx.set_source_rgba(*self.halo_color)
                self.ctx.set_line_width(self.halo_size)
                self.ctx.stroke_preserve()
            self.ctx.set_source_rgba(*self.label_color)
            self.ctx.fill()
            self.ctx.restore()

    def _change_styles(self, s):
        sheet = dict(s)

        will_stroke = False
        will_fill = False

        self.ctx.save()
        if 'stroke_width' in sheet and sheet['stroke_width'] is not None:
            self.ctx.set_line_width(sheet['stroke_width'])
            will_stroke = True
        if 'stroke_color' in sheet and sheet['stroke_color'] is not None:
            self.stroke_color = sheet['stroke_color']
            will_stroke = True
        else:
            self.stroke_color = None

        if 'stroke_dash' in sheet and sheet['stroke_dash'] is not None:
            self.ctx.set_dash(sheet['stroke_dash'])
        if 'stroke_join' in sheet and sheet['stroke_join'] is not None:
            self.ctx.set_line_join(STROKEJOINS[sheet['stroke_join']])
        if 'stroke_cap' in sheet and sheet['stroke_cap'] is not None:
            self.ctx.set_line_cap(STROKECAPS[sheet['stroke_cap']])

        if 'fill_pattern' in sheet and sheet['fill_pattern'] is not None:
            img = sheet['fill_pattern']
            if img:
                if img in self._cache:
                    img = self._cache[img]
                    self.fill_pattern = img
                else:
                    self.ctx.save()
                    img = self._cache[img] = self.ctx.pattern_create_for_surface(cr.ImageSurface.create_from_png(img))
                    self.fill_pattern = img
                    self.set_source(img)
                    self.ctx.pattern_set_extend(self.ctx.get_source(), cr.EXTEND_REPEAT)
                    self.ctx.restore()
            will_fill=True
        else:
            self.fill_pattern = None
        
        if 'fill_color' in sheet and sheet['fill_color'] is not None:
            self.fill_color = sheet['fill_color']
            will_fill = True
        else:
            self.fill_color = None

        if 'compositing_operator' in sheet and sheet['compositing_operator'] is not None:
            self.ctx.set_operator(OPERATORS[sheet['compositing_operator']])
        else:
            self.ctx.set_operator(cr.OPERATOR_OVER)

        if 'point_shape' in sheet and sheet['point_shape'] is not None:
            self._shape = sheet['point_shape']

        if 'point_size' in sheet and sheet['point_size'] is not None:
            self._pointsize = sheet['point_size']

        if 'point_icon' in sheet and sheet['point_icon'] is not None:
            if sheet['point_icon'] not in self._cache:
                self.point_icon = cr.ImageSurface.create_from_png(sheet['point_icon'])
                self._cache[sheet['point_icon']] = self._point_icon
            else:
                self.point_icon = self._cache[sheet['point_icon']]
        return will_stroke, will_fill

    def _style_labels(self, s):
        sheet = dict(s)
        
        self.ctx.save()

        slant = cr.FONT_SLANT_NORMAL
        weight = cr.FONT_WEIGHT_NORMAL
        if 'font_slant' in sheet and sheet['font_slant'] is not None:
            slant = FONTSLANTS[sheet['font_slant']]
        if 'font_weight' in sheet and sheet['font_weight'] is not None:
            weight = FONTWEIGHTS[sheet['font_weight']]
        size = 10
        options = None
        face = 'Arial'
        if 'font_size' in sheet and sheet['font_size'] is not None:
            size = sheet['font_size']
        if 'font_options' in sheet and sheet['font_options'] is not None:
            options = sheet['font_options']
        if 'font_face' in sheet and sheet['font_face'] is not None:
            face = sheet['font_face']
        if 'label_align' in sheet and sheet['label_align'] is not None:
            self.label_align = sheet['label_align']
        else:
            self.label_align = 'left'
        if 'label_offsets' in sheet and sheet['label_offsets'] is not None:
            self.label_offsets = sheet['label_offsets']
        else:
            self.label_offsets = (0,-8)

        self.ctx.select_font_face(face,slant,weight)
        self.ctx.set_font_size(size)

        if 'label_color' in sheet and sheet['label_color'] is not None:
            self.label_color = sheet['label_color']
        else:
            self.label_color = (0,0,0,1)

        if options is not None:
            self.ctx.set_font_options(options)

    def _style_haloes(self, s):
        sheet = dict(s)
        
        if 'label_halo_size' in sheet and sheet['label_halo_size'] is not None:
            self.halo_size = sheet['label_halo_size']
        else:
            self.halo_size = 1

        if 'label_halo_color' in sheet and sheet['label_halo_color'] is not None:
            self.halo_color = sheet['label_halo_color']
            return True
        else:
            return False

