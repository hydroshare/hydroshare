/**
* Created by Mauriel on 5/19/2019.
*/

let relevantToolsApp = new Vue({
    el: '#apps-dropdown',
    delimiters: ['${', '}'],
    data: {
        tools: [],
        openWithTools: [],
        resId: SHORT_ID,
        isLoading: true,
        trackingAppLaunchUrl: TRACKING_APPLAUNCH_URL,
    },
    methods: {
        // Returns the Url needed to launch the app with this resource
        getResAppUrl: function (tool) {
            return this.trackingAppLaunchUrl + '?url=' + tool.url + '&name=' +  tool.title +
                '&tool_res_id=' + tool.res_id + '&res_id=' + this.resId;
        },
        // Returns the Url needed to launch a file in this resource
        getFileAppUrl: function (tool) {
            if (tool.hasOwnProperty('file_extensions') && tool.url_file) {
                return this.trackingAppLaunchUrl + '?url=' + tool.url_file + '&name=' + tool.title +
                    '&tool_res_id=' + tool.res_id + '&res_id=' + this.resId;
            }
            return null;    // default
        },
        // Returns the Url needed to launch an aggregation in this resource
        getAggregationAppUrl: function (tool) {
            if (tool.hasOwnProperty('agg_types') && tool.url_aggregation) {
                return this.trackingAppLaunchUrl + '?url=' + tool.url_aggregation + '&name=' + tool.title +
                    '&tool_res_id=' + tool.res_id + '&res_id=' + this.resId;
            }
            return null;    // default
        }
    },
    mounted: function () {
        let vue = this;
        $.get("/hsapi/_internal/" + this.resId + "/relevant-tools/", function (response) {
            response = JSON.parse(response);
            if (response) {
                vue.tools = response['tool_list'].map(function (tool) {
                    // We need to encode special characters in Urls
                    if (tool.hasOwnProperty('url') && tool.url !== null) {
                        tool.url = encodeURIComponent(tool.url);
                    }
                    if (tool.hasOwnProperty('url_aggregation') && tool.url_aggregation !== null) {
                        tool.url_aggregation = encodeURIComponent(tool.url_aggregation);
                    }
                    if (tool.hasOwnProperty('url_file') && tool.url_file !== null) {
                        tool.url_file = encodeURIComponent(tool.url_file);
                    }

                    return tool;
                });
                // TODO 5386 revert
                console.log(vue.tools)

                vue.openWithTools = vue.tools.filter(function(tool) {
                    return tool.url;
                });

                // Append menu items to right click menu in file browser
                let menu = $("#right-click-menu");
                let hasTools = false;
                for (let i = 0; i < vue.tools.length; i++) {
                    let tool = vue.tools[i];

                    if (tool['agg_types']) {
                        let aggregationUrl = vue.getAggregationAppUrl(tool);
                        if (aggregationUrl) {
                            let menuItem =
                            '<li class="btn-open-with" data-menu-name="web-app" ' +
                                'data-file-extensions="' + tool['file_extensions'] + '" ' +
                                'data-agg-types="' + tool['agg_types'] + '" data-url-aggregation="' +
                                aggregationUrl + '" data-tool-appkey="' + tool['tool_appkey'] + '">' +
                                '<img class="file-options-webapp-icon" src="' + tool['icon_url'] +
                                    '" alt="' + tool['title'] + '"/>' + '<span>' + tool['title'] + '</span>' +
                            '</li>';
                            if (!hasTools) {
                                menu.append('<li id="tools-separator" role="separator" class="divider"></li>');
                            }
                            menu.append(menuItem);
                            hasTools = true;
                        }
                    }
                    // TODO 5386 file extensions for right click in file browser
                    if (tool['file_extensions']){
                        let urlFile = vue.getFileAppUrl(tool);
                        if (urlFile) {
                            let menuItem =
                            '<li class="btn-open-with" data-menu-name="web-app" ' +
                                'data-agg-types="' + tool['agg_types'] + '" ' +
                                'data-file-extensions="' + tool['file_extensions'] + '" data-url-file="' +
                                urlFile + '" data-tool-appkey="' + tool['tool_appkey'] + '">' +
                                '<img class="file-options-webapp-icon" src="' + tool['icon_url'] +
                                    '" alt="' + tool['title'] + '"/>' + '<span>' + tool['title'] + '</span>' +
                            '</li>';

                            if (!hasTools) {
                                menu.append('<li id="tools-separator" role="separator" class="divider"></li>');
                            }
                            menu.append(menuItem);
                            hasTools = true;
                        }
                    }
                }

                // Bind OpenWith method
                $(".btn-open-with").click(function () {
                    const file = $("#fb-files-container li.ui-selected");
                    // get the path under the contents directory
                    const path = file.attr("data-url").split(new RegExp("resource/[a-z0-9]*/data/contents/"))[1];
                    let fullURL;
                    if ($(this).attr("data-url-aggregation")) {
                        fullURL = $(this).attr("data-url-aggregation")
                        if(fullURL.includes('HS_JS_AGG_KEY')) {
                            fullURL = fullURL + '&HS_JS_AGG_KEY=' + path;
                        }

                        if (file.children('span.fb-file-type').text() === 'File Folder') {
                            // TODO: populate main_file value in aggregation object of structure response
                            if(fullURL.includes('HS_JS_MAIN_FILE_KEY')) {
                                fullURL = fullURL + '&HS_JS_MAIN_FILE_KEY=' + file.attr("data-main-file");
                            }
                        }
                        else {
                            if(fullURL.includes('HS_JS_MAIN_FILE_KEY')) {
                                fullURL = fullURL + '&HS_JS_MAIN_FILE_KEY=' + file.children('span.fb-file-name').text();
                            }
                        }
                    }
                    else {
                        // not an aggregation
                        fullURL = $(this).attr("data-url-file");
                        if(fullURL.includes('HS_JS_FILE_KEY')) {
                            fullURL = fullURL + '&HS_JS_FILE_KEY=' + path;
                        }
                    }
                    window.open(fullURL);
                });
            }

            vue.isLoading = false;
        });
    }
});