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
            let toolResAppURL;
             if (tool.url_res_query){
                toolResAppURL = encodeURI(tool.url_res_path) + '?' + encodeURIComponent(tool.url_res_query);
             }
             else {
                toolResAppURL = encodeURI(tool.url_res_path);
             }

            return this.trackingAppLaunchUrl + '?url=' + toolResAppURL + ';name=' +  tool.title +
                ';tool_res_id=' + tool.res_id + ';res_id=' + this.resId;
        },
        getPathTemplate: function (tool) {
            return this.trackingAppLaunchUrl + '?url=' + 'URL_PATH' + ';name=' + tool.title +
                    ';tool_res_id=' + tool.res_id + ';res_id=' + this.resId;
        },
        // Returns the Url needed to launch the app for an aggregation or a single file
        getFileAppLaunchUrl: function (pathTemplate, pathURL, queryURL) {
            pathURL = pathURL.trim();
            queryURL = queryURL.trim();
            let appLaunchURL;
            if (queryURL){
                appLaunchURL = encodeURI(pathURL) + '?' +  encodeURIComponent(queryURL);
            }
            else {
                appLaunchURL = encodeURI(pathURL);
            }

            return pathTemplate.replace('URL_PATH', appLaunchURL);
        }
    },
    mounted: function () {
        let vue = this;
        $.get("/hsapi/_internal/" + this.resId + "/relevant-tools/", function (response) {
            response = JSON.parse(response);
            if (response) {
                vue.tools = response['tool_list'];
                vue.openWithTools = vue.tools.filter(function(tool) {
                    if (tool.url_res_path){
                        return tool;
                    }
                });

                // Append menu items to right click menu in file browser
                let menu = $("#right-click-menu");
                let hasTools = false;
                for (let i = 0; i < vue.tools.length; i++) {
                    let tool = vue.tools[i];
                    let pathTemplate;
                    pathTemplate = vue.getPathTemplate(tool);

                    if (tool['agg_types']) {
                        let aggregationUrl = tool['url_aggregation_path'];
                        if (aggregationUrl) {
                            let menuItem =
                            '<li class="btn-open-with" data-menu-name="web-app" ' +
                                'data-agg-types="' + tool['agg_types'] + '" data-url-aggregation-path="' +
                                aggregationUrl + ' "data-url-aggregation-query="' + tool['url_aggregation_query'] +
                                ' "data-url-path-template="' + pathTemplate + '">' +
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

                    if (tool['file_extensions']){
                        let urlFile = tool['url_file_path'];
                        if (urlFile) {
                            let menuItem =
                            '<li class="btn-open-with" data-menu-name="web-app" ' +
                                'data-file-extensions="' + tool['file_extensions'] + '" data-url-file-path="'+
                                urlFile + ' "data-url-file-query="' + tool['url_file_query'] +
                                ' "data-url-path-template="' + pathTemplate + '">' +
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
                    let appLaunchURL;
                    let pathURL;
                    let queryURL;
                    let pathTemplate;
                    if ($(this).attr("data-url-aggregation-path")) {
                        // launching app for an aggregation
                        pathURL = $(this).attr("data-url-aggregation-path").replace("HS_JS_AGG_KEY", path);
                        if (file.children('span.fb-file-type').text() === 'File Folder') {
                            // TODO: populate main_file value in aggregation object of structure response
                            pathURL = pathURL.replace("HS_JS_MAIN_FILE_KEY", file.attr("data-main-file"));
                        }
                        else {
                            pathURL = pathURL.replace("HS_JS_MAIN_FILE_KEY", file.children('span.fb-file-name').text());
                        }
                        if ($(this).attr("data-url-aggregation-query")) {
                            queryURL = $(this).attr("data-url-aggregation-query").replace("HS_JS_AGG_KEY", path);
                        }
                        pathTemplate = $(this).attr("data-url-path-template");
                        appLaunchURL = vue.getFileAppLaunchUrl(pathTemplate, pathURL, queryURL);
                    }
                    else {
                        // not an aggregation - launching app for a file
                        pathURL = $(this).attr("data-url-file-path").replace("HS_JS_FILE_KEY", path);
                        if ($(this).attr("data-url-file-query")) {
                            queryURL = $(this).attr("data-url-file-query").replace("HS_JS_FILE_KEY", path);
                        }
                        pathTemplate = $(this).attr("data-url-path-template");
                        appLaunchURL = vue.getFileAppLaunchUrl(pathTemplate, pathURL, queryURL);
                    }

                    window.open(appLaunchURL);
                });
            }
            vue.isLoading = false;
        });
    }
});