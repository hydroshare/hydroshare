import unittest
from unittest import TestCase
from dateutil import parser

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group, User

from hs_core import hydroshare
from hs_core.hydroshare import utils, resource
from hs_core.models import BaseResource, CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_app_timeseries.models import TimeSeriesResource, Site, Variable, Method, ProcessingLevel, TimeSeriesResult


class TestTimeSeriesMetaData(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestTimeSeriesMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='Test Time Series Resource'
        )

    def tearDown(self):
        super(TestTimeSeriesMetaData, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Creator.objects.all().delete()
        Contributor.objects.all().delete()
        CoreMetaData.objects.all().delete()
        Coverage.objects.all().delete()
        Rights.objects.all().delete()
        Title.objects.all().delete()
        Publisher.objects.all().delete()
        Description.objects.all().delete()
        Relation.objects.all().delete()
        Subject.objects.all().delete()
        Source.objects.all().delete()
        Identifier.objects.all().delete()
        Type.objects.all().delete()
        Format.objects.all().delete()
        Date.objects.all().delete()
        Language.objects.all().delete()
        Variable.objects.all().delete()
        Site.objects.all().delete()
        Method.objects.all().delete()
        ProcessingLevel.objects.all().delete()
        TimeSeriesResult.objects.all().delete()

    def test_allowed_file_types(self):
        # test allowed file type is '.sqlite'
        self.assertIn('.sqlite', TimeSeriesResource.get_supported_upload_file_types())
        self.assertEquals(len(TimeSeriesResource.get_supported_upload_file_types()), 1)

        # there should not be any content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 0)

        files = []
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()
        files.append(UploadedFile(file=open(original_file_name, 'r'), name=original_file_name))

        # trying to add a test file to this resource should raise exception
        with self.assertRaises(Exception):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add sqlite file should pass the file add pre process check
        original_file_name = 'ODM2.sqlite'
        original_file = open(original_file_name, 'w')
        original_file.close()
        files = []
        files.append(UploadedFile(file=open(original_file_name, 'r'), name=original_file_name))
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        # should raise file validation error even thought the file gets added to the resource
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        # there should 1 content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

        # file pre add process should raise validation error if we try to add a 2nd file when the resource has
        # already one content file
        with self.assertRaises(ValidationError):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                                extract_metadata=False)

        # delete the content file
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, original_file_name, self.user)

        # there should no content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 0)

        # use a valid ODM2 sqlite which should pass the file pre add check post add check
        odm2_sqlite_file = 'hs_app_timeseries/tests/ODM2_8_19_2015.sqlite'
        files = []
        files.append(UploadedFile(file=open(odm2_sqlite_file, 'r'), name='ODM2_8_19_2015.sqlite'))
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

    def test_extracted_metadata(self):
        # test the core metadata at this point
        self.assertEquals(self.resTimeSeries.metadata.title.value, 'Test Time Series Resource')

        # there shouldn't any abstract element
        self.assertEquals(self.resTimeSeries.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resTimeSeries.metadata.subjects.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resTimeSeries.metadata.site, None)
        self.assertEquals(self.resTimeSeries.metadata.variable, None)
        self.assertEquals(self.resTimeSeries.metadata.method, None)
        self.assertEquals(self.resTimeSeries.metadata.processing_level, None)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result, None)

        # adding a valid ODM2 sqlite file should generate some core metadata and all extended metadata
        files = []
        odm2_sqlite_file = 'hs_app_timeseries/tests/ODM2_8_19_2015.sqlite'
        files.append(UploadedFile(file=open(odm2_sqlite_file, 'r'), name='ODM2_8_19_2015.sqlite'))
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # there should one content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

        # test core metadata after metadata extraction
        extracted_title = "Water temperature in the Little Bear River at Mendon Road near Mendon, UT"
        self.assertEquals(self.resTimeSeries.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEquals(self.resTimeSeries.metadata.description, None)
        extracted_abstract = "This dataset contains observations of water temperature in the Little Bear River at " \
                             "Mendon Road near Mendon, UT. Data were recorded every 30 minutes. The values were " \
                             "recorded using a HydroLab MS5 multi-parameter water quality sonde connected to a " \
                             "Campbell Scientific datalogger. Values represent quality controlled data that have " \
                             "undergone quality control to remove obviously bad data."
        self.assertEquals(self.resTimeSeries.metadata.description.abstract, extracted_abstract)

        # there should be 2 coverage element -  point type and period type
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='point').count(), 1)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='period').count(), 1)

        point_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='point').first()
        self.assertEquals(point_coverage.value['projection'], 'Unknown')
        self.assertEquals(point_coverage.value['units'], 'Decimal degrees')
        self.assertEquals(point_coverage.value['east'], -111.946402)
        self.assertEquals(point_coverage.value['north'], 41.718473)

        temporal_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='period').first()
        self.assertEquals(parser.parse(temporal_coverage.value['start']).date(), parser.parse('01/01/2008').date())
        self.assertEquals(parser.parse(temporal_coverage.value['end']).date(), parser.parse('01/31/2008').date())

        # there should be one format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 1)
        format_element = self.resTimeSeries.metadata.formats.all().first()
        self.assertEquals(format_element.value, 'application/sqlite')

        # there should be one subject element
        self.assertEquals(self.resTimeSeries.metadata.subjects.all().count(), 1)
        subj_element = self.resTimeSeries.metadata.subjects.all().first()
        self.assertEquals(subj_element.value, 'Temperature')

        # testing extended metadata elements
        self.assertNotEquals(self.resTimeSeries.metadata.site, None)
        self.assertEquals(self.resTimeSeries.metadata.site.site_code, 'USU-LBR-Mendon')
        site_name = 'Little Bear River at Mendon Road near Mendon, Utah'
        self.assertEquals(self.resTimeSeries.metadata.site.site_name, site_name)
        self.assertEquals(self.resTimeSeries.metadata.site.elevation_m, 1345)
        self.assertEquals(self.resTimeSeries.metadata.site.elevation_datum, 'NGVD29')
        self.assertEquals(self.resTimeSeries.metadata.site.site_type, 'Stream')

        self.assertNotEquals(self.resTimeSeries.metadata.variable, None)
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_code, 'USU36')
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_name, 'Temperature')
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_type, 'Water Quality')
        self.assertEquals(self.resTimeSeries.metadata.variable.no_data_value, -9999)
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_definition, None)
        self.assertEquals(self.resTimeSeries.metadata.variable.speciation, 'Not Applicable')

        self.assertNotEquals(self.resTimeSeries.metadata.method, None)
        self.assertEquals(self.resTimeSeries.metadata.method.method_code, 28)
        method_name = 'Quality Control Level 1 Data Series created from raw QC Level 0 data using ODM Tools.'
        self.assertEquals(self.resTimeSeries.metadata.method.method_name, method_name)
        self.assertEquals(self.resTimeSeries.metadata.method.method_type, 'Instrument deployment')
        method_des = 'Quality Control Level 1 Data Series created from raw QC Level 0 data using ODM Tools.'
        self.assertEquals(self.resTimeSeries.metadata.method.method_description, method_des)
        self.assertEquals(self.resTimeSeries.metadata.method.method_link, None)

        self.assertNotEquals(self.resTimeSeries.metadata.processing_level, None)
        self.assertEquals(self.resTimeSeries.metadata.processing_level.processing_level_code, 1)
        self.assertEquals(self.resTimeSeries.metadata.processing_level.definition, 'Quality controlled data')
        explanation = 'Quality controlled data that have passed quality assurance procedures such as ' \
                      'routine estimation of timing and sensor calibration or visual inspection and removal ' \
                      'of obvious errors. An example is USGS published streamflow records following parsing ' \
                      'through USGS quality control procedures.'
        self.assertEquals(self.resTimeSeries.metadata.processing_level.explanation, explanation)

        self.assertNotEquals(self.resTimeSeries.metadata.time_series_result, None)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_type, 'Temperature')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_name, 'degree celsius')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_abbreviation, 'degC')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.status, 'Unknown')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.sample_medium, 'Surface Water')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.value_count, 1441)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.aggregation_statistics, 'Average')

    @unittest.skip
    def test_metadata(self):
        # add a type element
        resource.create_metadata_element(self.resTimeSeries.short_id, 'type', url="http://hydroshare.org/netcdf")

        # add another creator with all sub_elements
        cr_name = 'Mike Sundar'
        cr_des = 'http://hydroshare.org/user/001'
        cr_org = "USU"
        cr_email = 'mike.sundar@usu.edu'
        cr_address = "11 River Drive, Logan UT-84321, USA"
        cr_phone = '435-567-0989'
        cr_homepage = 'http://usu.edu/homepage/001'
        cr_res_id = 'http://research.org/001'
        cr_res_gate_id = 'http://research-gate.org/001'
        resource.create_metadata_element(self.resTimeSeries.short_id,'creator',
                                         name=cr_name,
                                         description=cr_des,
                                         organization=cr_org,
                                         email=cr_email,
                                         address=cr_address,
                                         phone=cr_phone,
                                         homepage=cr_homepage,
                                         researcherID=cr_res_id,
                                         researchGateID=cr_res_gate_id)

        # add another creator with only the name
        resource.create_metadata_element(self.resTimeSeries.short_id, 'creator', name='Lisa Holley')

        #test adding a contributor with all sub_elements
        con_name = 'Sujan Peterson'
        con_des = 'http://hydroshare.org/user/002'
        con_org = "USU"
        con_email = 'sujan.peterson@usu.edu'
        con_address = "101 Center St, Logan UT-84321, USA"
        con_phone = '435-567-3245'
        con_homepage = 'http://usu.edu/homepage/009'
        con_res_id = 'http://research.org/009'
        con_res_gate_id = 'http://research-gate.org/009'
        resource.create_metadata_element(self.resTimeSeries.short_id,'contributor',
                                         name=con_name,
                                         description=con_des,
                                         organization=con_org,
                                         email=con_email,
                                         address=con_address,
                                         phone=con_phone,
                                         homepage=con_homepage,
                                         researcherID=con_res_id,
                                         researchGateID=con_res_gate_id)

        # add another creator with only the name
        resource.create_metadata_element(self.resTimeSeries.short_id, 'contributor', name='Andrew Smith')

        # add a period type coverage
        # add a period type coverage
        value_dict = {'name': 'Name for period coverage' , 'start': '1/1/2000', 'end': '12/12/2012'}
        resource.create_metadata_element(self.resTimeSeries.short_id,'coverage', type='period', value=value_dict)

        # add a point type coverage
        value_dict = {'name': 'Name for point coverage', 'east':'56.45678', 'north':'12.6789'}
        resource.create_metadata_element(self.resTimeSeries.short_id,'coverage', type='point', value=value_dict)

        # add date of type 'valid'
        resource.create_metadata_element(self.resTimeSeries.short_id,'date', type='valid', start_date='8/10/2011', end_date='8/11/2012')

        # add a format element
        format_nc = 'netcdf'
        resource.create_metadata_element(self.resTimeSeries.short_id,'format', value=format_nc)

        # add 'DOI' identifier
        #resource.create_metadata_element(self.resTimeSeries.short_id,'identifier', name='DOI', url="http://dx.doi.org/001")

        # add a language element
        resource.create_metadata_element(self.resTimeSeries.short_id,'language', code='eng')

        # add 'Publisher' element
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        hydroshare.add_resource_files(self.resTimeSeries.short_id, original_file)
        resource.create_metadata_element(self.resTimeSeries.short_id,'publisher', name="HydroShare", url="http://hydroshare.org")

        # add a relation element of uri type
        resource.create_metadata_element(self.resTimeSeries.short_id,'relation', type='isPartOf',
                                         value='http://hydroshare.org/resource/001')

        # add another relation element of non-uri type
        resource.create_metadata_element(self.resTimeSeries.short_id,'relation', type='isDataFor',
                                         value='This resource is for another resource')


        # add a source element of uri type
        resource.create_metadata_element(self.resTimeSeries.short_id,'source', derived_from='http://hydroshare.org/resource/0002')

        # add a rights element
        resource.create_metadata_element(self.resTimeSeries.short_id,'rights', statement='This is the rights statement for this resource',
                                         url='http://rights.ord/001')

        # add a subject element
        resource.create_metadata_element(self.resTimeSeries.short_id,'subject', value='sub-1')

        # add another subject element
        resource.create_metadata_element(self.resTimeSeries.short_id,'subject', value='sub-2')


        # add time series specific metadata elements
        self.resTimeSeries.metadata.create_element('site', site_code='LR_WaterLab_AA',
                                                   site_name='Logan River at the Utah Water Research Laboratory '
                                                             'west bridge', elevation_m=1414, elevation_datum='EGM96',
                                                   site_type='Stream')

        self.resTimeSeries.metadata.create_element('variable', variable_code='ODO', variable_name='Oxygen, dissolved',
                                                   variable_type='Concentration', no_data_value=-9999,
                                                   variable_definition='Concentration of oxygen gas dissolved in water.',
                                                   speciation='Not Applicable')

        self.resTimeSeries.metadata.create_element('method', method_code=59, method_name='Optical DO',
                                                   method_type='Instrument deployment',
                                                   method_description='Dissolved oxygen concentration measured '
                                                                      'optically using a YSI EXO multi-parameter water '
                                                                      'quality sonde.', method_link='http://www.exowater.com')

        exp_text = """Raw and unprocessed data and data products that have not undergone quality control.
        Depending on the variable, data type, and data transmission system, raw data may be available within seconds
        or minutes after the measurements have been made. Examples include real time precipitation, streamflow and
        water quality measurements."""
        self.resTimeSeries.metadata.create_element('processinglevel', processing_level_code=0, definition='Raw data',
                                                   explanation=exp_text)

        self.resTimeSeries.metadata.create_element('timeseriesresult', units_type='Concentration',
                                                   units_name='milligrams per liter', units_abbreviation='mg/L',
                                                   status='Complete', sample_medium='Surface water', value_count=11283,
                                                   aggregation_statistics="Average")

        print self.resTimeSeries.metadata.get_xml()

        print(bad)
