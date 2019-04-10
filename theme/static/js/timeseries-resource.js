/**
* Created by Mauriel on 3/9/2017.
*/

$(document).ready(function(){
    var el = $('#div-series-selection');
    if (el.length) {
        $(window).scrollTop($(el).offset().top - 300);
        if ($("#can-update-sqlite-file").val() === "True" && ($("#metadata-dirty").val() === "True")) {
            $("#sql-file-update").show();
        }
    }

    if ($("#resource-mode").val() === 'Edit'){
        $("#readonly-coverage-notice").show();
    }

    $("#coverage-spatial :input").prop('readonly', true);
    // Don't allow the user to change the coverage type
    var $id_type_div = $("#div_id_type");
    var $box_radio = $id_type_div.find("input[value='box']");
    var $point_radio = $id_type_div.find("input[value='point']");
    if ($box_radio.attr("checked") !== "checked") {
        $box_radio.parent().closest("label").addClass("text-muted");
        $box_radio.attr('disabled', true);
    }
    else {
        $point_radio.parent().closest("label").addClass("text-muted");
        $point_radio.attr('disabled', true);
    }
    $point_radio.attr('onclick', 'return false');
    $box_radio.attr('onclick', 'return false');

    if ($('#id_north').val() || $('#id_northlimit').val()){
        $("#id_name").prop('readonly', false);
        $('#coverage-spatial').find("button.btn-primary").prop('disabled', false);
    }

    $("#coverage-temporal :input").prop('disabled', true);

    var tsSelect = $(".time-series-forms select");

    tsSelect.append('<option value="Other">Other...</option>');

    tsSelect.parent().parent().append('<div class="controls other-field" style="display:none;"> <label class="text-muted control-label">Specify: </label><input class="form-control input-sm textinput textInput" name="" type="text"> </div>')

    tsSelect.change(function(e){
        if (e.target.value == "Other") {
            var name = e.target.name;
            $(e.target).parent().parent().find(".other-field").show();
            $(e.target).parent().parent().find(".other-field input").attr("name", name);
            $(e.target).removeAttr("name");
        }
        else {
            if (!e.target.name.length) {
                var name = $(e.target).parent().parent().find(".other-field input").attr("name");
                $(e.target).attr("name", name);
                $(e.target).parent().parent().find(".other-field input").removeAttr("name");
                $(e.target).parent().parent().find(".other-field").hide();
            }
        }
    });

    processSiteMetadataElement();
    processVariableMetadataElement();
    processMethodMetadataElement();
    processProcessingLevelMetadataElement();

    // TODO: TESTING
    $("#btn-update-sqlite-file").click(function () {
        this.form.submit();
        return false;
    });

    $("#series_id").change(function() {
        this.form.submit()
    });
});

