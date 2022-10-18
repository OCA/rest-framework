[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/271/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-rest-framework-271)
[![Build Status](https://travis-ci.org/OCA/rest-framework.svg?branch=13.0)](https://travis-ci.org/OCA/rest-framework)
[![codecov](https://codecov.io/gh/OCA/rest-framework/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/rest-framework)

# REST Framework

This repo holds addons developed to ease the development of REST and GraphQL services into Odoo.

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_rest](base_rest/) | 13.0.3.1.3 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Develop your own high level REST APIs for Odoo thanks to this addon.
[base_rest_auth_user_service](base_rest_auth_user_service/) | 13.0.1.0.1 |  | Login/logout from session using a REST call
[base_rest_datamodel](base_rest_datamodel/) | 13.0.3.1.1 |  | Datamodel binding for base_rest
[base_rest_demo](base_rest_demo/) | 13.0.3.0.3 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Demo addon for Base REST
[base_rest_pydantic](base_rest_pydantic/) | 13.0.1.0.1 |  | Pydantic binding for base_rest
[datamodel](datamodel/) | 13.0.3.0.4 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | This addon allows you to define simple data models supporting serialization/deserialization
[extendable](extendable/) | 13.0.1.0.0 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Extendable classes registry loader for Odoo
[graphql_base](graphql_base/) | 13.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Base GraphQL/GraphiQL controller
[graphql_demo](graphql_demo/) | 13.0.1.0.1 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | GraphQL Demo
[model_serializer](model_serializer/) | 13.0.1.0.0 |  | Automatically translate Odoo models into Datamodels for (de)serialization
[pydantic](pydantic/) | 13.0.1.0.1 | [![lmignon](https://github.com/lmignon.png?size=30px)](https://github.com/lmignon) | Utility addon to ease mapping between Pydantic and Odoo models
[rest_log](rest_log/) | 13.0.1.4.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Track REST API calls into DB

[//]: # (end addons)

----

Here are the [Odoo Experience 2018 presentation](https://www.youtube.com/watch?v=kWlniXgM3Sc&index=8&list=PLgRkpfC5FsCzEid-KcHTorEymPNO8QeyI) and [slides](https://docs.google.com/presentation/d/e/2PACX-1vStBIMdVI8JeUL7Ac8GlplPlbLnE3ybcrrhzqxVhjFQa-wzU2BSvBUxqAq9vl9CLxqFYctmk7_ysUDZ/pub?start=true&loop=true&delayms=3000)
for `base_rest`.

Here is the [FOSDEM 2019](https://archive.fosdem.org/2019/schedule/event/python_discover_graphql/) presentation for `graphql_base`.

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
