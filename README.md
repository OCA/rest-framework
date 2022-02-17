[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/271/14.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-rest-framework-271)
[![Build Status](https://travis-ci.com/OCA/rest-framework.svg?branch=14.0)](https://travis-ci.com/OCA/rest-framework)
[![codecov](https://codecov.io/gh/OCA/rest-framework/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/rest-framework)
[![Translation Status](https://translation.odoo-community.org/widgets/rest-framework-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/rest-framework-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# REST frameworks

This repo holds addons developed to ease the development of REST services into Odoo.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_rest](base_rest/) | 14.0.4.5.1 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Develop your own high level REST APIs for Odoo thanks to this addon.
[base_rest_auth_api_key](base_rest_auth_api_key/) | 14.0.1.0.2 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Base Rest: Add support for the auth_api_key security policy into the openapi documentation
[base_rest_auth_jwt](base_rest_auth_jwt/) | 14.0.1.1.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Base Rest: Add support for the auth_jwt security policy into the openapi documentation
[base_rest_auth_user_service](base_rest_auth_user_service/) | 14.0.1.1.0 |  | Login/logout from session using a REST call
[base_rest_datamodel](base_rest_datamodel/) | 14.0.4.1.0 |  | Datamodel binding for base_rest
[base_rest_demo](base_rest_demo/) | 14.0.4.1.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Demo addon for Base REST
[datamodel](datamodel/) | 14.0.3.0.5 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | This addon allows you to define simple data models supporting serialization/deserialization
[extendable](extendable/) | 14.0.1.0.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Extendable classes registry loader for Odoo
[graphql_base](graphql_base/) | 14.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Base GraphQL/GraphiQL controller
[graphql_demo](graphql_demo/) | 14.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | GraphQL Demo
[model_serializer](model_serializer/) | 14.0.1.0.0 |  | Automatically translate Odoo models into Datamodels for (de)serialization
[rest_log](rest_log/) | 14.0.1.1.2 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Track REST API calls into DB

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
