from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    AbstractMetaDataElement

from hs_modelinstance.models import ModelInstanceMetaData, ModelOutput, ExecutedBy


def delete_if_empty(term_obj, non_standard_elements):
    all_blank = True
    for attr, val in vars(term_obj).iteritems():
        if attr in non_standard_elements and val != '':
            all_blank = False
            break
    if all_blank:
        term_obj.delete()


def uncouple(choices):
    uncoupled = [c[0] for c in choices]
    return uncoupled


def validate_choice(value, choices):
    choices = choices if isinstance(choices[0], basestring) else uncouple(choices)
    if isinstance(value, int):
        return value
    if 'Choose' in value:
        return ''
    if value and value not in choices:
        raise ValidationError('Invalid parameter: {} not in {}'.format(value, ", ".join(choices)))
    else:
        return value


class ModelOutput(ModelOutput):
    class Meta:
        proxy = True


class ExecutedBy(ExecutedBy):
    class Meta:
        proxy = True


# extended metadata elements for MODFLOW Model Instance resource type
class StudyArea(AbstractMetaDataElement):
    term = 'StudyArea'
    totalLength = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name='Total length in meters')
    totalWidth = models.CharField(max_length=100, null=True, blank=True,
                                  verbose_name='Total width in meters')
    maximumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Maximum elevation in meters')
    minimumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Minimum elevation in meters')

    def __unicode__(self):
        return self.totalLength

    class Meta:
        # StudyArea element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def update(cls, element_id, **kwargs):
        study_area = super(StudyArea, cls).update(element_id, **kwargs)
        delete_if_empty(study_area,
                        ['totalLength', 'totalWidth', 'maximumElevation', 'minimumElevation'])


