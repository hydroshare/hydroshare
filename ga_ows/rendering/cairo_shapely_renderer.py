import cairo as cr 
import math

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

STROKEJOINS = {
    "bevel" : cr.LINE_JOIN_BEVEL, 
    "round" : cr.LINE_JOIN_ROUND,
    "miter" : cr.LINE_JOIN_MITER
}

STROKECAPS = { 
    "butt" : cr.LINE_CAP_BUTT,
    "round" : cr.LINE_CAP_ROUND,
    "square" : cr.LINE_CAP_SQUARE
}

POINTSHAPES = {
    'circle' : 0,
    'square' : 1,
    'cross' : 2,
    'x' : 3,
    'diamond' : 4,
    'star' : 5
}

FONTSLANTS = {
    'normal' : cr.FONT_SLANT_NORMAL,
    'italic' : cr.FONT_SLANT_ITALIC
}

FONTWEIGHTS = {
    'normal' : cr.FONT_WEIGHT_NORMAL,
    'bold' : cr.FONT_WEIGHT_BOLD
}

class RenderingContext(object):
    def __init__(self, ss, minx, miny, maxx, maxy, width, height, surfdata=None):
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

    def xy(self, x, y):
        return ((x-self.minx) / self.pixel_w,
                -(y-self.maxy) / self.pixel_h)

    def cleanslate(self):
        self.ctx.set_source_rgba(1,1,1,0)
        self.ctx.set_operator(cr.OPERATOR_SOURCE)
        self.ctx.paint()

    def render(self, data, geometry_accessor):
        label_queue = []

        s0 = frozenset()
        stroke_pending = False
        fill_pending = False
        for datum in data:
            g = geometry_accessor(datum)
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
                
                stroke_pending, fill_pending = self.change_styles(s)

            self.sketch_feature(g)

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
    
        #self.draw_haloes(label_queue)
        self.draw_labels(label_queue)

    def sketch_feature(self, g):
        if g.type == 'Point':
            self.sketch_point(g)
        elif g.type == 'MultiPoint':
            for pg in g.geoms:
                self.sketch_point(pg)
        elif g.type == 'LineString':
            self.sketch_linestring(g)
        elif g.type == 'MultiLineString':
            for pg in g.geoms:
                self.sketch_linestring(pg)
        elif g.type == 'Polygon':
            self.sketch_polygon(g)
        elif g.type == 'MultiPolygon':
            for pg in g.geoms:
                self.sketch_polygon(pg)
        elif g.type == 'GeometryCollection':
            self.sketch_collection(g)
        elif g.type == 'LinearRing':
            self.sketch_linearring(g)
        else:
            raise ('unsupported feature type ' + g)

    def sketch_linestring(self, g):
        xys = [self.xy(x,y) for x, y in g.coords]
        self.ctx.move_to(*xys[0])
        for x, y in xys[1:]:
            self.ctx.line_to(x,y)

    def sketch_linearring(self, g):
        self.sketch_linestring(g)
        self.ctx.close_path()

    def sketch_polygon(self, g):
        xys = [self.xy(x,y) for x, y in g.exterior.coords]
        self.ctx.move_to(*xys[0])
        for x, y in xys[1:]:
            self.ctx.line_to(x,y)
        self.ctx.close_path()

        for interior in g.interiors:
            ixys = [self.xy(x,y) for x, y in interior.coords] 
            self.ctx.new_sub_path()
            self.ctx.move_to(*ixys[0])
            for x, y in xys[1:]:
                self.ctx.line_to(x,y)
            self.ctx.close_path()

    def sketch_collection(self, gs):
        for g in gs:
            if g.type == 'Point':
                self.sketch_point(self, g)
            elif g.type == 'MultiPoint':
                for pg in g.geoms:
                    self.sketch_point(self, pg)
            elif g.type == 'LineString':
                self.sketch_linestring(self, g)
            elif g.type == 'MultiLineString':
                for pg in g.geoms:
                    self.sketch_linestring(self, pg)
            elif g.type == 'Polygon':
                self.sketch_polygon(self, g)
            elif g.type == 'MultiPolygon':
                for pg in g.geoms:
                    self.sketch_polygon(self, pg)
            elif g.type == 'GeometryCollection':
                self.sketch_collection(self, g)
            elif g.type == 'LinearRing':
                self.sketch_linearring(self, g)
            

    def sketch_point(self, g):
        x,y = self.xy(g.x, g.y)
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

    def reckon(self, geom):
        """analyze a geometry to figure out where the label should go"""
        if geom.type is 'Point':
            x, y = self.xy(geom.x, geom.y)
            return x+5, y-5, 0
        elif geom.type in ('MultiPoint', 'Polygon', 'MultiPolygon', 'LinearRing'):
            p = geom.centroid
            x, y = self.xy(p.x, p.y)
            return x, y, 0
        elif geom.type is 'LineString' and len(geom.coords) >= 2:
            p1x, p1y = geom.coords[len(geom.coords)/2]
            p2x, p2y = geom.coords[len(geom.coords)/2+1]
            rise = p2y-p1y
            run = p2x-p1x
            if run == 0:
                run = 0.01*math.pi
            theta = math.atan(rise/run)
            x, y = self.xy(p1x, p1y)
            return x, y, theta
        elif geom.type is 'MultiLineString' and len(geom.geoms[0].coords) >= 2:
            p1x, p1y = geom.geoms[0].coords[len(geom.coords)/2]
            p2x, p2y = geom.geoms[0].coords[len(geom.coords)/2+1]
            rise = p2y-p1y
            run = p2x-p1x
            if run == 0:
                run = 0.01*math.pi
            theta = math.atan(rise/run)
            x, y = self.xy(p1x, p1y)
            return x, y, theta
        else:
            p = geom.centroid
            x, y = self.xy(p.x, p.y)
            return x, y, 0

        return 0,0,0

    def draw_labels(self, lbls):
        prevstyle = frozenset()
        pending = False
        haloes = False

        for geom, label, style in lbls:
            if label and len(label) > 0: 
                x, y, theta = self.reckon(geom)
                
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
                    self.style_labels(style)
                    haloes = self.style_haloes(style)
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

    def change_styles(self, s):
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

    def style_labels(self, s):
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

        self.ctx.select_font_face(face,weight,slant)
        self.ctx.set_font_size(size)

        if 'label_color' in sheet and sheet['label_color'] is not None:
            self.label_color = sheet['label_color']
        else:
            self.label_color = (0,0,0,1)

        if options is not None:
            self.ctx.set_font_options(options)

    def style_haloes(self, s):
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

