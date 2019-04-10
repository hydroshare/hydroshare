/**
* Created by Mauriel on 3/9/2017.
*/

var globurl = "";

$(document).ready(function(){
    $('#site').change(function(){
        var site = $('#site').val();
        if (site != "-1")
        {
            get_variables(site);
        }
    });

    $('#variable').change(function(){
        var variable = $('#variable').val();
        var site = $('#site').val();
        if  (site != "-1" && variable != "-1")
        {
            getVals('soap', site, variable);
        }
    });

    // prevent from unexpectedly submitting form when users press down "Enter" key
    $('#create-form').on("keyup keypress", function(e) {
    var code = e.keyCode || e.which;
        if (code  == 13) {
            e.preventDefault();
            return false;
        }
    });

    $('#site-div').hide();
    $('#variable-div').hide();
    $('#message-div').show();
    $('#preview-div').hide();
    $('#check-url-btn').prop('disabled', false);
    get_his_central_urls();

    $("#check-url-btn").click(function() {
        check_url($('#input_url').val());
    });
});

function show_message(show_it, msg, color) {
    if (show_it)
    {
        $('#message').html(msg).css('color', color);
        $('#message-div').show();
    }
    else
    {
        $('#message-div').hide();
    }
}

function get_his_central_urls(){
    $.ajax({
        type: "GET",
        url: '/hsapi/_internal/get-his-urls/',
        success: function (data, xhr, status) {
            if (data["status"] == "success")
            {
                $('#his-loading')
                        .html('HIS Central Servers available')
                        .css('color', 'Green');
                var select = document.getElementsByName('url')[0];
                removeOptions(select);
                for (var i=0; i < data["url_list"].length; i++)
                {
                    var ln = data["url_list"][i];
                    var opt = document.createElement('option');
                    opt.value = ln;
                    opt.innerHTML = ln;
                    select.appendChild(opt);
                }
            }
            else
            {
                $('#his-loading')
                    .html('HIS Central Servers currently not available')
                    .css('color','Red');
            }
        },
        error: function(){
            $('#his-loading')
                    .html('HIS Central Servers currently not available')
                    .css('color','Red');
        }
    });
} // function get_his_central_urls()

 // check the url users input
function check_url(url){
    $('#check-url-btn').prop('disabled', true);
    globurl = url;

    show_message(false);
    $('#site-div').hide();
    $('#variable-div').hide();
    $('#preview-div').hide();
    $('#submit').addClass('disabled');
    show_message(true, 'Checking URL...', 'Black');
    if (url.toLowerCase().match(/wsdl$/))
    { // SOAP
        get_sites(url);
    }
    else { // REST
        $.ajax({
            type: "GET",
            url: '/hsapi/_internal/verify-rest-url/',
            data: {url: url},
            success: function (data, xhr, status) {
                $('#check-url-btn').prop('disabled', false);
                show_message(false);
                if (data["status"] == "success")
                {
                    getVals('rest');
                }
                else
                {
                    show_message(true, '<h4>URL did not verify. There may be a problem with the URL you entered</h4>', 'Red');
                }
            },
            error: function(){
                $('#check-url-btn').prop('disabled', false);
                show_message(true, '<h4>URL did not verify. There may be a problem with the URL you entered</h4>', 'Red');
            }
        });
    }
} // function check_url(url)

function removeOptions(selectbox){
    for(var i=selectbox.options.length-1; i>=0; i--)
    {
        selectbox.remove(i);
    }
}

