import cairo as cr
from osgeo import osr
import math

class UnsupportedFeatureType(Exception):
    """Attempted to render an unsupported feature type"""

class TODOError(Exception):
    """Attempted to use a feature that hasn't been implemented yet"""

class MapRenderingContext(object):
    def __init__(self, proj, world, width, height):
        """Construct a context from scratch with a clear background"""
        self._proj = proj
        self._world = world
        self._width = width
        self._height = height
        self._bkg = None
        self._cache = {}

    def basemap(self, surface, proj, world):
        """Set the base map surface to a Cairo surface"""
        self._bkg = cr.surface
        self._width = surface.get_width()
        self._height = surface.get_height()
        self._world = world 
        self._proj = proj

    @classmethod
    def CreateFromRasterBand(cls, gdal_dataset, bandix, palette):
        """Set a base map layer from a paletted gdal band"""
        self = MapRenderingContext(None, None, None,None)
        self._bkg = cr.ImageSurface.create_for_data(
            palette(gdal_dataset.GetRasterBand(bandix).ReadAsArray(0,0,gdal_dataset.RasterXSize, gdal_dataset.RasterYSize)).ravel(), 
            cr.FORMAT_ARGB32, 
            gdal_dataset.RasterXSize, 
            gdal_dataset.RasterYSize, 
            gdal_dataset.RasterXSize)
        self._width = gdal_dataset.RasterXSize
        self._height = gdal_dataset.RasterYSize
        self._world = gdal_dataset.GetGeoTransform()
        self._proj = osr.ImportFromWkt(gdal_dataset.GetProjectionRef())
    
    @classmethod
    def CreateFromGDALData(cls, gdal_dataset, bands=[1,2,3,4], interp='rgba'):
        """Set the base layer from an rgb, rgba, or luminance raster band"""

    def imgcoords(self, x, y):
        """Return image coordinates from real-space coordinates"""
        w, dx, _x, n, _y, dy = self._world
        return ((x-w)/dx , (y-n)/dy)

    def begin(self):
        """Make _surface clean"""
        self._surface = cr.ImageSurface(cr.FORMAT_ARGB32, self._width, self._height)
        self._basectx = cr.Context(self._surface)
        if self._bkg:
            self._basectx.set_operator(cr.OPERATOR_SOURCE)
            self._basectx.set_source_surface(self._bkg)
            self._basectx.paint()
        self._slate = cr.ImageSurface(cr.FORMAT_ARGB32, self._width, self._height)
        self._slatectx = cr.Context(self._slate)
        self._basectx.set_source_surface(self._slate)

    def end(self):
        """Finalize _surface if necessary and return _surface"""
        
    def cleanslate(self):
        """Return a clear surface with the same physical size as the underlying one"""
        self._slatectx.set_source_rgba(1,1,1,0)
        self._slatectx.set_operator(cr.OPERATOR_SOURCE)
        self._slatectx.paint()

    def __call__(self, *layers):
        """Render a bunch of layers"""
        self.begin()
        for layer, stylesheet in layers:
            self.render(layer, stylesheet)
        self.end()
        return self._surface
    
    def render(self, layer, stylesheet):
        """Style the data and layer it onto the current context
        
        * ctx : a Context object
        """
        pxlsz = (self._world[1], self._world[5])
        # do things that can be pre-styled
        stylesheet.constants(self._slatectx)
        for feature, data in layer.features:
            # use the context to find every point in the feature's location on the surface
            # draw feature and labels
            self.cleanslate()
            if feature.type == 'Point':
                self._render_point(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiPoint':
                for p in feature.geoms:
                    self._render_point(feature, data, pxlsz, stylesheet)
            elif feature.type == 'LineString':
                self._render_linestring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'LinearRing':
                self._render_linearring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiLineString':
                for p in feature.geoms:
                    self._render_linestring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'Polygon':
                self._render_polygon(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiPolygon':
                for p in feature.geoms:
                    self._render_polygon(feature, data, pxlsz, stylesheet)
            elif feature.type == 'GeometryCollection':
                self._render_collection(feature, data, pxlsz, stylesheet)
            else:
                raise UnsupportedFeatureType("Attempted to render unknown feature type '{f}'".format(feature.type))
            # change layering operator
            stylesheet.set_layeringoperator(self._basectx, data, pxlsz, stylesheet)
            # apply to context's surface
            self._basectx.paint()

    def _render_linestring(self, f, data, pxlsz, ss):
        c = self._slatectx
        c.set_operator(cr.OPERATOR_OVER)
        where = self.imgcoords(*f.coords[0])

        ss.style_stroke(c, data, pxlsz)
        ss.style.strokecap(c, data, pxlsz)
        c.move_to(*where)
        for x, y in f.coords[1:]:
            c.line_to(self.imgcoords(x,y))
        c.stroke()

        label = ss.get_label(data)
        if label and len(label) > 0 and ss.style_label(c, data, pxlsz):
            xoff, yoff = ss.get_labeloffsets(data, pxlsz)
            c.save()
            
            c.move_to(0,0)
            anchor = self.imgcoords(f.interpolate(xoff, normalized=True))
            xbear, ybear, width, height, _0, _1 = cr.text_extents(label)
            width = width * pxlsz[0]
            adv = self.imgcoords(*f.interpolate(f.length*xoff + width))
            angle = math.arctan((adv[1] - anchor[1]) / (adv[0] - anchor[0]))
            c.translate(-yoff*height)
            c.rotate(angle)
            c.translate(*anchor)
            if ss.style_labelhalo(c, data, pxlsz):
                c.text_path(label)
                c.stroke()
            
            c.text_path(label)
            if ss.style_labelfill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_labelstroke(c, data, pxlsz):
                c.stroke()

            c.restore()


    def _render_linearring(self, f, data, pxlsz, ss):
        c = self._slatectx
        c.set_operator(cr.OPERATOR_OVER)
        ss.style_stroke(c, data, pxlsz)
        c.move_to(*self.imgcoords(*f.coords[0]))
        for x, y in f.coords[1:]:
            c.line_to(self.imgcoords(x,y))
        c.close_path()
        c.stroke()
        
        label = ss.get_label(data)
        if label and len(label) > 0 and ss.style_label(c, data, pxlsz):
            xoff, yoff = ss.get_labeloffsets(data, pxlsz)
            c.save()
            
            c.move_to(0,0)
            anchor = self.imgcoords(f.interpolate(xoff, normalized=True))
            xbear, ybear, width, height, _0, _1 = cr.text_extents(label)
            width = width * pxlsz[0]
            adv = self.imgcoords(*f.interpolate(f.length*xoff + width))
            angle = math.arctan((adv[1] - anchor[1]) / (adv[0] - anchor[0]))
            c.translate(-yoff*height)
            c.rotate(angle)
            c.translate(*anchor)
            if ss.style_labelhalo(c, data, pxlsz):
                c.text_path(label)
                c.stroke()
            
            c.text_path(label)
            if ss.style_labelfill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_labelstroke(c, data, pxlsz):
                c.stroke()

            c.restore()
 
    def _render_polygon(self, f, data, pxlsz, ss):
        c = self._slatectx
        c.set_operator(cr.OPERATOR_OVER)
        c.move_to(*self.imgcoords(*f.coords[0]))
        for x, y in f.exterior.coords[1:]:
            c.line_to(self.imgcoords(x,y))
        c.close_path()

        for interior in f.interiors:
            c.new_sub_path()
            c.move_to(*self.imgcoords(*f.coords[0]))
            for x, y in f.exterior.coords[1:]:
                c.line_to(self.imgcoords(x,y))
            c.close_path()

        if ss.style_fill(c, data, pxlsz):
            cr.fill_preserve()
        if ss.style_stroke(c, data, pxlsz):
            cr.stroke()
        
        label = ss.get_label(data)
        if label and len(label) > 0 and ss.style_label(c, data, pxlsz):
            anchor = self.imgcoords(*f.representative_point())
            xbear, ybear, width, height, _0, _1 = cr.text_extents(label)
            width = width * pxlsz[0]
            xoff = -(width+xbear) / 2.0
            yoff = (height-ybear) / 2.0
            c.move_to(anchor[0]+xoff, anchor[1]+yoff)

            if ss.style_labelhalo(c, data, pxlsz):
                c.text_path(label)
                c.stroke()
            
            c.text_path(label)
            if ss.style_labelfill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_labelstroke(c, data, pxlsz):
                c.stroke()


    def _render_collection(self, fs, data, pxlsz, stylesheet):
        for feature in fs:
            if feature.type == 'Point':
                self._render_point(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiPoint':
                for p in feature.geoms:
                    self._render_point(feature, data, pxlsz, stylesheet)
            elif feature.type == 'LineString':
                self._render_linestring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'LinearRing':
                self._render_linearring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiLineString':
                for p in feature.geoms:
                    self._render_linestring(feature, data, pxlsz, stylesheet)
            elif feature.type == 'Polygon':
                self._render_polygon(feature, data, pxlsz, stylesheet)
            elif feature.type == 'MultiPolygon':
                for p in feature.geoms:
                    self._render_polygon(feature, data, pxlsz, stylesheet)
            elif feature.type == 'GeometryCollection':
                self._render_collection(feature, data, pxlsz, stylesheet)
            else:
                raise UnsupportedFeatureType("Attempted to render unknown feature type '{f}'".format(feature.type))


    def _render_point(self, f, data, pxlsz, ss):
        c = self._slatectx
        c.set_operator(cr.OPERATOR_OVER)
        where = self.imgcoords(f.x, f.y)
        shape = ss.get_pointshape(data, pxlsz)
        r = ss.get_pointsize(data, pxlsz)
        if shape is 'circle':
            c.move_to(*where)
            c.arc(where[0], where[1], r, 0, 2*math.pi)
            if ss.style_fill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()
            
        elif shape is 'square':
            where = (where[0] - r, where[1] - r)
            c.move_to(*where)
            c.rel_line_to(0, r)
            c.rel_line_to(r, 0)
            c.rel_line_to(0, -r)
            c.close_path()
            if ss.style_fill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()
        
        elif shape is 'cross':
            c.move_to(*where)
            c.rel_line_to(0,r)
            c.rel_line_to(0,-2*r)
            c.rel_line_to(0,r)
            c.rel_line_to(-r,0)
            c.rel_line_to(2*r,0)
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()

        elif shape is 'x':
            c.move_to(*where)
            c.rel_line_to(r,r)
            c.rel_line_to(-2*r,-2*r)
            c.rel_line_to(r,r)
            c.rel_line_to(-r,-r)
            c.rel_line_to(2*r,2*r)
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()
            
        elif shape is 'star':
            coords = []
            o = (0,0)
            for x in range(0,5):
                o = (r*math.cos(2*x*math.pi/5) - o[0], r*math.sin(2*math.pi/5) - o[1])
                coords.append(o)
                o = (r*math.cos(math.pi + 2*x*math.pi/5) - o[0], r*math.sin(math.pi + 2*math.pi/5) - o[1])
                coords.append(o)
            c.move_to(*coords[0])
            for xy in coords[1:]:
                c.rel_line_to(xy)
            c.close_path()
            if ss.style_fill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()
            
        elif shape is 'triangle':
            c.move_to(where[0], where[1]+r)
            c.rel_line_to(r*math.cos(2*math.pi/3), r*math.sin(2*math.pi/3) - r)
            c.rel_line_to(-2*r*math.cos(2*math.pi/3), 0)
            c.close_path()
            if ss.style_fill(c, data, pxlsz):
                c.fill_preserve()
            if ss.style_stroke(c, data, pxlsz):
                c.stroke()

        else:
            imgfile = ss.get_pointgraphic(data, pxlsz)
            if imgfile in self._cache:
                surf = self._cache[imgfile]
            else:
                surf = self._cache[imgfile] = cr.ImageSurface.create_from_png(imgfile)
            
            c.set_source_surface(surf)
            c.save()
            c.translate(*where)
            c.paint()
            c.restore()

        label = ss.get_label(data)
        if label and len(label) > 0 and ss.style_label(c, data, pxlsz):
            anchor = self.imgcoords(f.x, f.y)
            xoff, yoff = ss.get_labeloffsets(data, pxlsz)
            c.move_to(anchor[0]+xoff, anchor[1]+yoff)

            if ss.style_labelhalo(c, data, pxlsz):
                c.text_path(label)
                c.stroke()
            
            c.text_path(label)
            if ss.style_labelfill(data, pxlsz):
                c.fill_preserve()
            if ss.style_labelstroke(data, pxlsz):
                c.stroke()
        
    
    @property
    def surface(self):
        return self._surface

    @property
    def scale(self):
        """Return the width and height of one pixel, in terms of projection units"""
        return (self._world[1], self._world[5])