function processSiteMetadataElement(){
    var sites_text = $('#id_available_sites').val();
    var sites_json = $.parseJSON(sites_text);
    var original_site_code = $('#id_site_code').val();
    var site_form_elements = ['#id_site_code', '#id_site_name', '#id_elevation_m', '#id_elevation_datum', '#id_site_type', '#id_latitude', '#id_longitude'];
    // remove the select option "Other.." from site code selection dropdown
    $("#id_site_code_choices option[value='Other']").remove();

    $('#id_site_code_choices').change(function () {
        var selectedSiteCode = this.value;
        if(selectedSiteCode === "----"){
            $('#id-site').find("button.btn-primary").hide();
            for (i = 0; i < site_form_elements.length; i++) {
                $(site_form_elements[i]).val("");
                $(site_form_elements[i]).attr('readonly', false);
            }

            $("#id_site_type").css('pointer-events', 'auto');
            $("#id_elevation_datum").css('pointer-events', 'auto');
            var form_action = $('#id-site').attr('action');
            if(form_action.includes("update-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("site") + 5;
                form_action = form_action.slice(0, slice_end_index) + "add-metadata/";
                $('#id-site').attr('action', form_action);
            }
            return;
        }

        $(sites_json).each(function (i, site) {
            if (site.site_code === selectedSiteCode){
                $('#id_site_code').val(site.site_code);
                $('#id_site_name').val(site.site_name);
                $('#id_elevation_m').val(site.elevation_m);
                $('#id_elevation_datum').val(site.elevation_datum);
                $('#id_site_type').val(site.site_type);
                $('#id_latitude').val(site.latitude);
                $('#id_longitude').val(site.longitude);
                // change the site form action
                var form_action = $('#id-site').attr('action');
                if(form_action.includes("add-metadata")){
                    form_action = form_action.replace("add-metadata", site.id + "/update-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("site") + 5;
                    form_action = form_action.slice(0, slice_end_index) + site.id + "/update-metadata/";
                }

                $('#id-site').attr('action', form_action);

                if (selectedSiteCode !== original_site_code){
                    $('#id-site').find("button.btn-primary").show();
                }
                else {
                    $('#id-site').find("button.btn-primary").hide();
                }
                for (i = 0; i < site_form_elements.length; i++) {
                    $(site_form_elements[i]).attr('readonly', selectedSiteCode !== original_site_code);
                }

                if (selectedSiteCode !== original_site_code){
                     $("#id_site_type").css('pointer-events', 'none');
                     $("#id_elevation_datum").css('pointer-events', 'none');
                 }
                 else {
                     $("#id_site_type").css('pointer-events', 'auto');
                     $("#id_elevation_datum").css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}
function processVariableMetadataElement(){
    var variable_text = $('#id_available_variables').val();
    var variables_json = $.parseJSON(variable_text);
    var original_variable_code = $('#id_variable_code').val();
    var variable_from_elements = ['#id_variable_code', '#id_variable_name', '#id_variable_type', '#id_no_data_value', '#id_variable_definition', '#id_speciation'];
    // remove the select option "Other.." from variable code selection dropdown
    $("#id_variable_code_choices option[value='Other']").remove();
    $('#id_variable_code_choices').change(function () {
        var selectedVariableCode = this.value;
        if(selectedVariableCode === "----"){
            $('#id-variable').find("button.btn-primary").hide();
            for (i = 0; i < variable_from_elements.length; i++) {
                $(variable_from_elements[i]).val("");
                $(variable_from_elements[i]).attr('readonly', false);
            }

            $('#id_variable_name').css('pointer-events', 'auto');
            $('#id_variable_type').css('pointer-events', 'auto');
            $('#id_speciation').css('pointer-events', 'auto');
            var form_action = $('#id-variable').attr('action');
            if(form_action.includes("update-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("variable") + 9;
                form_action = form_action.slice(0, slice_end_index) + "add-metadata/";
                $('#id-variable').attr('action', form_action);
            }
            return;
        }

        $(variables_json).each(function (i, variable) {
            if (variable.variable_code === selectedVariableCode){
                $('#id_variable_code').val(variable.variable_code);
                $('#id_variable_name').val(variable.variable_name);
                $('#id_variable_type').val(variable.variable_type);
                $('#id_no_data_value').val(variable.no_data_value);
                $('#id_variable_definition').val(variable.variable_definition);
                $('#id_speciation').val(variable.speciation);
                // change the variable form action
                var form_action = $('#id-variable').attr('action');
                if(form_action.includes("add-metadata")){
                    form_action = form_action.replace("add-metadata", variable.id + "/update-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("variable") + 9;
                    form_action = form_action.slice(0, slice_end_index) + variable.id + "/update-metadata/";
                }

                $('#id-variable').attr('action', form_action);

                if (selectedVariableCode !== original_variable_code){
                    $('#id-variable').find("button.btn-primary").show();
                }
                else {
                    $('#id-variable').find("button.btn-primary").hide();
                }
                for (i = 0; i < variable_from_elements.length; i++) {
                    $(variable_from_elements[i]).attr('readonly', selectedVariableCode !== original_variable_code);
                }

                if(selectedVariableCode !== original_variable_code){
                    $('#id_variable_name').css('pointer-events', 'none');
                    $('#id_variable_type').css('pointer-events', 'none');
                    $('#id_speciation').css('pointer-events', 'none');
                }
                else {
                    $('#id_variable_name').css('pointer-events', 'auto');
                    $('#id_variable_type').css('pointer-events', 'auto');
                    $('#id_speciation').css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}
function processMethodMetadataElement(){
    var method_text = $('#id_available_methods').val();
    var methods_json = $.parseJSON(method_text);
    var original_method_code = $('#id_method_code').val();
    var method_form_elements = ['#id_method_code', '#id_method_name', '#id_method_type', '#id_method_description', '#id_method_link'];
    // remove the select option "Other.." from method code selection dropdown
    $("#id_method_code_choices option[value='Other']").remove();
    $('#id_method_code_choices').change(function () {
        var selectedMethodCode = this.value;
        if(selectedMethodCode === "----"){
            $('#id-method').find("button.btn-primary").hide();
            for (i = 0; i < method_form_elements.length; i++) {
                $(method_form_elements[i]).val("");
                $(method_form_elements[i]).attr('readonly', false);
            }
            $('#id_method_type').css('pointer-events', 'auto');

            var form_action = $('#id-method').attr('action');
            if(form_action.includes("update-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("method") + 7;
                form_action = form_action.slice(0, slice_end_index) + "add-metadata/";
                $('#id-method').attr('action', form_action);
            }
            return;
        }

        $(methods_json).each(function (i, method) {
            if (method.method_code === selectedMethodCode){
                $('#id_method_code').val(method.method_code);
                $('#id_method_name').val(method.method_name);
                $('#id_method_type').val(method.method_type);
                $('#id_method_description').val(method.method_description);
                $('#id_method_link').val(method.method_link);

                // change the method form action
                var form_action = $('#id-method').attr('action');
                if(form_action.includes("add-metadata")){
                    form_action = form_action.replace("add-metadata", method.id + "/update-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("method") + 7;
                    form_action = form_action.slice(0, slice_end_index) + method.id + "/update-metadata/";
                }

                $('#id-method').attr('action', form_action);

                if (selectedMethodCode !== original_method_code){
                    $('#id-method').find("button.btn-primary").show();
                }
                else {
                    $('#id-method').find("button.btn-primary").hide();
                }
                for (i = 0; i < method_form_elements.length; i++) {
                    $(method_form_elements[i]).attr('readonly', selectedMethodCode !== original_method_code);
                }

                if(selectedMethodCode !== original_method_code){
                    $('#id_method_type').css('pointer-events', 'none');
                }
                else {
                    $('#id_method_type').css('pointer-events', 'auto');
                }
                return false;
            }
        });
    })
}

function processProcessingLevelMetadataElement(){
    var pro_level_text = $('#id_available_processinglevels').val();
    var pro_levels_json = $.parseJSON(pro_level_text);
    var original_pro_level_code = $('#id_processing_level_code').val();
    var pro_level_form_elements = ['#id_processing_level_code', '#id_definition', '#id_explanation'];
    // remove the select option "Other.." from processinglevel code selection dropdown
    $("#id_processinglevel_code_choices option[value='Other']").remove();
    $('#id_processinglevel_code_choices').change(function () {
        var selectedProLevelCode = this.value;
        if(selectedProLevelCode === "----"){
            $('#id-processinglevel').find("button.btn-primary").hide();
            for (i = 0; i < pro_level_form_elements.length; i++) {
                $(pro_level_form_elements[i]).val("");
                $(pro_level_form_elements[i]).attr('readonly', false);
            }

            var form_action = $('#id-processinglevel').attr('action');
            if(form_action.includes("update-metadata")) {
                var slice_end_index = form_action.toLowerCase().indexOf("processinglevel") + 16;
                form_action = form_action.slice(0, slice_end_index) + "add-metadata/";
                $('#id-processinglevel').attr('action', form_action);
            }
            return;
        }

        $(pro_levels_json).each(function (i, pro_level) {
            if (pro_level.processing_level_code.toString() === selectedProLevelCode){
                $('#id_processing_level_code').val(pro_level.processing_level_code);
                $('#id_definition').val(pro_level.definition);
                $('#id_explanation').val(pro_level.explanation);

                // change the processinglevel form action
                var form_action = $('#id-processinglevel').attr('action');
                if(form_action.includes("add-metadata")){
                    form_action = form_action.replace("add-metadata", pro_level.id + "/update-metadata");
                }
                else {
                    var slice_end_index = form_action.toLowerCase().indexOf("processinglevel") + 16;
                    form_action = form_action.slice(0, slice_end_index) + pro_level.id + "/update-metadata/";
                }

                $('#id-processinglevel').attr('action', form_action);

                if (selectedProLevelCode !== original_pro_level_code){
                    $('#id-processinglevel').find("button.btn-primary").show();
                }
                else {
                    $('#id-processinglevel').find("button.btn-primary").hide();
                }
                for (i = 0; i < pro_level_form_elements.length; i++) {
                    $(pro_level_form_elements[i]).attr('readonly', selectedProLevelCode !== original_pro_level_code);
                }
                return false;
            }
        });
    })
}