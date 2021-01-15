/* global SwaggerUIBundle, SwaggerUIStandalonePreset*/
odoo.define("base_rest.swagger_ui", function (require) {
    "use strict";

    var core = require("web.core");

    var SwaggerUI = core.Class.extend({
        init: function (api_urls, primary_name) {
            this.api_urls = api_urls;
            this.primary_name = primary_name;
        },

        start: function (dom_id) {
            this.ui = SwaggerUIBundle({
                urls: this.api_urls,
                dom_id: dom_id,
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                plugins: [SwaggerUIBundle.plugins.DownloadUrl],
                layout: "StandaloneLayout",
                "urls.primaryName": this.primary_name,
                operationsSorter: function (a, b) {
                    var methodsOrder = [
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "options",
                        "trace",
                    ];
                    var result =
                        methodsOrder.indexOf(a.get("method")) -
                        methodsOrder.indexOf(b.get("method"));
                    if (result === 0) {
                        result = a.get("path").localeCompare(b.get("path"));
                    }
                    return result;
                },
                tagsSorter: "alpha",
                onComplete: function () {
                    if (this.web_btn === undefined) {
                        this.web_btn = $(
                            "<a class='fa fa-th swg-odoo-web-btn' href='/web' accesskey='h'></a>"
                        );
                        $(".topbar").prepend(this.web_btn);
                    }
                },
            });
        },
    });

    return SwaggerUI;
});
