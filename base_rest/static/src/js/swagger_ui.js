/* global SwaggerUIBundle, SwaggerUIStandalonePreset*/
odoo.define("base_rest.swagger_ui", function (require) {
    "use strict";

    var core = require("web.core");

    var SwaggerUI = core.Class.extend({
        init: function (selector) {
            this.selector = selector;
            this.$el = $(this.selector);
        },
        _swagger_bundle_settings: function () {
            const defaults = {
                dom_id: this.selector,
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                plugins: [SwaggerUIBundle.plugins.DownloadUrl],
                layout: "StandaloneLayout",
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
            };
            const config = this.$el.data("settings");
            return Object.assign({}, defaults, config);
        },
        start: function () {
            this.ui = SwaggerUIBundle(this._swagger_bundle_settings());
        },
    });

    return SwaggerUI;
});