class GridDimensions(AbstractMetaDataElement):
    term = 'GridDimensions'
    gridTypeChoices = (('Regular', 'Regular'), ('Irregular', 'Irregular'),)

    numberOfLayers = models.CharField(max_length=100, null=True, blank=True,
                                      verbose_name='Number of layers')
    typeOfRows = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True,
                                  verbose_name='Type of rows')
    numberOfRows = models.CharField(max_length=100, null=True, blank=True,
                                    verbose_name='Number of rows')
    typeOfColumns = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True,
                                     verbose_name='Type of columns')
    numberOfColumns = models.CharField(max_length=100, null=True, blank=True,
                                       verbose_name='Number of columns')

    def __unicode__(self):
        return self.numberOfLayers

    class Meta:
        # GridDimensions element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        grid_dimensions = super(GridDimensions, cls).create(**kwargs)
        return grid_dimensions

    @classmethod
    def update(cls, element_id, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        grid_dimensions = super(GridDimensions, cls).update(element_id, **kwargs)
        delete_if_empty(grid_dimensions,
                        ['numberOfLayers', 'typeOfRows', 'numberOfRows', 'typeOfColumns',
                         'numberOfColumns',
                         ])

    @classmethod
    def _validate_params(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if key == 'typeOfRows' or key == 'typeOfColumns':
                kwargs[key] = validate_choice(val, cls.gridTypeChoices)
        return kwargs


class StressPeriod(AbstractMetaDataElement):
    term = 'StressPeriod'
    stressPeriodTypeChoices = (('Steady', 'Steady'), ('Transient', 'Transient'),
                               ('Steady and Transient', 'Steady and Transient'),)
    transientStateValueTypeChoices = (('Annually', 'Annually'), ('Monthly', 'Monthly'),
                                      ('Daily', 'Daily'), ('Hourly', 'Hourly'), ('Other', 'Other'),)

    stressPeriodType = models.CharField(max_length=100,
                                        choices=stressPeriodTypeChoices, null=True, blank=True,
                                        verbose_name='Type')
    steadyStateValue = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Length of steady state stress period(s)')
    transientStateValueType = \
        models.CharField(max_length=100,
                         choices=transientStateValueTypeChoices,
                         null=True,
                         verbose_name='Type of transient state stress period(s)')
    transientStateValue = \
        models.CharField(max_length=100,
                         null=True,
                         blank=True,
                         verbose_name='Length of transient state stress period(s)')

    def __unicode__(self):
        return self.stressPeriodType

    class Meta:
        # StressPeriod element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        stress_period = super(StressPeriod, cls).create(**kwargs)
        return stress_period

    @classmethod
    def update(cls, element_id, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        stress_period = super(StressPeriod, cls).update(element_id, **kwargs)
        delete_if_empty(stress_period,
                        ['stressPeriodType', 'steadyStateValue']
                        )

    @classmethod
    def _validate_params(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if key == 'stressPeriodType':
                kwargs[key] = validate_choice(val, cls.stressPeriodTypeChoices)
            elif key == 'transientStateValueType':
                kwargs[key] = validate_choice(val, cls.transientStateValueTypeChoices)
        return kwargs


class GroundWaterFlow(AbstractMetaDataElement):
    term = 'GroundWaterFlow'
    flowPackageChoices = (('BCF6', 'BCF6'), ('LPF', 'LPF'), ('HUF2', 'HUF2'), ('UPW', 'UPW'),)
    flowParameterChoices = (('Hydraulic Conductivity', 'Hydraulic Conductivity'),
                            ('Transmissivity', 'Transmissivity'),)

    flowPackage = models.CharField(max_length=100, choices=flowPackageChoices, null=True,
                                   blank=True, verbose_name='Flow package')
    unsaturatedZonePackage = models.BooleanField(default=False, verbose_name='Includes UZF package')
    horizontalFlowBarrierPackage = models.BooleanField(default=False,
                                                       verbose_name='Includes HFB6 package')
    seawaterIntrusionPackage = models.BooleanField(default=False,
                                                   verbose_name='Includes SWI2 package')
    flowParameter = models.CharField(max_length=100, choices=flowParameterChoices, null=True,
                                     blank=True, verbose_name='Flow parameter')

    def __unicode__(self):
        return self.flowPackage

    class Meta:
        # GroundWaterFlow element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        gw_flow = super(GroundWaterFlow, cls).create(**kwargs)
        return gw_flow

    @classmethod
    def update(cls, element_id, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        gw_flow = super(GroundWaterFlow, cls).update(element_id, **kwargs)
        delete_if_empty(gw_flow,
                        ['flowPackage', 'flowParameter'])

    @classmethod
    def _validate_params(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if key == 'flowPackage':
                kwargs[key] = validate_choice(val, cls.flowPackageChoices)
            elif key == 'flowParameter':
                kwargs[key] = validate_choice(val, cls.flowParameterChoices)
        return kwargs

    @property
    def includesUnsaturatedZonePackage(self):
        if self.unsaturatedZonePackage:
            return "Yes"
        else:
            return "No"

    @property
    def includesHorizontalFlowBarrierPackage(self):
        if self.horizontalFlowBarrierPackage:
            return "Yes"
        else:
            return "No"

    @property
    def includesSeawaterIntrusionPackage(self):
        if self.seawaterIntrusionPackage:
            return "Yes"
        else:
            return "No"


class AbstractChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.description

    class Meta:
        abstract = True


class SpecifiedHeadBoundaryPackageChoices(AbstractChoices):
    pass


class SpecifiedFluxBoundaryPackageChoices(AbstractChoices):
    pass


class HeadDependentFluxBoundaryPackageChoices(AbstractChoices):
    pass


class BoundaryCondition(AbstractMetaDataElement):
    term = 'BoundaryCondition'
    specifiedHeadBoundaryPackageChoices = (('BFH', 'BFH'), ('CHD', 'CHD'), ('FHB', 'FHB'),)
    specifiedFluxBoundaryPackageChoices = (('FHB', 'FHB'), ('RCH', 'RCH'), ('WEL', 'WEL'),)
    headDependentFluxBoundaryPackageChoices = (('DAF', 'DAF'), ('DAFG', 'DAFG'), ('DRN', 'DRN'),
                                               ('DRT', 'DRT'), ('ETS', 'ETS'), ('EVT', 'EVT'),
                                               ('GHB', 'GHB'), ('LAK', 'LAK'), ('MNW1', 'MNW1'),
                                               ('MNW2', 'MNW2'), ('RES', 'RES'), ('RIP', 'RIP'),
                                               ('RIV', 'RIV'), ('SFR', 'SFR'), ('STR', 'STR'),
                                               ('UZF', 'UZF'),)
    specified_head_boundary_packages = models.ManyToManyField(SpecifiedHeadBoundaryPackageChoices,
                                                              blank=True)
    other_specified_head_boundary_packages = models.CharField(max_length=200, null=True, blank=True,
                                                              verbose_name='Other packages')
    specified_flux_boundary_packages = models.ManyToManyField(SpecifiedFluxBoundaryPackageChoices,
                                                              blank=True)
    other_specified_flux_boundary_packages = models.CharField(max_length=200, null=True, blank=True,
                                                              verbose_name='Other packages')
    head_dependent_flux_boundary_packages = models.ManyToManyField(
        HeadDependentFluxBoundaryPackageChoices, blank=True)
    other_head_dependent_flux_boundary_packages = models.CharField(max_length=200, null=True,
                                                                   blank=True,
                                                                   verbose_name='Other packages')

    # may be this could cause a problem
    def __unicode__(self):
        return self.term

    class Meta:
        # BoundaryCondition element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_specified_head_boundary_packages(self):
        return ', '.join([types.description for types in
                          self.specified_head_boundary_packages.all()])

    def get_specified_flux_boundary_packages(self):
        return ', '.join([packages.description for packages in
                          self.specified_flux_boundary_packages.all()])

    def get_head_dependent_flux_boundary_packages(self):
        return ', '.join([packages.description for packages in
                          self.head_dependent_flux_boundary_packages.all()])

    def _add_specified_head_boundary_packages(self, packages):
        """ there are two possibilities for package values: list of string (during normal create or
         update) or integer (during creating new version of the resource)"""
        for package in packages:
            if isinstance(package, int):
                qs = SpecifiedHeadBoundaryPackageChoices.objects.filter(id=package)
            else:
                qs = SpecifiedHeadBoundaryPackageChoices.objects.filter(description__exact=package)
            if qs.exists():
                self.specified_head_boundary_packages.add(qs[0])
            else:
                if isinstance(package, basestring):
                    self.specified_head_boundary_packages.create(description=package)

    def _add_specified_flux_boundary_packages(self, packages):
        """ there are two possibilities for package values: list of string (during normal create or
         update) or integer (during creating new version of the resource)"""
        for package in packages:
            if isinstance(package, int):
                qs = SpecifiedFluxBoundaryPackageChoices.objects.filter(id=package)
            else:
                qs = SpecifiedFluxBoundaryPackageChoices.objects.filter(description__exact=package)
            if qs.exists():
                self.specified_flux_boundary_packages.add(qs[0])
            else:
                if isinstance(package, basestring):
                    self.specified_flux_boundary_packages.create(description=package)

    def _add_head_dependent_flux_boundary_packages(self, packages):
        """ there are two possibilities for package values: list of string (during normal create or
         update) or integer (during creating new version of the resource)"""
        for package in packages:
            if isinstance(package, int):
                qs = HeadDependentFluxBoundaryPackageChoices.objects.filter(id=package)
            else:
                qs = HeadDependentFluxBoundaryPackageChoices.objects.\
                    filter(description__exact=package)
            if qs.exists():
                self.head_dependent_flux_boundary_packages.add(qs[0])
            else:
                if isinstance(package, basestring):
                    self.head_dependent_flux_boundary_packages.create(description=package)

    # need to define create and update methods
    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        model_boundary_condition = super(BoundaryCondition, cls).create(
            content_object=kwargs['content_object'],
            other_specified_head_boundary_packages=kwargs.get(
                'other_specified_head_boundary_packages', ''),
            other_specified_flux_boundary_packages=kwargs.get(
                'other_specified_flux_boundary_packages', ''),
            other_head_dependent_flux_boundary_packages=kwargs.get(
                'other_head_dependent_flux_boundary_packages', '')
                    )
        if kwargs.get('specified_head_boundary_packages', None):
            model_boundary_condition._add_specified_head_boundary_packages(
                kwargs['specified_head_boundary_packages'])
        if kwargs.get('specified_flux_boundary_packages', None):
            model_boundary_condition._add_specified_flux_boundary_packages(
                kwargs['specified_flux_boundary_packages'])
        if kwargs.get('head_dependent_flux_boundary_packages', None):
            model_boundary_condition._add_head_dependent_flux_boundary_packages(
                kwargs['head_dependent_flux_boundary_packages'])

        return model_boundary_condition

    @classmethod
    def update(cls, element_id, **kwargs):
        model_boundary_condition = BoundaryCondition.objects.get(id=element_id)
        kwargs = cls._validate_params(**kwargs)
        if model_boundary_condition:
            if 'specified_head_boundary_packages' in kwargs:
                model_boundary_condition.specified_head_boundary_packages.clear()
                cls._add_specified_head_boundary_packages(model_boundary_condition,
                                                          kwargs[
                                                              'specified_head_boundary_packages'
                                                          ])

            if 'specified_flux_boundary_packages' in kwargs:
                model_boundary_condition.specified_flux_boundary_packages.clear()
                cls._add_specified_flux_boundary_packages(model_boundary_condition,
                                                          kwargs[
                                                              'specified_flux_boundary_packages'
                                                          ])

            if 'head_dependent_flux_boundary_packages' in kwargs:
                model_boundary_condition.head_dependent_flux_boundary_packages.clear()
                cls._add_head_dependent_flux_boundary_packages(
                    model_boundary_condition,
                    kwargs['head_dependent_flux_boundary_packages'])

            if 'other_specified_head_boundary_packages' in kwargs:
                model_boundary_condition.other_specified_head_boundary_packages = \
                    kwargs['other_specified_head_boundary_packages']
            if 'other_specified_flux_boundary_packages' in kwargs:
                model_boundary_condition.other_specified_flux_boundary_packages = \
                    kwargs['other_specified_flux_boundary_packages']
            if 'other_head_dependent_flux_boundary_packages' in kwargs:
                model_boundary_condition.other_head_dependent_flux_boundary_packages = \
                    kwargs['other_head_dependent_flux_boundary_packages']

            model_boundary_condition.save()
            num_sp_hd_bdy_pckgs = \
                len(model_boundary_condition.get_specified_head_boundary_packages())
            num_sp_fx_bdy_pckgs = \
                len(model_boundary_condition.get_specified_flux_boundary_packages())
            num_hd_dp_bdy_pckgs = \
                len(model_boundary_condition.get_head_dependent_flux_boundary_packages())
            if num_hd_dp_bdy_pckgs + num_sp_fx_bdy_pckgs + num_sp_hd_bdy_pckgs == 0:
                delete_if_empty(model_boundary_condition,
                                ['specified_head_boundary_packages',
                                 'specified_flux_boundary_packages',
                                 'head_dependent_flux_boundary_packages',
                                 'other_specified_head_boundary_packages',
                                 'other_specified_flux_boundary_packages',
                                 'other_head_dependent_flux_boundary_packages'
                                 ])

        else:
            raise ObjectDoesNotExist(
                "No BoundaryCondition element was found for the provided id:%s" % kwargs['id']
            )

    @classmethod
    def _validate_params(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if key == 'specified_head_boundary_packages':
                kwargs[key] = [validate_choice(package, cls.specifiedHeadBoundaryPackageChoices)
                               for package in kwargs[key]]
            elif key == 'specified_flux_boundary_packages':
                kwargs[key] = [validate_choice(package, cls.specifiedFluxBoundaryPackageChoices)
                               for package in kwargs[key]]
            elif key == 'head_dependent_flux_boundary_packages':
                kwargs[key] = [validate_choice(package, cls.headDependentFluxBoundaryPackageChoices)
                               for package in kwargs[key]]
        return kwargs


class ModelCalibration(AbstractMetaDataElement):
    term = 'ModelCalibration'
    observationProcessPackageChoices = (('ADV2', 'ADV2'), ('CHOB', 'CHOB'), ('DROB', 'DROB'),
                                        ('DTOB', 'DTOB'), ('GBOB', 'GBOB'), ('HOB', 'HOB'),
                                        ('OBS', 'OBS'), ('RVOB', 'RVOB'), ('STOB', 'STOB'),)

    calibratedParameter = models.CharField(max_length=200, null=True, blank=True,
                                           verbose_name='Calibrated parameter(s)')
    observationType = models.CharField(max_length=200, null=True, blank=True,
                                       verbose_name='Observation type(s)')
    observationProcessPackage = models.CharField(max_length=100,
                                                 choices=observationProcessPackageChoices,
                                                 null=True, blank=True,
                                                 verbose_name='Observation process package')
    calibrationMethod = models.CharField(max_length=200, null=True, blank=True,
                                         verbose_name='Calibration method(s)')

    def __unicode__(self):
        return self.calibratedParameter

    class Meta:
        # ModelCalibration element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        model_calibration = super(ModelCalibration, cls).create(**kwargs)
        return model_calibration

    @classmethod
    def update(cls, element_id, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        model_calibration = super(ModelCalibration, cls).update(element_id, **kwargs)
        delete_if_empty(model_calibration,
                        ['calibratedParameter',
                         'observationType',
                         'observationProcessPackage',
                         'calibrationMethod'
                         ])

    @classmethod
    def _validate_params(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if key == 'observationProcessPackage':
                kwargs[key] = validate_choice(val, cls.observationProcessPackageChoices)
        return kwargs


class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    inputType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Type')
    inputSourceName = models.CharField(max_length=200, null=True, blank=True,
                                       verbose_name='Source name')
    inputSourceURL = models.URLField(null=True, blank=True, verbose_name='Source URL')

    def __unicode__(self):
        return self.inputType


class OutputControlPackageChoices(AbstractChoices):
    pass


class GeneralElements(AbstractMetaDataElement):
    term = 'GeneralElements'
    modelSolverChoices = (('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'),
                          ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT'),)
    outputControlPackageChoices = (('GAGE', 'GAGE'), ('HYD', 'HYD'), ('LMT6', 'LMT6'),
                                   ('MNWI', 'MNWI'), ('OC', 'OC'),)
    subsidencePackageChoices = (('IBS', 'IBS'), ('SUB', 'SUB'), ('SWT', 'SWT'),)

    modelParameter = models.CharField(max_length=200, null=True, blank=True,
                                      verbose_name='Model parameter(s)')
    modelSolver = models.CharField(max_length=100, choices=modelSolverChoices, null=True,
                                   blank=True, verbose_name='Model solver')
    output_control_package = models.ManyToManyField(OutputControlPackageChoices, blank=True)
    subsidencePackage = models.CharField(max_length=100, choices=subsidencePackageChoices,
                                         null=True, blank=True, verbose_name='Subsidence package')

    def __unicode__(self):
        return self.modelParameter

    class Meta:
        # GeneralElements element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_output_control_package(self):
        return ', '.join([packages.description for packages in self.output_control_package.all()])

    def _add_output_control_package(self, choices):
        """ there are two possibilities for type_choices values: list of string (during normal
         create or update) or integer (during creating new version of the resource)"""
        for type_choices in choices:
            if isinstance(type_choices, int):
                qs = OutputControlPackageChoices.objects.filter(id=type_choices)
            else:
                qs = OutputControlPackageChoices.objects.filter(description__exact=type_choices)
            if qs.exists():
                self.output_control_package.add(qs[0])
            else:
                if isinstance(type_choices, basestring):
                    self.output_control_package.create(description=type_choices)

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_params(**kwargs)
        ocp = kwargs.pop('output_control_package', None)
        general_elements = super(GeneralElements, cls).create(**kwargs)
        if ocp:
            general_elements._add_output_control_package(ocp)

        return general_elements

    @classmethod
    def update(cls, element_id, **kwargs):
        general_elements = GeneralElements.objects.get(id=element_id)
        kwargs = cls._validate_params(**kwargs)
        if general_elements:
            ocp = kwargs.pop('output_control_package', None)
            general_elements = super(GeneralElements, cls).update(element_id, **kwargs)

            if ocp is not None:
                general_elements.output_control_package.clear()
                general_elements._add_output_control_package(ocp)

            general_elements.save()
            if len(general_elements.get_output_control_package()) == 0:
                delete_if_empty(general_elements,
                                ['modelParameter', 'modelSolver', 'subsidencePackage',
                                 'output_control_package'])

    @classmethod
    def _validate_params(cls, **kwargs):
        # raise Exception(kwargs)
        for key, val in kwargs.iteritems():
            if key == 'modelSolver':
                kwargs[key] = validate_choice(val, cls.modelSolverChoices)
            elif key == 'output_control_package':
                kwargs[key] = [validate_choice(package, cls.outputControlPackageChoices) for package
                               in kwargs[key]]
            elif key == 'subsidencePackage':
                kwargs[key] = validate_choice(val, cls.subsidencePackageChoices)
        return kwargs


# MODFLOW Model Instance Resource type
class MODFLOWModelInstanceResource(BaseResource):
    objects = ResourceManager("MODFLOWModelInstanceResource")

    discovery_content_type = 'MODFLOW Model Instance'  # used during discovery

    class Meta:
        verbose_name = 'MODFLOW Model Instance Resource'
        proxy = True

    @classmethod
    def get_metadata_class(cls):
        return MODFLOWModelInstanceMetaData

    def check_content_files(self):
        """
        like 'has_required_content_files()' this method checks that one and only of .nam or .mfn
         exists, but unlike 'has_required_content_files()' this method returns which files are
         missing so that more information can be returned to the user via the interface
        :return: -['.nam or .mfn'] if there are no files or if there are files but no .nam or .mfn
                    file
                 -'multiple_nam' if more than one .nam file has been uploaded
                 -missing_files, a list of file names that are included in the .nam file but have
                 not been uploaded by the user
        """
        missing_files = []
        if self.files.all().count() >= 1:
            nam_files, reqd_files, existing_files, model_packages = self.find_content_files()
            if not nam_files:
                return ['.nam or .mfn']
            else:
                if nam_files > 1:
                    return 'multiple_nam'
                else:
                    for f in reqd_files:
                        if f not in existing_files:
                            missing_files.append(f)
                    return missing_files
        else:
            return ['.nam or .mfn ']

    def find_content_files(self):
        """
        loops through uploaded files to count the .nam and/or .mfn files, creates a list of required
         files (file names listed in the .nam or .mfn file needed to run the model), and a list of
         existing file names
        :return: -nam_file_count, (int), the number of .nam files uploaded
                 -reqd_files, (list of strings), the files listed in the .nam file that should be
                 included for the model to run
                 -existing_files, (list of strings), the names of files that have been uploaded
                 -model packages (list of strings), the names of the packages for the uploaded model
                 found in the .nam or .mfn file. These are the entries in the far left column of the
                 .nam or .mfn file.
        """
        nam_file_count = 0
        existing_files = []
        reqd_files = []
        model_packages = []
        for res_file in self.files.all():
                ext = res_file.extension
                existing_files.append(res_file.file_name)
                if ext == '.nam' or ext == '.mfn':
                    nam_file_count += 1
                    name_file = res_file.resource_file.file
                    for row in name_file:
                        row = row.strip()
                        row = row.replace("'", "")
                        row = row.replace('"', "")
                        row = row.split(" ")
                        r = row[0].strip()
                        if not r.startswith('#') and r != '' and r.lower() != 'list' \
                                and r.lower() != 'data' and r.lower() != 'data(binary)':
                            reqd_file = row[-1].strip()
                            reqd_files.append(reqd_file)
                            model_package_name = row[0].strip()
                            model_package_ext = reqd_file.split('.')[-1].upper()
                            model_packages.extend(set([model_package_name, model_package_ext]))
        return nam_file_count, reqd_files, existing_files, model_packages


processor_for(MODFLOWModelInstanceResource)(resource_processor)


# metadata container class
class MODFLOWModelInstanceMetaData(ModelInstanceMetaData):
    _study_area = GenericRelation(StudyArea)
    _grid_dimensions = GenericRelation(GridDimensions)
    _stress_period = GenericRelation(StressPeriod)
    _ground_water_flow = GenericRelation(GroundWaterFlow)
    _boundary_condition = GenericRelation(BoundaryCondition)
    _model_calibration = GenericRelation(ModelCalibration)
    _model_input = GenericRelation(ModelInput)
    _general_elements = GenericRelation(GeneralElements)

    @property
    def resource(self):
        return MODFLOWModelInstanceResource.objects.filter(object_id=self.id).first()

    @property
    def study_area(self):
        return self._study_area.all().first()

    @property
    def grid_dimensions(self):
        return self._grid_dimensions.all().first()

    @property
    def stress_period(self):
        return self._stress_period.all().first()

    @property
    def ground_water_flow(self):
        return self._ground_water_flow.all().first()

    @property
    def boundary_condition(self):
        return self._boundary_condition.all().first()

    @property
    def model_calibration(self):
        return self._model_calibration.all().first()

    @property
    def model_inputs(self):
        return self._model_input.all()

    @property
    def general_elements(self):
        return self._general_elements.all().first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import MODFLOWModelInstanceMetaDataSerializer
        return MODFLOWModelInstanceMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        ModelInstanceMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'studyarea' in keys_to_update:
            parsed_metadata.append({"studyarea": metadata.pop('studyarea')})

        if 'griddimensions' in keys_to_update:
            parsed_metadata.append({"griddimensions": metadata.pop('griddimensions')})

        if 'stressperiod' in keys_to_update:
            parsed_metadata.append({"stressperiod": metadata.pop('stressperiod')})

        if 'groundwaterflow' in keys_to_update:
            parsed_metadata.append({"groundwaterflow": metadata.pop('groundwaterflow')})

        if 'boundarycondition' in keys_to_update:
            parsed_metadata.append({"boundarycondition": metadata.pop('boundarycondition')})

        if 'modelcalibration' in keys_to_update:
            parsed_metadata.append({"modelcalibration": metadata.pop('modelcalibration')})

        if 'generalelements' in keys_to_update:
            parsed_metadata.append({"generalelements": metadata.pop('generalelements')})

        if 'modelinputs' in keys_to_update:
            for modelinput in metadata.pop('modelinputs'):
                parsed_metadata.append({"modelinput": modelinput})

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(MODFLOWModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('StudyArea')
        elements.append('GridDimensions')
        elements.append('StressPeriod')
        elements.append('GroundWaterFlow')
        elements.append('BoundaryCondition')
        elements.append('ModelCalibration')
        elements.append('ModelInput')
        elements.append('GeneralElements')
        return elements

    def update(self, metadata, user):
        # overriding the base class update method
        from forms import StudyAreaValidationForm, GridDimensionsValidationForm, \
            StressPeriodValidationForm, GroundWaterFlowValidationForm, \
            BoundaryConditionValidationForm, ModelCalibrationValidationForm, \
            GeneralElementsValidationForm, ModelOutputValidationForm, ExecutedByValidationForm, \
            ModelInputValidationForm

        super(MODFLOWModelInstanceMetaData, self).update(metadata, user)
        attribute_mappings = {'studyarea': 'study_area',
                              'griddimensions': 'grid_dimensions',
                              'stressperiod': 'stress_period',
                              'groundwaterflow': 'ground_water_flow',
                              'boundarycondition': 'boundary_condition',
                              'modelcalibration': 'model_calibration',
                              'generalelements': 'general_elements',
                              'modeloutput': 'model_output', 'executedby': 'executed_by'}

        validation_forms_mapping = {'studyarea': StudyAreaValidationForm,
                                    'griddimensions': GridDimensionsValidationForm,
                                    'stressperiod': StressPeriodValidationForm,
                                    'groundwaterflow': GroundWaterFlowValidationForm,
                                    'boundarycondition': BoundaryConditionValidationForm,
                                    'modelcalibration': ModelCalibrationValidationForm,
                                    'generalelements': GeneralElementsValidationForm,
                                    'modeloutput': ModelOutputValidationForm,
                                    'executedby': ExecutedByValidationForm}

        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in attribute_mappings.keys():
                for dict_item in metadata:
                    if element_name in dict_item:
                        validation_form = validation_forms_mapping[element_name](
                            dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                        element_property_name = attribute_mappings[element_name]
                        self.update_non_repeatable_element(element_name, metadata,
                                                           element_property_name)

            # update possibly only one repeatable element 'modelinput'
            element_name = 'modelinput'
            for dict_item in metadata:
                if element_name in dict_item:
                    validation_form = ModelInputValidationForm(dict_item[element_name])
                    if not validation_form.is_valid():
                        err_string = self.get_form_errors_as_string(validation_form)
                        raise ValidationError(err_string)
            self.update_repeatable_element(element_name=element_name, metadata=metadata,
                                           property_name='model_inputs')

    def get_xml(self, pretty_print=True, include_format_elements=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(MODFLOWModelInstanceMetaData, self).get_xml(pretty_print=pretty_print)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.study_area:
            studyAreaFields = ['totalLength', 'totalWidth', 'maximumElevation', 'minimumElevation']
            self.add_metadata_element_to_xml(container, self.study_area, studyAreaFields)

        if self.grid_dimensions:
            gridDimensionsFields = ['numberOfLayers', 'typeOfRows', 'numberOfRows', 'typeOfColumns',
                                    'numberOfColumns']
            self.add_metadata_element_to_xml(container, self.grid_dimensions, gridDimensionsFields)

        if self.stress_period:
            stressPeriodFields = ['stressPeriodType', 'steadyStateValue',
                                  'transientStateValueType', 'transientStateValue']
            self.add_metadata_element_to_xml(container, self.stress_period, stressPeriodFields)

        if self.ground_water_flow:
            groundWaterFlowFields = ['flowPackage', 'includesUnsaturatedZonePackage',
                                     'includesHorizontalFlowBarrierPackage',
                                     'includesSeawaterIntrusionPackage', 'flowParameter']
            self.add_metadata_element_to_xml(container, self.ground_water_flow,
                                             groundWaterFlowFields)

        if self.boundary_condition:
            hsterms_boundary = etree.SubElement(container,
                                                '{%s}BoundaryCondition' %
                                                self.NAMESPACES['hsterms'])
            hsterms_boundary_rdf_Description = \
                etree.SubElement(hsterms_boundary, '{%s}Description' % self.NAMESPACES['rdf'])

            if self.boundary_condition.specified_head_boundary_packages:
                hsterms_boundary_package = \
                    etree.SubElement(hsterms_boundary_rdf_Description,
                                     '{%s}specifiedHeadBoundaryPackages' %
                                     self.NAMESPACES['hsterms'])
                if len(self.boundary_condition.get_specified_head_boundary_packages()) == 0 and \
                        self.boundary_condition.other_specified_head_boundary_packages:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.other_specified_head_boundary_packages
                elif len(self.boundary_condition.get_specified_head_boundary_packages()) != 0 and \
                        not self.boundary_condition.other_specified_head_boundary_packages:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.get_specified_head_boundary_packages()
                else:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.get_specified_head_boundary_packages() + ', ' +\
                            self.boundary_condition.other_specified_head_boundary_packages
            if self.boundary_condition.specified_flux_boundary_packages:
                hsterms_boundary_package = \
                    etree.SubElement(hsterms_boundary_rdf_Description,
                                     '{%s}specifiedFluxBoundaryPackages' %
                                     self.NAMESPACES['hsterms'])
                if len(self.boundary_condition.get_specified_flux_boundary_packages()) == 0 and \
                        self.boundary_condition.other_specified_flux_boundary_packages:
                    hsterms_boundary_package.text = \
                        self.boundary_condition.other_specified_flux_boundary_packages
                elif len(self.boundary_condition.get_specified_flux_boundary_packages()) != 0 and \
                        not self.boundary_condition.other_specified_flux_boundary_packages:
                    hsterms_boundary_package.text = \
                        self.boundary_condition.get_specified_flux_boundary_packages()
                else:
                    hsterms_boundary_package.text = \
                        self.boundary_condition.get_specified_flux_boundary_packages() + ', ' + \
                        self.boundary_condition.other_specified_flux_boundary_packages

            if self.boundary_condition.head_dependent_flux_boundary_packages:
                hsterms_boundary_package = \
                    etree.SubElement(hsterms_boundary_rdf_Description,
                                     '{%s}headDependentFluxBoundaryPackages' %
                                     self.NAMESPACES['hsterms'])
                if len(self.boundary_condition.get_head_dependent_flux_boundary_packages()) == 0 \
                        and self.boundary_condition.other_head_dependent_flux_boundary_packages:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.other_head_dependent_flux_boundary_packages
                elif len(self.boundary_condition.get_head_dependent_flux_boundary_packages()) != 0 \
                        and not self.boundary_condition.other_head_dependent_flux_boundary_packages:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.get_head_dependent_flux_boundary_packages()
                else:
                        hsterms_boundary_package.text = \
                            self.boundary_condition.get_head_dependent_flux_boundary_packages() + \
                            ', ' + \
                            self.boundary_condition.other_head_dependent_flux_boundary_packages

        if self.model_calibration:
            modelCalibrationFields = ['calibratedParameter', 'observationType',
                                      'observationProcessPackage', 'calibrationMethod']
            self.add_metadata_element_to_xml(container, self.model_calibration,
                                             modelCalibrationFields)

        if self.model_inputs:
            modelInputFields = ['inputType', 'inputSourceName', 'inputSourceURL']
            for model_input in self.model_inputs:
                self.add_metadata_element_to_xml(container, model_input, modelInputFields)

        if self.general_elements:

            if self.general_elements.modelParameter:
                model_parameter = etree.SubElement(container, '{%s}modelParameter' %
                                                   self.NAMESPACES['hsterms'])
                model_parameter.text = self.general_elements.modelParameter

            if self.general_elements.modelSolver:
                model_solver = etree.SubElement(container, '{%s}modelSolver' %
                                                self.NAMESPACES['hsterms'])
                model_solver.text = self.general_elements.modelSolver

            if self.general_elements.output_control_package:
                output_package = etree.SubElement(container, '{%s}outputControlPackage' %
                                                  self.NAMESPACES['hsterms'])
                output_package.text = self.general_elements.get_output_control_package()

            if self.general_elements.subsidencePackage:
                subsidence_package = etree.SubElement(container, '{%s}subsidencePackage' %
                                                      self.NAMESPACES['hsterms'])
                subsidence_package.text = self.general_elements.subsidencePackage

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def delete_all_elements(self):
        super(MODFLOWModelInstanceMetaData, self).delete_all_elements()
        self._study_area.all().delete()
        self._grid_dimensions.all().delete()
        self._stress_period.all().delete()
        self._ground_water_flow.all().delete()
        self._boundary_condition.all().delete()
        self._model_calibration.all().delete()
        self._model_input.all().delete()
        self._general_elements.all().delete()
