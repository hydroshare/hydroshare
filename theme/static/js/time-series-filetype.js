function processSiteMetadataElement(){
    var sites_text = $('#id_available_sites').val();
    var sites_json = $.parseJSON(sites_text);
    var original_site_code = $('#id_site_code_filetype').val();
    var site_form_elements = ['#id_site_code_filetype', '#id_site_name_filetype',
        '#id_elevation_m_filetype', '#id_elevation_datum_filetype', '#id_site_type_filetype',
        '#id_latitude_filetype', '#id_longitude_filetype'];
    // remove the select option "Other.." from site code selection dropdown
    $("#id_site_code_choices option[value='Other']").remove();

    $('#id_site_code_choices').change(function () {
        var selectedSiteCode = this.value;
        if(selectedSiteCode === "----"){
            $('#id-site-file-type').find("button.btn-primary").hide();
            for (i = 0; i < site_form_elements.length; i++) {
                $(site_form_elements[i]).val("");
                $(site_form_elements[i]).attr('readonly', false);
            }

            $("#id_site_type_filetype").css('pointer-events', 'auto');
            $("#id_elevation_datum_filetype").css('pointer-events', 'auto');
            var form_action = $('#id-site-file-type').attr('action');
            if(form_action.includes("update-file-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("site") + 5;
                form_action = form_action.slice(0, slice_end_index) + "add-file-metadata/";
                $('#id-site-file-type').attr('action', form_action);
            }
            return;
        }

        $(sites_json).each(function (i, site) {
            if (site.site_code === selectedSiteCode){
                $('#id_site_code_filetype').val(site.site_code);
                $('#id_site_name_filetype').val(site.site_name);
                $('#id_elevation_m_filetype').val(site.elevation_m);
                $('#id_elevation_datum_filetype').val(site.elevation_datum);
                $('#id_site_type_filetype').val(site.site_type);
                $('#id_latitude_filetype').val(site.latitude);
                $('#id_longitude_filetype').val(site.longitude);
                // change the site form action
                var form_action = $('#id-site-file-type').attr('action');
                if(form_action.includes("add-file-metadata")){
                    form_action = form_action.replace("add-file-metadata", site.id + "/update-file-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("site") + 5;
                    form_action = form_action.slice(0, slice_end_index) + site.id + "/update-file-metadata/";
                }

                $('#id-site-file-type').attr('action', form_action);

                if (selectedSiteCode !== original_site_code){
                    $('#id-site-file-type').find("button.btn-primary").show();
                }
                else {
                    $('#id-site-file-type').find("button.btn-primary").hide();
                }
                for (i = 0; i < site_form_elements.length; i++) {
                    $(site_form_elements[i]).attr('readonly', selectedSiteCode !== original_site_code);
                }

                if (selectedSiteCode !== original_site_code){
                     $("#id_site_type_filetype").css('pointer-events', 'none');
                     $("#id_elevation_datum_filetype").css('pointer-events', 'none');
                 }
                 else {
                     $("#id_site_type_filetype").css('pointer-events', 'auto');
                     $("#id_elevation_datum_filetype").css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}

function processVariableMetadataElement(){
    var variable_text = $('#id_available_variables').val();
    var variables_json = $.parseJSON(variable_text);
    var original_variable_code = $('#id_variable_code_filetype').val();
    var variable_from_elements = ['#id_variable_code_filetype', '#id_variable_name_filetype',
        '#id_variable_type_filetype', '#id_no_data_value_filetype',
        '#id_variable_definition_filetype', '#id_speciation_filetype'];
    // remove the select option "Other.." from variable code selection dropdown
    $("#id_variable_code_choices option[value='Other']").remove();
    $('#id_variable_code_choices').change(function () {
        var selectedVariableCode = this.value;
        if(selectedVariableCode === "----"){
            $('#id-variable-file-type').find("button.btn-primary").hide();
            for (i = 0; i < variable_from_elements.length; i++) {
                $(variable_from_elements[i]).val("");
                $(variable_from_elements[i]).attr('readonly', false);
            }

            $('#id_variable_name_filetype').css('pointer-events', 'auto');
            $('#id_variable_type_filetype').css('pointer-events', 'auto');
            $('#id_speciation_filetype').css('pointer-events', 'auto');
            var form_action = $('#id-variable-file-type').attr('action');
            if(form_action.includes("update-file-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("variable") + 9;
                form_action = form_action.slice(0, slice_end_index) + "add-file-metadata/";
                $('#id-variable-file-type').attr('action', form_action);
            }
            return;
        }

        $(variables_json).each(function (i, variable) {
            if (variable.variable_code === selectedVariableCode){
                $('#id_variable_code_filetype').val(variable.variable_code);
                $('#id_variable_name_filetype').val(variable.variable_name);
                $('#id_variable_type_filetype').val(variable.variable_type);
                $('#id_no_data_value_filetype').val(variable.no_data_value);
                $('#id_variable_definition_filetype').val(variable.variable_definition);
                $('#id_speciation_filetype').val(variable.speciation);
                // change the variable form action
                var form_action = $('#id-variable-file-type').attr('action');
                if(form_action.includes("add-file-metadata")){
                    form_action = form_action.replace("add-file-metadata", variable.id + "/update-file-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("variable") + 9;
                    form_action = form_action.slice(0, slice_end_index) + variable.id + "/update-file-metadata/";
                }

                $('#id-variable-file-type').attr('action', form_action);

                if (selectedVariableCode !== original_variable_code){
                    $('#id-variable-file-type').find("button.btn-primary").show();
                }
                else {
                    $('#id-variable-file-type').find("button.btn-primary").hide();
                }
                for (i = 0; i < variable_from_elements.length; i++) {
                    $(variable_from_elements[i]).attr('readonly', selectedVariableCode !== original_variable_code);
                }

                if(selectedVariableCode !== original_variable_code){
                    $('#id_variable_name_filetype').css('pointer-events', 'none');
                    $('#id_variable_type_filetype').css('pointer-events', 'none');
                    $('#id_speciation_filetype').css('pointer-events', 'none');
                }
                else {
                    $('#id_variable_name_filetype').css('pointer-events', 'auto');
                    $('#id_variable_type_filetype').css('pointer-events', 'auto');
                    $('#id_speciation_filetype').css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}

function processMethodMetadataElement(){
    var method_text = $('#id_available_methods').val();
    var methods_json = $.parseJSON(method_text);
    var original_method_code = $('#id_method_code_filetype').val();
    var method_form_elements = ['#id_method_code_filetype', '#id_method_name_filetype',
        '#id_method_type_filetype', '#id_method_description_filetype', '#id_method_link_filetype'];
    // remove the select option "Other.." from method code selection dropdown
    $("#id_method_code_choices option[value='Other']").remove();
    $('#id_method_code_choices').change(function () {
        var selectedMethodCode = this.value;
        if(selectedMethodCode === "----"){
            $('#id-method-file-type').find("button.btn-primary").hide();
            for (i = 0; i < method_form_elements.length; i++) {
                $(method_form_elements[i]).val("");
                $(method_form_elements[i]).attr('readonly', false);
            }
            $('#id_method_type_filetype').css('pointer-events', 'auto');

            var form_action = $('#id-method-file-type').attr('action');
            if(form_action.includes("update-file-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("method") + 7;
                form_action = form_action.slice(0, slice_end_index) + "add-file-metadata/";
                $('#id-method-file-type').attr('action', form_action);
            }
            return;
        }

        $(methods_json).each(function (i, method) {
            if (method.method_code === selectedMethodCode){
                $('#id_method_code_filetype').val(method.method_code);
                $('#id_method_name_filetype').val(method.method_name);
                $('#id_method_type_filetype').val(method.method_type);
                $('#id_method_description_filetype').val(method.method_description);
                $('#id_method_link_filetype').val(method.method_link);

                // change the method form action
                var form_action = $('#id-method-file-type').attr('action');
                if(form_action.includes("add-file-metadata")){
                    form_action = form_action.replace("add-file-metadata", method.id + "/update-file-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("method") + 7;
                    form_action = form_action.slice(0, slice_end_index) + method.id + "/update-file-metadata/";
                }

                $('#id-method-file-type').attr('action', form_action);

                if (selectedMethodCode !== original_method_code){
                    $('#id-method-file-type').find("button.btn-primary").show();
                }
                else {
                    $('#id-method-file-type').find("button.btn-primary").hide();
                }
                for (i = 0; i < method_form_elements.length; i++) {
                    $(method_form_elements[i]).attr('readonly', selectedMethodCode !== original_method_code);
                }

                if(selectedMethodCode !== original_method_code){
                    $('#id_method_type_filetype').css('pointer-events', 'none');
                }
                else {
                    $('#id_method_type_filetype').css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}

function processProcessingLevelMetadataElement(){
    var pro_level_text = $('#id_available_processinglevels').val();
    var pro_levels_json = $.parseJSON(pro_level_text);
    var original_pro_level_code = $('#id_processing_level_code_filetype').val();
    var pro_level_form_elements = ['#id_processing_level_code_filetype', '#id_definition_filetype',
        '#id_explanation_filetype'];
    // remove the select option "Other.." from processinglevel code selection dropdown
    $("#id_processinglevel_code_choices option[value='Other']").remove();
    $('#id_processinglevel_code_choices').change(function () {
        var selectedProLevelCode = this.value;
        if(selectedProLevelCode === "----"){
            $('#id-processinglevel-file-type').find("button.btn-primary").hide();
            for (i = 0; i < pro_level_form_elements.length; i++) {
                $(pro_level_form_elements[i]).val("");
                $(pro_level_form_elements[i]).attr('readonly', false);
            }

            var form_action = $('#id-processinglevel-file-type').attr('action');
            if(form_action.includes("update-file-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("processinglevel") + 16;
                form_action = form_action.slice(0, slice_end_index) + "add-file-metadata/";
                $('#id-processinglevel-file-type').attr('action', form_action);
            }
            return;
        }

        $(pro_levels_json).each(function (i, pro_level) {
            if (pro_level.processing_level_code.toString() === selectedProLevelCode){
                $('#id_processing_level_code_filetype').val(pro_level.processing_level_code);
                $('#id_definition_filetype').val(pro_level.definition);
                $('#id_explanation_filetype').val(pro_level.explanation);

                // change the processinglevel form action
                var form_action = $('#id-processinglevel-file-type').attr('action');
                if(form_action.includes("add-file-metadata")){
                    form_action = form_action.replace("add-file-metadata", pro_level.id + "/update-file-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("processinglevel") + 16;
                    form_action = form_action.slice(0, slice_end_index) + pro_level.id + "/update-file-metadata/";
                }

                $('#id-processinglevel-file-type').attr('action', form_action);

                if (selectedProLevelCode !== original_pro_level_code){
                    $('#id-processinglevel_filetype').find("button.btn-primary").show();
                }
                else {
                    $('#id-processinglevel_filetype').find("button.btn-primary").hide();
                }
                for (i = 0; i < pro_level_form_elements.length; i++) {
                    $(pro_level_form_elements[i]).attr('readonly', selectedProLevelCode !== original_pro_level_code);
                }
                return false;
            }
        });
    })
}