function get_sites(url)
{
    show_message(true, 'Retrieving sites...', 'Black');
    // disable url textbox
    $('.ui-autocomplete-input').prop("disabled", true);

    $.ajax({
        type:"GET",
        url:'/hsapi/_internal/search-sites/',
        data: {url: url},
        success: function(data, xhr, status){
            $('#check-url-btn').prop("disabled", false);
            if(data["status"] == "success")
            {
                var select = document.getElementsByName('site')[0];
                removeOptions(select);
                if (data["sites"].length > 1)
                {
                    var opt = document.createElement('option');
                    opt.value = "";
                    opt.innerHTML = "Please select a Site";
                    opt.disabled = true;
                    opt.selected = true;
                    select.appendChild(opt);
                }

                for(var i=0; i < data["sites"].length; i++)
                {
                    var ln = data["sites"][i];
                    var opt = document.createElement('option');
                    opt.value = ln;
                    opt.innerHTML = ln.substring(0, ln.indexOf(" ["));
                    select.appendChild(opt);
                }

                show_message(false);
                $('#site-div').show();
                // enable url textbox
                $('.ui-autocomplete-input').prop("disabled", false);

                if (data["sites"].length == 1){
                    $('#site').trigger("change");
                }
            }
            else
            {
               get_sites_failed();
            }
        },
        error: function(data, stuff){
            $('#check-url-btn').prop("disabled", false);
            get_sites_failed();
        }
    });

} // get_sites(url)

function get_sites_failed()
{
    $('#site-div').hide();
    $('#variable-div').hide();
    $('#preview-div').hide();
    show_message(true, 'There was an error retrieving sites for this server', "Red");
    // enable url textbox
    $('.ui-autocomplete-input').prop("disabled", false);
}

function get_variables(site)
{
    site_code = site;
    var url = globurl;

    show_message(true, 'Retrieving variables...', 'Black');
    // disable url textbox
    $('.ui-autocomplete-input').prop("disabled", true);
    $('#site-div').show();
    // disable site select box
    $('#site').prop("disabled", true);
    $('#variable-div').hide();
    $('#preview-div').hide();
    $('#submit').addClass('disabled');
    $('#check-url-btn').prop("disabled", true);

    $.ajax({
        type:"GET",
        url:'/hsapi/_internal/search-variables/',
        data: {url: url,
            site: site_code},
        success: function(data, xhr, status){
            $('#check-url-btn').prop("disabled", false);
            if(data["status"] == "success")
            {
                show_message(false);
                $('.ui-autocomplete-input').prop("disabled", false);
                $('#site-div').show();
                $('#site').prop("disabled", false);
                $('#variable-div').show();
                $('#variable').prop("disabled", false);

                var select = document.getElementsByName('variable')[0];
                removeOptions(select);
                if (data["variables"].length > 1)
                {
                    var opt = document.createElement('option');
                    opt.value = "";
                    opt.innerHTML = "Please select a Variable";
                    opt.disabled = true;
                    opt.selected = true;
                    select.appendChild(opt);
                }

                for(var i=0; i < data["variables"].length; i++)
                {
                    var ln = data["variables"][i];
                    var opt = document.createElement('option');
                    opt.value = ln;
                    opt.innerHTML = ln.substring(0, ln.indexOf(" ["));
                    select.appendChild(opt);
                }

                if (data["variables"].length == 1){
                    $('#variable').trigger("change");
                }
            }
            else
            {
                get_variables_failed();
            }
        },
        error: function(data, stuff) {
            $('#check-url-btn').prop("disabled", false);
            get_variables_failed();
        }
    })
} // get_variables(site)

function get_variables_failed()
{
    show_message(true, 'There was an error retrieving variables for this site', 'Red');
    $('.ui-autocomplete-input').prop("disabled", false);
    $('#site-div').show();
    $('#site').prop("disabled", false);
    $('#variable-div').hide();
    $('#preview-div').hide();
    $('#submit').addClass('disabled');
}

