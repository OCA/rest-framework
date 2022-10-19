
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/rest-framework&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/rest-framework/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/rest-framework/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/rest-framework/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/rest-framework/actions/workflows/test.yml?query=branch%3A14.0)
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
[base_rest](base_rest/) | 14.0.4.7.2 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Develop your own high level REST APIs for Odoo thanks to this addon.
[base_rest_auth_api_key](base_rest_auth_api_key/) | 14.0.1.0.2 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Base Rest: Add support for the auth_api_key security policy into the openapi documentation
[base_rest_auth_jwt](base_rest_auth_jwt/) | 14.0.1.1.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Base Rest: Add support for the auth_jwt security policy into the openapi documentation
[base_rest_auth_user_service](base_rest_auth_user_service/) | 14.0.1.1.0 |  | Login/logout from session using a REST call
[base_rest_datamodel](base_rest_datamodel/) | 14.0.4.3.0 |  | Datamodel binding for base_rest
[base_rest_demo](base_rest_demo/) | 14.0.4.2.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Demo addon for Base REST
[base_rest_pydantic](base_rest_pydantic/) | 14.0.4.3.1 |  | Pydantic binding for base_rest
[datamodel](datamodel/) | 14.0.3.0.5 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | This addon allows you to define simple data models supporting serialization/deserialization
[extendable](extendable/) | 14.0.1.0.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Extendable classes registry loader for Odoo
[graphql_base](graphql_base/) | 14.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Base GraphQL/GraphiQL controller
[graphql_demo](graphql_demo/) | 14.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | GraphQL Demo
[model_serializer](model_serializer/) | 14.0.1.0.1 | [![fdegrave](https://github.com/fdegrave.png?size=30px)](https://github.com/fdegrave) | Automatically translate Odoo models into Datamodels for (de)serialization
[pydantic](pydantic/) | 14.0.1.1.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Utility addon to ease mapping between Pydantic and Odoo models
[rest_log](rest_log/) | 14.0.1.3.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Track REST API calls into DB

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
