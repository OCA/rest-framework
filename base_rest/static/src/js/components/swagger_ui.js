/* global SwaggerUIBundle, SwaggerUIStandalonePreset, document, window */

const {Component, mount, onMounted, whenReady, xml} = owl;

class SwaggerUI extends Component {
    static template = xml`
        <t t-name="base_rest.swagger_ui">
          <div id="swagger-ui"/>
        </t>`;
    static props = {
        settings: {type: Object},
    };

    setup() {
        onMounted(() => {
            const settings = this._swagger_bundle_settings();
            SwaggerUIBundle(settings);
        });
    }

    _swagger_bundle_settings() {
        const defaults = {
            dom_id: "#swagger-ui",
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            plugins: [SwaggerUIBundle.plugins.DownloadUrl],
            layout: "StandaloneLayout",
            operationsSorter: (a, b) => {
                const methodsOrder = [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "trace",
                ];
                const order =
                    methodsOrder.indexOf(a.get("method")) -
                    methodsOrder.indexOf(b.get("method"));
                return order === 0 ? a.get("path").localeCompare(b.get("path")) : order;
            },
            tagsSorter: "alpha",
            onComplete: () => {
                const hasOdoobtn = document.querySelector(".swg-odoo-web-btn");
                if (!hasOdoobtn) {
                    const odooBtn = document.createElement("a");
                    odooBtn.className = "fa fa-th-large swg-odoo-web-btn";
                    odooBtn.href = "/web";
                    odooBtn.accessKey = "h";
                    document.querySelector(".topbar")?.prepend(odooBtn);
                }
            },
            oauth2RedirectUrl: `${window.location.origin}/base_rest/static/lib/swagger-ui-3.51.1/oauth2-redirect.html`,
        };
        return Object.assign({}, defaults, this.props.settings);
    }
}

(function () {
    "use strict";

    whenReady(() => {
        const swaggerUiEl = document.getElementById("swagger-ui");
        const settings = JSON.parse(swaggerUiEl.getAttribute("data-settings") || "{}");
        mount(SwaggerUI, swaggerUiEl, {props: {settings: settings}});
    });
})();