function getVals(ref_type, _site, _var)
{
    $('.ui-autocomplete-input').prop("disabled", true);
    show_message(true, 'Retrieving Data...', "Black");
    $('#submit').addClass('disabled');
    $('#preview-div').hide();
    $('#check-url-btn').prop("disabled", true);

    var service_url = "";
    var site = "";
    var variable = "";
    if (ref_type == 'rest')
    {
        service_url = globurl;
    }
    else
    {
        $('#site-div').show();
        $('#site').prop("disabled", true);
        $('#variable-div').show();
        $('#variable').prop("disabled", true);

        service_url = globurl;
        site = _site;
        variable = _var;
    }

    $.ajax({
        type:"GET",
        url:'/hsapi/_internal/time-series-from-service/',
        data: {ref_type: ref_type,
            service_url: service_url,
            site: site,
            variable: variable},
        success: function(data, xhr, status){
            $('#check-url-btn').prop("disabled", false);
            if (data["status"] == "success")
            {
                $('.ui-autocomplete-input').prop("disabled", false);
                $('#site').prop("disabled", false);
                $('#variable').prop("disabled", false);
                show_message(false);
                $('#submit').removeClass('disabled');

                var preview_url = data['preview_url'];
                $('#preview-div').html('<p style="text-align:center;"><img align="middle" src="'+
                        preview_url +'" id="preview-graph" /></p>').show();
            }
            else
            {
                getVals_failed();
            }
        },
        error: function(data, stuff){
            $('#check-url-btn').prop("disabled", false);
            getVals_failed();
        }
    });
} // function getVals(ref_type, _site, _var)

function getVals_failed() {
    $('.ui-autocomplete-input').prop("disabled", false);
    show_message(true, "This data failed to validate, which probably means that the WaterML document is not correctly formatted. This time series cannot be used to create a resource.", 'Red')
    $('#preview-div').hide();
    $('#site').prop("disabled", false);
    $('#variable').prop("disabled", false);
}

$.widget( "custom.combobox", {
    _create: function() {
        this.wrapper = $( "<span>" )
                .addClass( "custom-combobox" )
                .insertAfter( this.element );

        this.element.hide();
        this._createAutocomplete();
        this._createShowAllButton();
    },

    _createAutocomplete: function() {
        var selected = this.element.children( ":selected" ),
                value = selected.val() ? selected.text() : "";

        this.input = $( "<input>" )
                .appendTo( this.wrapper )
                .val( value )
                .attr( "title", "")
                .attr("id", "input_url")
                .addClass( "form-control" )
                .autocomplete({
                    delay: 0,
                    minLength: 0,
                    source: $.proxy( this, "_source" )
                })
                .tooltip({
                    tooltipClass: "ui-state-highlight"
                });

        this._on( this.input, {
            autocompleteselect: function( event, ui ) {
                check_url(ui.item.value);
                ui.item.option.selected = true;
                this._trigger( "select", event, {
                    item: ui.item.option
                });
            },

            autocompletechange: "_removeIfInvalid"
        });
    },

    _createShowAllButton: function() {
        var input = this.input,
                wasOpen = false;

        $( "<a>" )
                .attr( "title", "Show All Items" )
                .tooltip()
                .appendTo( this.wrapper )
                .button({
                    icons: {
                        primary: "ui-icon-triangle-1-s"
                    },
                    text: false
                })
                .removeClass( "ui-corner-all" )
                .addClass( "custom-combobox-toggle ui-corner-right" )
                .mousedown(function() {
                    wasOpen = input.autocomplete( "widget" ).is( ":visible" );
                })
                .click(function() {
                    input.focus();

                    // Close if already visible
                    if ( wasOpen ) {
                        return;
                    }

                    // Pass empty string as value to search for, displaying all results
                    input.autocomplete( "search", "" );
                });
    },

    _source: function( request, response ) {
        var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
        check_url(request.term);
        response( this.element.children( "option" ).map(function() {
            var text = $( this ).text();
            if ( this.value && ( !request.term || matcher.test(text) ) )
                return {
                    label: text,
                    value: text,
                    option: this
                };
        }) );
    },

    _removeIfInvalid: function( event, ui ) {

        // Selected an item, nothing to do
        if ( ui.item ) {
            return;
        }

        // Search for a match (case-insensitive)
        var value = this.input.val();
        var valueLowerCase = value.toLowerCase();
        var valid = false;
        this.element.children( "option" ).each(function() {
            if ( $( this ).text().toLowerCase() === valueLowerCase ) {
                this.selected = valid = true;
                return false;
            }
        });

        // Found a match, nothing to do
        if ( valid ) {
            return;
        }
    },

    _destroy: function() {
        this.wrapper.remove();
        this.element.show();
    }
});

$(function() {
$("#url").combobox();
$("#toggle").click(function() {
    $("#combobox").toggle();
});
});