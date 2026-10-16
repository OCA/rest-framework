import {registry} from "@web/core/registry";

registry
    .category("web_tour.tours")
    .add("base_rest.tour_api_docs_no_content_validation", {
        steps: () => [
            {
                trigger: "h4:contains('No API definition provided.')",
            },
        ],
    });

registry.category("web_tour.tours").add("base_rest.tour_api_docs_simple_api_endpoint", {
    steps: () => [
        {
            trigger: "span:contains('pod_bay_doors')",
        },
        {
            trigger:
                "span.opblock-summary-path[data-path='/control-panel/pod_bay_doors/open']",
            run: "click",
        },
        {
            trigger: "button.try-out__btn",
            run: "click",
        },
        {
            trigger: "button.execute",
            run: "click",
        },
        {
            trigger: "pre.microlight:contains('I'm sorry, Dave.')",
        },
    ],
});
