from mezzanine.pages.models import Page, RichText
from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from mezzanine.pages.page_processors import processor_for
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class RefTimeSeries(BaseResource):
    objects = ResourceManager()

    class Meta:
        verbose_name = "HIS Referenced Time Series"
        proxy = False

    reference_type = models.CharField(max_length=4, null=False, blank=True, default='')
    url = models.URLField(null=False, blank=True, default='',
                          verbose_name='Web Services Url')

    def extra_capabilities(self):
        return None

    @property
    def metadata(self):
        md = RefTSMetadata()
        return self._get_metadata(md)

    def can_add(self, request):
        return super(RefTimeSeries, self).can_add(self, request)

    def can_change(self, request):
        return super(RefTimeSeries, self).can_change(self, request)

    def can_delete(self, request):
        return super(RefTimeSeries, self).can_delete(self, request)

    def can_view(self, request):
        return super(RefTimeSeries, self).can_view(self, request)

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False


processor_for(RefTimeSeries)(resource_processor)

class ReferenceURL(AbstractMetaDataElement):
    term = 'Reference URL'
    value = models.CharField(max_length=500)
    type = models.CharField(max_length=4)

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if 'content_object' in kwargs:
                metadata_obj = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                referenceURL = ReferenceURL.objects.filter(value__iexact=kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if referenceURL:
                    raise ValidationError('Reference URL:%s already exists' % kwargs['value'])
                referenceURL = ReferenceURL.objects.create(value=kwargs['value'], type=kwargs['type'], content_object=metadata_obj)
                return referenceURL
            else:
                raise ValidationError('Metadata instance for which Reference URL element to be created is missing.')
        else:
            raise ValidationError("Value of Reference URL is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        referenceURL = ReferenceURL.objects.get(id=element_id)
        if referenceURL:
            if 'value' in kwargs:
                referenceURL.value = kwargs['value']
                referenceURL.save()
            else:
                raise ValidationError('Value of Reference URL is missing')
        else:
            raise ObjectDoesNotExist("No Reference URL element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        referenceURL = ReferenceURL.objects.get(id=element_id)
        if referenceURL:
            referenceURL.delete()
        else:
            raise ObjectDoesNotExist("No method element was found for id:%d." % element_id)

class Method(AbstractMetaDataElement):
    term = 'Method'
    value = models.CharField(max_length=200)

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if 'content_object' in kwargs:
                metadata_obj = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                method = Method.objects.filter(value__iexact=kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if method:
                    raise ValidationError('Method:%s already exists' % kwargs['value'])
                method = Method.objects.create(value=kwargs['value'], content_object=metadata_obj)
                return method
            else:
                raise ValidationError('Metadata instance for which method element to be created is missing.')
        else:
            raise ValidationError("Value of method is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        method = Method.objects.get(id=element_id)
        if method:
            if 'value' in kwargs:
                method.value = kwargs['value']
                method.save()
            else:
                raise ValidationError('Value of method is missing')
        else:
            raise ObjectDoesNotExist("No method element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        method = Method.objects.get(id=element_id)
        if method:
            method.delete()
        else:
            raise ObjectDoesNotExist("No method element was found for id:%d." % element_id)


class QualityControlLevel(AbstractMetaDataElement):
    term = 'QualityControlLevel'
    value = models.CharField(max_length=200)

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if 'content_object' in kwargs:
                metadata_obj = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                quality_level = QualityControlLevel.objects.filter(value__iexact=kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if quality_level:
                    raise ValidationError('QualityControlLevel :%s already exists' % kwargs['value'])
                quality_level = QualityControlLevel.objects.create(value=kwargs['value'], content_object=metadata_obj)
                return quality_level
            else:
                raise ValidationError('Metadata instance for which QualityControlLevel element to be created is missing.')
        else:
            raise ValidationError("Value of QualityControlLevel is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        quality_level = QualityControlLevel.objects.get(id=element_id)
        if quality_level:
            if 'value' in kwargs:
                if quality_level.value != kwargs['value']:
                    # check this new value not already exists
                    if QualityControlLevel.objects.filter(value__iexact=kwargs['value'], object_id=quality_level.object_id,
                                                          content_type__pk=quality_level.content_type.id).count()> 0:
                        raise ValidationError('QualityControlLevel value:%s already exists.' % kwargs['value'])
                    quality_level.value = kwargs['value']
                    quality_level.save()
            else:
                raise ValidationError('No Value provided in kwargs')
        else:
            raise ObjectDoesNotExist("No QualityControlLevel element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        quality_level = QualityControlLevel.objects.get(id=element_id)
        if quality_level:
            # make sure we are not deleting all coverages of a resource
            if QualityControlLevel.objects.filter(object_id=quality_level.object_id, content_type__pk=quality_level.content_type.id).count()== 1:
                raise ValidationError("The only QualityControlLevel of the resource can't be deleted.")
            quality_level.delete()
        else:
            raise ObjectDoesNotExist("No QualityControlLevel element was found for id:%d." % element_id)


class Variable(AbstractMetaDataElement):
    term = 'Variable'
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    data_type = models.CharField(max_length=50, null=True)
    sample_medium = models.CharField(max_length=50, null=True)

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            if 'content_object' in kwargs:
                metadata_obj = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                variable = Variable.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if variable:
                    raise ValidationError('Variable for resource already exists')
                else:
                    variable = Variable.objects.create(name=kwargs['name'], code=kwargs['code'], data_type=kwargs.get('data_type'), sample_medium=kwargs.get('sample_medium'), content_object=metadata_obj)
                    return variable
            else:
                raise ValidationError('metadata object is missing from inputs')
        else:
            raise ValidationError('name is missing from inputs')

    @classmethod
    def update(cls, element_id, **kwargs):
        variable = Variable.objects.get(id=element_id)
        if variable:
            if 'name' in kwargs:
                variable.name = kwargs['name']
            if 'code' in kwargs:
                variable.code = kwargs['code']
            if 'data_type' in kwargs:
                variable.data_type = kwargs['data_type']
            if 'sample_medium' in kwargs:
                variable.sample_medium = kwargs['sample_medium']
            variable.save()
        else:
            raise ObjectDoesNotExist("No variable element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        variable = Variable.objects.get(id=element_id)
        if variable:
            # make sure we are not deleting all coverages of a resource
            if Variable.objects.filter(object_id=variable.object_id, content_type__pk=variable.content_type.id).count()== 1:
                raise ValidationError("The only Variable of the resource can't be deleted.")
            variable.delete()
        else:
            raise ObjectDoesNotExist("No Variable element was found for id:%d." % element_id)


class Site(AbstractMetaDataElement):
    term = 'Site'
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            if 'content_object' in kwargs:
                metadata_obj = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                site = Site.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if site:
                    raise ValidationError('Site for resource already exists')
                else:
                    if 'code' in kwargs:
                        site = Site.objects.create(name=kwargs['name'], code=kwargs['code'], latitude=kwargs.get('latitude'), longitude=kwargs.get('longitude'), content_object=metadata_obj)
                        return site
                    else:
                        raise ValidationError('code is missing from inputs')
            else:
                raise ValidationError('metadata object is missing from inputs')
        else:
            raise ValidationError('name is missing from inputs')

    @classmethod
    def update(cls, element_id, **kwargs):
        site = Site.objects.get(id=element_id)
        if site:
            if 'name' in kwargs:
                site.name = kwargs['name']
            if 'code' in kwargs:
                site.code = kwargs['code']
            if 'latitude' in kwargs:
                site.latitude = kwargs['latitude']
            if 'longitude' in kwargs:
                site.longitude = kwargs['longitude']
            site.save()
        else:
            raise ObjectDoesNotExist("No site element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        site = Site.objects.get(id=element_id)
        if site:
            # make sure we are not deleting all coverages of a resource
            if Site.objects.filter(object_id=site.object_id, content_type__pk=site.content_type.id).count()== 1:
                raise ValidationError("The only Variable of the resource can't be deleted.")
            site.delete()
        else:
            raise ObjectDoesNotExist("No Site element was found for id:%d." % element_id)


# class Source(AbstractMetaDataElement):
#     term = 'Source'
#     derived_from = models.CharField(max_length=300)
#     organization = models.CharField(max_length=200, null=True)
#     source_description = models.CharField(max_length=400, null=True)
#
#     def __unicode__(self):
#         return self.derived_from
#
#     @classmethod
#     def create(cls, **kwargs):
#         if 'derived_from' in kwargs:
#             # check the source doesn't already exists - source needs to be unique per resource
#             if 'metadata_obj' in kwargs:
#                 metadata_obj = kwargs['metadata_obj']
#                 metadata_type = ContentType.objects.get_for_model(metadata_obj, relate_name='+')
#                 src = Source.objects.filter(derived_from= kwargs['derived_from'], object_id=metadata_obj.id, content_type=metadata_type,related_name='+').first()
#                 if src:
#                     raise ValidationError('Source:%s already exists for this resource.' % kwargs['derived_from'])
#                 src = Source.objects.create(derived_from=kwargs['derived_from'], organization=kwargs.get('organization'),source_description=kwargs.get('source_description'), content_object=metadata_obj)
#                 return src
#             else:
#                 raise ValidationError('Metadata instance for which source element to be created is missing.')
#         else:
#             raise ValidationError("Source data is missing.")
#
#     @classmethod
#     def update(cls, element_id, **kwargs):
#         src = Source.objects.get(id=element_id)
#         if src:
#             if 'derived_from' in kwargs:
#                 src.derived_from = kwargs['derived_from']
#             if 'organization' in kwargs:
#                 src.organization = kwargs['organization']
#             if 'source_description' in kwargs:
#                 src.source_description = kwargs['source_description']
#             src.save()
#         else:
#             raise ObjectDoesNotExist("No source element was found for the provided id:%s" % element_id)
#
#     @classmethod
#     def remove(cls, element_id):
#         src = Source.objects.get(id=element_id)
#         if src:
#             src.delete()
#         else:
#             raise ObjectDoesNotExist("No source element was found for id:%d." % element_id)


class RefTSMetadata(CoreMetaData):
    methods = generic.GenericRelation(Method)
    quality_levels = generic.GenericRelation(QualityControlLevel)
    variables = generic.GenericRelation(Variable)
    sites = generic.GenericRelation(Site)
    referenceURLs = generic.GenericRelation(ReferenceURL)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RefTSMetadata, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Method')
        elements.append('QualityControlLevel')
        elements.append('Variable')
        elements.append('Site')
        elements.append('ReferenceURL')
        return elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(RefTSMetadata, self).get_xml(pretty_print=True)
        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject resource specific metadata elements to container element
        for refURL in self.referenceURLs.all():
            hsterms_refURL = etree.SubElement(container, '{%s}ReferenceURL' % self.NAMESPACES['hsterms'])
            hsterms_refURL_rdf_Description = etree.SubElement(hsterms_refURL, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_refURL_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = refURL.value
            hsterms_name = etree.SubElement(hsterms_refURL_rdf_Description, '{%s}type' % self.NAMESPACES['hsterms'])
            hsterms_name.text = refURL.type

        for method in self.methods.all():
            hsterms_method = etree.SubElement(container, '{%s}method' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = method.value

        for q_l in self.quality_levels.all():
            hsterms_q_l = etree.SubElement(container, '{%s}qualitycontrollevel' % self.NAMESPACES['hsterms'])
            hsterms_q_l_rdf_Description = etree.SubElement(hsterms_q_l, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_q_l_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = q_l.value

        for variable in self.variables.all():
            hsterms_variable = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_variable_rdf_Description = etree.SubElement(hsterms_variable, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_variable_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = variable.name
            hsterms_code = etree.SubElement(hsterms_variable_rdf_Description, '{%s}code' % self.NAMESPACES['hsterms'])
            hsterms_code.text = variable.code
            hsterms_data_type = etree.SubElement(hsterms_variable_rdf_Description, '{%s}dataType' % self.NAMESPACES['hsterms'])
            hsterms_data_type.text = variable.data_type
            hsterms_sample_medium = etree.SubElement(hsterms_variable_rdf_Description, '{%s}sampleMedium' % self.NAMESPACES['hsterms'])
            hsterms_sample_medium.text = variable.sample_medium

        for site in self.sites.all():
            hsterms_site = etree.SubElement(container, '{%s}site' % self.NAMESPACES['hsterms'])
            hsterms_site_rdf_Description = etree.SubElement(hsterms_site, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_site_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = site.name
            hsterms_code = etree.SubElement(hsterms_site_rdf_Description, '{%s}code' % self.NAMESPACES['hsterms'])
            hsterms_code.text = site.code
            hsterms_latitude = etree.SubElement(hsterms_site_rdf_Description, '{%s}latitude' % self.NAMESPACES['hsterms'])
            hsterms_latitude.text = unicode(site.latitude) or ''
            hsterms_longitude = etree.SubElement(hsterms_site_rdf_Description, '{%s}longitude' % self.NAMESPACES['hsterms'])
            hsterms_longitude.text = unicode(site.longitude) or ''

        # for src in self.sources.all():
        #     hsterms_src = etree.SubElement(container, '{%s}src' % self.NAMESPACES['hsterms'])
        #     hsterms_src_rdf_Description = etree.SubElement(hsterms_src, '{%s}Description' % self.NAMESPACES['rdf'])
        #
        #     hsterms_name = etree.SubElement(hsterms_src_rdf_Description, '{%s}derivedFrom' % self.NAMESPACES['hsterms'])
        #     hsterms_name.text = src.derivedfrom
        #     hsterms_code = etree.SubElement(hsterms_src_rdf_Description, '{%s}organization' % self.NAMESPACES['hsterms'])
        #     hsterms_code.text = src.organization or ''
        #     hsterms_latitude = etree.SubElement(hsterms_src_rdf_Description, '{%s}sourceDescription' % self.NAMESPACES['hsterms'])
        #     hsterms_latitude.text = src.source_description or ''

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers
