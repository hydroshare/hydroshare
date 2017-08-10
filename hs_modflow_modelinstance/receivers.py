from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from hs_core.hydroshare.hs_bagit import create_bag_files

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update, \
    pre_create_resource, post_metadata_element_update, post_add_files_to_resource, \
    post_create_resource


import hs_modflow_modelinstance.models as modflow_models

from hs_modflow_modelinstance.forms import ModelOutputValidationForm, ExecutedByValidationForm,\
    StudyAreaValidationForm, GridDimensionsValidationForm, StressPeriodValidationForm,\
    GroundWaterFlowValidationForm, BoundaryConditionValidationForm, ModelCalibrationValidationForm,\
    ModelInputValidationForm, GeneralElementsValidationForm


@receiver(pre_create_resource, sender=modflow_models.MODFLOWModelInstanceResource)
def modflowmodelinstance_pre_create_resource(sender, **kwargs):
    metadata = kwargs['metadata']
    modeloutput = {'modeloutput': {'includes_output': False}}
    metadata.append(modeloutput)


@receiver(pre_metadata_element_create, sender=modflow_models.MODFLOWModelInstanceResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    return _process_metadata_update_create(update_or_create='create', **kwargs)


@receiver(pre_metadata_element_update, sender=modflow_models.MODFLOWModelInstanceResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    return _process_metadata_update_create(update_or_create='update', **kwargs)


@receiver(post_metadata_element_update, sender=modflow_models.MODFLOWModelInstanceResource)
def check_element_exist(sender, **kwargs):
    element_id = kwargs['element_id']
    element_name = kwargs['element_name']
    element_exists = False
    class_names = vars(modflow_models)
    for class_name, cls in class_names.iteritems():
        if class_name.lower() == element_name.lower():
            try:
                cls.objects.get(pk=element_id)
                element_exists = True
            except ObjectDoesNotExist:
                break
    return {'element_exists': element_exists}


def _process_metadata_update_create(update_or_create, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "modeloutput":
        element_form = ModelOutputValidationForm(request.POST)
    elif element_name == 'executedby':
        element_form = ExecutedByValidationForm(request.POST)
    elif element_name == 'studyarea':
        element_form = StudyAreaValidationForm(request.POST)
    elif element_name == 'griddimensions':
        element_form = GridDimensionsValidationForm(request.POST)
    elif element_name == 'stressperiod':
        element_form = StressPeriodValidationForm(request.POST)
    elif element_name == 'groundwaterflow':
        element_form = GroundWaterFlowValidationForm(request.POST)
    elif element_name == 'boundarycondition':
        element_form = BoundaryConditionValidationForm(request.POST)
    elif element_name == 'modelcalibration':
        element_form = ModelCalibrationValidationForm(request.POST)
    elif element_name == 'modelinput':
        if update_or_create == 'update':
            # since modelinput is a repeatable element and modelinput data is displayed on the
            # landing page using formset, the data coming from a single modelinput form in the
            # request for update needs to be parsed to match with modelinput field names
            form_data = {}
            for field_name in ModelInputValidationForm().fields:
                matching_key = [key for key in request.POST if '-'+field_name in key][0]
                form_data[field_name] = request.POST[matching_key]

            element_form = ModelInputValidationForm(form_data)
        else:
            element_form = ModelInputValidationForm(request.POST)
    elif element_name == 'generalelements':
        element_form = GeneralElementsValidationForm(request.POST)
    else:
        raise Exception('Element name: "{}" is not supported by this resource type'.format(
            element_name
        ))

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(post_add_files_to_resource, sender=modflow_models.MODFLOWModelInstanceResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    add_metadata_from_file(resource)


@receiver(post_create_resource, sender=modflow_models.MODFLOWModelInstanceResource)
def post_create_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    add_metadata_from_file(resource)


def add_metadata_from_file(resource):
    # extract metadata from the just uploaded file
    res_files = resource.files.all()
    if res_files:
        process_package_info(resource)
        for f in res_files:
            if f.extension == '.dis':
                add_metadata_from_dis_file(f, resource)


def process_package_info(resource):
    # check if only one .nam file is uploaded
    nam_file_count, reqd_files, existing_files, packages = resource.find_content_files()
    if nam_file_count == 1:
        if packages:
            # make list for many to many relations so that more than one can be added
            output_control_package_list = []
            specified_head_boundary_package_list = []
            specified_flux_boundary_packages_list = []
            head_dependent_flux_boundary_packages = []

            # loop through packages from .nam file to see if they match any of the controlled terms
            if 'UZF' in packages:
                create_or_update_from_package(resource, modflow_models.GroundWaterFlow,
                                              unsaturatedZonePackage=True)
            if 'HFB6' in packages:
                create_or_update_from_package(resource, modflow_models.GroundWaterFlow,
                                              horizontalFlowBarrierPackage=True)
            if 'SWI2' in packages:
                create_or_update_from_package(resource, modflow_models.GroundWaterFlow,
                                              seawaterIntrusionPackage=True)
            for p in packages:
                # check each term
                # StressPeriod
                if p in modflow_models.uncouple(
                        modflow_models.StressPeriod.stressPeriodTypeChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.StressPeriod,
                                                  stressPeriodType=p)
                if p in modflow_models.uncouple(
                        modflow_models.StressPeriod.transientStateValueTypeChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.StressPeriod,
                                                  transientStateValueType=p)
                # GroundWaterFlow
                if p in modflow_models.uncouple(
                        modflow_models.GroundWaterFlow.flowPackageChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.GroundWaterFlow,
                                                  flowPackage=p)
                if p in modflow_models.uncouple(
                        modflow_models.GroundWaterFlow.flowParameterChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.GroundWaterFlow,
                                                  flowParameter=p)
                # BoundaryCondition
                if p in modflow_models.uncouple(
                        modflow_models.BoundaryCondition.specifiedHeadBoundaryPackageChoices):
                    # create if does not exist, update if it does exist
                    specified_head_boundary_package_list.append(p)
                    create_or_update_from_package(
                        resource, modflow_models.BoundaryCondition,
                        specified_head_boundary_packages=specified_head_boundary_package_list)
                if p in modflow_models.uncouple(
                        modflow_models.BoundaryCondition.specifiedFluxBoundaryPackageChoices):
                    # create if does not exist, update if it does exist
                    specified_flux_boundary_packages_list.append(p)
                    create_or_update_from_package(
                        resource, modflow_models.BoundaryCondition,
                        specified_flux_boundary_packages=specified_flux_boundary_packages_list)
                if p in modflow_models.uncouple(
                        modflow_models.BoundaryCondition.headDependentFluxBoundaryPackageChoices):
                    # create if does not exist, update if it does exist
                    head_dependent_flux_boundary_packages.append(p)
                    create_or_update_from_package(
                        resource, modflow_models.BoundaryCondition,
                        head_dependent_flux_boundary_packages=head_dependent_flux_boundary_packages)
                # ModelCalibration
                if p in modflow_models.uncouple(
                        modflow_models.ModelCalibration.observationProcessPackageChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.ModelCalibration,
                                                  observationProcessPackage=p)
                # GeneralElements
                if p in modflow_models.uncouple(
                        modflow_models.GeneralElements.modelSolverChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.GeneralElements,
                                                  modelSolver=p)
                if p in modflow_models.uncouple(
                        modflow_models.GeneralElements.outputControlPackageChoices):
                    # create if does not exist, update if it does exist
                    output_control_package_list.append(p)
                    create_or_update_from_package(
                        resource, modflow_models.GeneralElements,
                        output_control_package=output_control_package_list)
                if p in modflow_models.uncouple(
                        modflow_models.GeneralElements.subsidencePackageChoices):
                    # create if does not exist, update if it does exist
                    create_or_update_from_package(resource, modflow_models.GeneralElements,
                                                  subsidencePackage=p)


def create_or_update_from_package(resource, term, **kwargs):
    terms_dict = dict(
            StressPeriod='stress_period',
            GroundWaterFlow='ground_water_flow',
            BoundaryCondition='boundary_condition',
            ModelCalibration='model_calibration',
            GeneralElements='general_elements',
            GridDimensions='grid_dimensions',
            StudyArea='study_area'
            )
    t = terms_dict[term.term]
    metadata_term_obj = getattr(resource.metadata, t)
    if not metadata_term_obj:
        resource.metadata.create_element(
            term.term,
            **kwargs
        )
    else:
        resource.metadata.update_element(
            term.term,
            metadata_term_obj.id,
            **kwargs
        )
    create_bag_files(resource)


def add_metadata_from_dis_file(dis_file, res):
    """
    This function parses the .dis file and populates relevant metadata terms for the MODFLOWModel-
    InstanceResource object being passed. Data from the .dis file is used to populate portions of
    the StressPeriod, GridDimensions, and StudyArea terms. Information about what the parts of the
    .dis file is at : https://water.usgs.gov/nrp/gwsoftware/modflow2000/MFDOC/index.html?dis.htm
    inputs:
    dis_file: file object of .dis file
    res: MODFLOWModelInstanceResource object
    """
    lines = dis_file.resource_file.readlines()
    first_line = True
    ss = False
    tr = False
    total_y_length = None
    total_x_length = None
    study_area_info = dict()
    stress_period_info = dict()
    for l in lines:
        l = l.strip()
        l = l.split()
        first_char = l[0].strip()
        l = [c.lower() for c in l]
        if not first_char.startswith('#'):
            if first_line:
                grid_dimension_info = dict(
                    numberOfLayers=l[0],
                    numberOfRows=l[1],
                    numberOfColumns=l[2],
                )
                lenuni = l[5]
                first_line = False
            unit_con_factor = get_unit_conversion_factor(int(lenuni))
            if 'delr' in l:
                if 'constant' in l:
                    grid_dimension_info['typeOfRows'] = 'Regular'
                    row_len = l[1]
                    if int(lenuni) > 0:
                        total_y_length = float(row_len) * float(
                            grid_dimension_info['numberOfRows']) * unit_con_factor
                elif 'internal' in l:
                    grid_dimension_info['typeOfRows'] = 'Irregular'
            if 'delc' in l:
                if 'constant' in l:
                    grid_dimension_info['typeOfColumns'] = 'Regular'
                    col_len = l[1]
                    if int(lenuni) > 0:
                        total_x_length = float(col_len) * float(
                            grid_dimension_info['numberOfColumns']) * unit_con_factor
                elif 'internal' in l:
                    grid_dimension_info['typeOfColumns'] = 'Irregular'
            if 'ss' in l:
                ss = True
            if 'tr' in l:
                tr = True
            if total_y_length and total_x_length:
                study_area_info['totalLength'] = max(total_y_length, total_x_length)
                study_area_info['totalWidth'] = min(total_y_length, total_x_length)
    if ss and not tr:
        stress_period_info['stressPeriodType'] = 'Steady'
    elif tr and not ss:
        stress_period_info['stressPeriodType'] = 'Transient'
    elif ss and tr:
        stress_period_info['stressPeriodType'] = 'Steady and Transient'
    create_or_update_from_package(res, modflow_models.StressPeriod, **stress_period_info)
    create_or_update_from_package(res, modflow_models.GridDimensions, **grid_dimension_info)
    create_or_update_from_package(res, modflow_models.StudyArea, **study_area_info)


def get_unit_conversion_factor(unit_id):
    factor = None
    if unit_id == 0:
        factor = 'length units are undefined'
    elif unit_id == 1:  # units are in feet
        factor = 0.3048
    elif unit_id == 2:
        factor = 1.
    elif unit_id == 3:
        factor = .01
    return factor
