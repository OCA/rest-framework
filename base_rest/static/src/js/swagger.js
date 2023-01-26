odoo.define("base_rest.swagger", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var SwaggerUi = require("base_rest.swagger_ui");

    publicWidget.registry.Swagger = publicWidget.Widget.extend({
        selector: "#swagger-ui",
        start: function () {
            var def = this._super.apply(this, arguments);
            var swagger_ui = new SwaggerUi("#swagger-ui");
            swagger_ui.start();
            return def;
        },
    });
});
