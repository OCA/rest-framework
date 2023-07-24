What's building an API with fastapi?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FastAPI is a modern, fast (high-performance), web framework for building APIs
with Python 3.7+ based on standard Python type hints. This addons let's you
keep advantage of the fastapi framework and use it with Odoo.

Before you start, we must define some terms:

* **App**: A FastAPI app is a collection of routes, dependencies, and other
  components that can be used to build a web application.
* **Router**: A router is a collection of routes that can be mounted in an
  app.
* **Route**: A route is a mapping between an HTTP method and a path, and
  defines what should happen when the user requests that path.
* **Dependency**: A dependency is a callable that can be used to get some
  information from the user request, or to perform some actions before the
  request handler is called.
* **Request**: A request is an object that contains all the information
  sent by the user's browser as part of an HTTP request.
* **Response**: A response is an object that contains all the information
  that the user's browser needs to build the result page.
* **Handler**: A handler is a function that takes a request and returns a
  response.
* **Middleware**: A middleware is a function that takes a request and a
  handler, and returns a response.

The FastAPI framework is based on the following principles:

* **Fast**: Very high performance, on par with NodeJS and Go (thanks to Starlette
  and Pydantic). [One of the fastest Python frameworks available]
* **Fast to code**: Increase the speed to develop features by about 200% to 300%.
* **Fewer bugs**: Reduce about 40% of human (developer) induced errors.
* **Intuitive**: Great editor support. Completion everywhere. Less time
  debugging.
* **Easy**: Designed to be easy to use and learn. Less time reading docs.
* **Short**: Minimize code duplication. Multiple features from each parameter
  declaration. Fewer bugs.
* **Robust**: Get production-ready code. With automatic interactive documentation.
* **Standards-based**: Based on (and fully compatible with) the open standards
  for APIs: OpenAPI (previously known as Swagger) and JSON Schema.
* **Open Source**: FastAPI is fully open-source, under the MIT license.

The first step is to install the fastapi addon. You can do it with the
following command:

    $ pip install odoo-addon-fastapi

Once the addon is installed, you can start building your API. The first thing
you need to do is to create a new addon that depends on 'fastapi'. For example,
let's create an addon called *my_demo_api*.

Then, you need to declare your app by defining a model that inherits from
'fastapi.endpoint' and add your app name into the app field. For example:

.. code-block:: python

    from odoo import fields, models

    class FastapiEndpoint(models.Model):

        _inherit = "fastapi.endpoint"

        app: str = fields.Selection(
            selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
        )

The **'fastapi.endpoint'** model is the base model for all the endpoints. An endpoint
instance is the mount point for a fastapi app into Odoo. When you create a new
endpoint, you can define the app that you want to mount in the **'app'** field
and the path where you want to mount it in the **'path'** field.

figure:: static/description/endpoint_create.png

    FastAPI Endpoint

Thanks to the **'fastapi.endpoint'** model, you can create as many endpoints as
you want and mount as many apps as you want in each endpoint. The endpoint is
also the place where you can define configuration parameters for your app. A
typical example is the authentication method that you want to use for your app
when accessed at the endpoint path.

Now, you can create your first router. For that, you need to define a global
variable into your fastapi_endpoint module called for example 'demo_api_router'

.. code-block:: python

    from fastapi import APIRouter
    from odoo import fields, models

    class FastapiEndpoint(models.Model):

        _inherit = "fastapi.endpoint"

        app: str = fields.Selection(
            selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
        )

    # create a router
    demo_api_router = APIRouter()


To make your router available to your app, you need to add it to the list of routers
returned by the **_get_fastapi_routers** method of your fastapi_endpoint model.

.. code-block:: python

    from fastapi import APIRouter
    from odoo import api, fields, models

    class FastapiEndpoint(models.Model):

        _inherit = "fastapi.endpoint"

        app: str = fields.Selection(
            selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
        )

        def _get_fastapi_routers(self):
            if self.app == "demo":
                return [demo_api_router]
            return super()._get_fastapi_routers()

    # create a router
    demo_api_router = APIRouter()

Now, you can start adding routes to your router. For example, let's add a route
that returns a list of partners.

.. code-block:: python

    from typing import Annotated

    from fastapi import APIRouter
    from pydantic import BaseModel

    from odoo import api, fields, models
    from odoo.api import Environment

    from odoo.addons.fastapi.dependencies import odoo_env

    class FastapiEndpoint(models.Model):

        _inherit = "fastapi.endpoint"

        app: str = fields.Selection(
            selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
        )

        def _get_fastapi_routers(self):
            if self.app == "demo":
                return [demo_api_router]
            return super()._get_fastapi_routers()

    # create a router
    demo_api_router = APIRouter()

    class PartnerInfo(BaseModel):
        name: str
        email: str

    @demo_api_router.get("/partners", response_model=list[PartnerInfo])
    def get_partners(env: Annotated[Environment, Depends(odoo_env)]) -> list[PartnerInfo]:
        return [
            PartnerInfo(name=partner.name, email=partner.email)
            for partner in env["res.partner"].search([])
        ]

Now, you can start your Odoo server, install your addon and create a new endpoint
instance for your app. Once it's done click on the docs url to access the
interactive documentation of your app.

Before trying to test your app, you need to define on the endpoint instance the
user that will be used to run the app. You can do it by setting the **'user_id'**
field. This information is the most important one because it's the basis for
the security of your app. The user that you define in the endpoint instance
will be used to run the app and to access the database. This means that the
user will be able to access all the data that he has access to in Odoo. To ensure
the security of your app, you should create a new user that will be used only
to run your app and that will have no access to the database.

.. code-block:: xml

  <record
        id="my_demo_app_user"
        model="res.users"
        context="{'no_reset_password': True, 'no_reset_password': True}"
    >
    <field name="name">My Demo Endpoint User</field>
    <field name="login">my_demo_app_user</field>
    <field name="groups_id" eval="[(6, 0, [])]" />
  </record>

At the same time you should create a new group that will be used to define the
access rights of the user that will run your app. This group should imply
the predefined group **'FastAPI Endpoint Runner'**. This group defines the
minimum access rights that the user needs to:

* access the endpoint instance it belongs to
* access to its own user record
* access to the partner record that is linked to its user record

.. code-block:: xml

  <record id="my_demo_app_group" model="res.groups">
    <field name="name">My Demo Endpoint Group</field>
    <field name="users" eval="[(4, ref('my_demo_app_user'))]" />
    <field name="implied_ids" eval="[(4, ref('fastapi.group_fastapi_endpoint_runner'))]" />
  </record>


Now, you can test your app. You can do it by clicking on the 'Try it out' button
of the route that you have defined. The result of the request will be displayed
in the 'Response' section and contains the list of partners.

.. note::
  The **'FastAPI Endpoint Runner'** group ensures that the user cannot access any
  information others than the 3 ones mentioned above. This means that for every
  information that you want to access from your app, you need to create the
  proper ACLs and record rules. (see `Managing security into the route handlers`_)
  It's a good practice to use a dedicated user into a specific group from the
  beginning of your project and in your tests. This will force you to define
  the proper security rules for your endoints.

Dealing with the odoo environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **'odoo.addons.fastapi.dependencies'** module provides a set of functions that you can use
to inject reusable dependencies into your routes. For example, the **'odoo_env'**
function returns the current odoo environment. You can use it to access the
odoo models and the database from your route handlers.

.. code-block:: python

    from typing import Annotated

    from odoo.api import Environment
    from odoo.addons.fastapi.dependencies import odoo_env

    @demo_api_router.get("/partners", response_model=list[PartnerInfo])
    def get_partners(env: Annotated[Environment, Depends(odoo_env)]) -> list[PartnerInfo]:
        return [
            PartnerInfo(name=partner.name, email=partner.email)
            for partner in env["res.partner"].search([])
        ]

As you can see, you can use the **'Depends'** function to inject the dependency
into your route handler. The **'Depends'** function is provided by the
**'fastapi'** framework. You can use it to inject any dependency into your route
handler. As your handler is a python function, the only way to get access to
the odoo environment is to inject it as a dependency. The fastapi addon provides
a set of function that can be used as dependencies:

* **'odoo_env'**: Returns the current odoo environment.
* **'fastapi_endpoint'**: Returns the current fastapi endpoint model instance.
* **'authenticated_partner'**: Returns the authenticated partner.
* **'authenticated_partner_env'**: Returns the current odoo environment with the
  authenticated_partner_id into the context.

By default, the **'odoo_env'** and **'fastapi_endpoint'** dependencies are
available without extra work.

.. note::
  Even if 'odoo_env' and 'authenticated_partner_env' returns the current odoo
  environment, they are not the same. The 'odoo_env' dependency returns the
  environment without any modification while the 'authenticated_partner_env'
  adds the authenticated partner id into the context of the environment. As it will
  be explained in the section `Managing security into the route handlers`_ dedicated
  to the security, the presence of the authenticated partner id into the context
  is the key information that will allow you to enforce the security of your endpoint
  methods. As consequence, you should always use the 'authenticated_partner_env'
  dependency instead of the 'odoo_env' dependency for all the methods that are
  not public.

The dependency injection mechanism
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **'odoo_env'** dependency relies on a simple implementation that retrieves
the current odoo environment from ContextVar variable initialized at the start
of the request processing by the specific request dispatcher processing the
fastapi requests.

The **'fastapi_endpoint'** dependency relies on the 'dependency_overrides' mechanism
provided by the **'fastapi'** module. (see the fastapi documentation for more
details about the dependency_overrides mechanism). If you take a look at the
current implementation of the **'fastapi_endpoint'** dependency, you will see
that the method depends of two parameters: **'endpoint_id'** and **'env'**. Each
of these parameters are dependencies themselves.

.. code-block:: python

    def fastapi_endpoint_id() -> int:
        """This method is overriden by default to make the fastapi.endpoint record
        available for your endpoint method. To get the fastapi.endpoint record
        in your method, you just need to add a dependency on the fastapi_endpoint method
        defined below
        """


    def fastapi_endpoint(
        _id: Annotated[int, Depends(fastapi_endpoint_id)],
        env: Annotated[Environment, Depends(odoo_env)],
    ) -> "FastapiEndpoint":
        """Return the fastapi.endpoint record"""
        return env["fastapi.endpoint"].browse(_id)


As you can see, one of these dependencies is the **'fastapi_endpoint_id'**
dependency and has no concrete implementation. This method is used as a contract
that must be implemented/provided at the time the fastapi app is created.
Here comes the power of the dependency_overrides mechanism.

If you take a look at the **'_get_app'** method of the **'FastapiEndpoint'** model,
you will see that the **'fastapi_endpoint_id'** dependency is overriden by
registering a specific method that returns the id of the current fastapi endpoint
model instance for the original method.

.. code-block:: python

    def _get_app(self) -> FastAPI:
        app = FastAPI(**self._prepare_fastapi_endpoint_params())
        for router in self._get_fastapi_routers():
            app.include_router(prefix=self.root_path, router=router)
        app.dependency_overrides[dependencies.fastapi_endpoint_id] = partial(
            lambda a: a, self.id
        )

This kind of mechanism is very powerful and allows you to inject any dependency
into your route handlers and moreover, define an abstract dependency that can be
used by any other addon and for which the implementation could depend on the
endpoint configuration.

The authentication mechanism
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make our app not tightly coupled with a specific authentication mechanism,
we will use the **'authenticated_partner'** dependency. As for the
**'fastapi_endpoint'** this dependency depends on an abstract dependency.

When you define a route handler, you can inject the **'authenticated_partner'**
dependency as a parameter of your route handler.

.. code-block:: python

    from odoo.addons.base.models.res_partner import Partner


    @demo_api_router.get("/partners", response_model=list[PartnerInfo])
    def get_partners(
        env: Annotated[Environment, Depends(odoo_env)], partner: Annotated[Partner, Depends(authenticated_partner)]
    ) -> list[PartnerInfo]:
        return [
            PartnerInfo(name=partner.name, email=partner.email)
            for partner in env["res.partner"].search([])
        ]


At this stage, your handler is not tied to a specific authentication mechanism
but only expects to get a partner as a dependency. Depending on your needs, you
can implement different authentication mechanism available for your app.
The fastapi addon provides a default authentication mechanism using the
'BasicAuth' method. This authentication mechanism is implemented in the
**'odoo.addons.fastapi.dependencies'** module and relies on functionalities provided
by the **'fastapi.security'** module.

.. code-block:: python

      def authenticated_partner(
          env: Annotated[Environment, Depends(odoo_env)],
          security: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())],
      ) -> "res.partner":
          """Return the authenticated partner"""
          partner = env["res.partner"].search(
              [("email", "=", security.username)], limit=1
          )
          if not partner:
              raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid authentication credentials",
                  headers={"WWW-Authenticate": "Basic"},
              )
          if not partner.check_password(security.password):
              raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid authentication credentials",
                  headers={"WWW-Authenticate": "Basic"},
              )
          return partner

As you can see, the **'authenticated_partner'** dependency relies on the
**'HTTPBasic'** dependency provided by the **'fastapi.security'** module.
In this dummy implementation, we just check that the provided credentials
can be used to authenticate a user in odoo. If the authentication is successful,
we return the partner record linked to the authenticated user.

In some cases you could want to implement a more complex authentication mechanism
that could rely on a token or a session. In this case, you can override the
**'authenticated_partner'** dependency by registering a specific method that
returns the authenticated partner. Moreover, you can make it configurable on
the fastapi endpoint model instance.

To do it, you just need to implement a specific method for each of your
authentication mechanism and allows the user to select one of these methods
when he creates a new fastapi endpoint. Let's say that we want to allow the
authentication by using an api key or via basic auth. Since basic auth is already
implemented, we will only implement the api key authentication mechanism.

.. code-block:: python

  from fastapi.security import APIKeyHeader

  def api_key_based_authenticated_partner_impl(
      api_key: Annotated[str, Depends(
          APIKeyHeader(
              name="api-key",
              description="In this demo, you can use a user's login as api key.",
          )
      )],
      env: Annotated[Environment, Depends(odoo_env)],
  ) -> Partner:
      """A dummy implementation that look for a user with the same login
      as the provided api key
      """
      partner = env["res.users"].search([("login", "=", api_key)], limit=1).partner_id
      if not partner:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
          )
      return partner

As for the 'BasicAuth' authentication mechanism, we also rely on one of the native
security dependency provided by the **'fastapi.security'** module.

Now that we have an implementation for our two authentication mechanisms, we
can allows the user to select one of these authentication mechanisms by adding
a selection field on the fastapi endpoint model.

.. code-block:: python

  from odoo import fields, models

  class FastapiEndpoint(models.Model):

      _inherit = "fastapi.endpoint"

      app: str = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
      )
      demo_auth_method = fields.Selection(
          selection=[("api_key", "Api Key"), ("http_basic", "HTTP Bacic")],
          string="Authenciation method",
      )

.. note::
  A good practice is to prefix specific configuration fields of your app with
  the name of your app. This will avoid conflicts with other app when the
  'fastapi.endpoint' model is extended for other 'app'.

Now that we have a selection field that allows the user to select the
authentication method, we can use the dependency override mechanism to
provide the right implementation of the **'authenticated_partner'** dependency
when the app is instantiated.

.. code-block:: python

  from odoo.addons.fastapi.dependencies import authenticated_partner
  class FastapiEndpoint(models.Model):

      _inherit = "fastapi.endpoint"

      app: str = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
      )
      demo_auth_method = fields.Selection(
          selection=[("api_key", "Api Key"), ("http_basic", "HTTP Bacic")],
          string="Authenciation method",
      )

    def _get_app(self) -> FastAPI:
        app = super()._get_app()
        if self.app == "demo":
            # Here we add the overrides to the authenticated_partner_impl method
            # according to the authentication method configured on the demo app
            if self.demo_auth_method == "http_basic":
                authenticated_partner_impl_override = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                authenticated_partner_impl_override = (
                    api_key_based_authenticated_partner_impl
                )
            app.dependency_overrides[
                authenticated_partner_impl
            ] = authenticated_partner_impl_override
        return app


To see how the dependency override mechanism works, you can take a look at the
demo app provided by the fastapi addon. If you choose the app 'demo' in the
fastapi endpoint form view, you will see that the authentication method
is configurable. You can also see that depending on the authentication method
configured on your fastapi endpoint, the documentation will change.

.. note::
  At time of writing, the dependency override mechanism is not supported by
  the fastapi documentation generator. A fix has been proposed and is waiting
  to be merged. You can follow the progress of the fix on `github
  <https://github.com/tiangolo/fastapi/pull/5452>`_

Managing configuration parameters for your app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we have seen in the previous section, you can add configuration fields
on the fastapi endpoint model to allow the user to configure your app (as for
any odoo model you extend). When you need to access these configuration fields
in your route handlers, you can use the **'odoo.addons.fastapi.dependencies.fastapi_endpoint'**
dependency method to retrieve the 'fastapi.endpoint' record associated to the
current request.

.. code-block:: python

  from pydantic import BaseModel, Field
  from odoo.addons.fastapi.dependencies import fastapi_endpoint

  class EndpointAppInfo(BaseModel):
    id: str
    name: str
    app: str
    auth_method: str = Field(alias="demo_auth_method")
    root_path: str
    model_config = ConfigDict(from_attributes=True)


    @demo_api_router.get(
        "/endpoint_app_info",
        response_model=EndpointAppInfo,
        dependencies=[Depends(authenticated_partner)],
    )
    async def endpoint_app_info(
        endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    ) -> EndpointAppInfo:
        """Returns the current endpoint configuration"""
        # This method show you how to get access to current endpoint configuration
        # It also show you how you can specify a dependency to force the security
        # even if the method doesn't require the authenticated partner as parameter
        return EndpointAppInfo.model_validate(endpoint)

Some of the configuration fields of the fastapi endpoint could impact the way
the app is instantiated. For example, in the previous section, we have seen
that the authentication method configured on the 'fastapi.endpoint' record is
used in order to provide the right implementation of the **'authenticated_partner'**
when the app is instantiated. To ensure that the app is re-instantiated when
an element of the configuration used in the instantiation of the app is
modified, you must override the **'_fastapi_app_fields'** method to add the
name of the fields that impact the instantiation of the app into the returned
list.

.. code-block:: python

  class FastapiEndpoint(models.Model):

      _inherit = "fastapi.endpoint"

      app: str = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
      )
      demo_auth_method = fields.Selection(
          selection=[("api_key", "Api Key"), ("http_basic", "HTTP Bacic")],
          string="Authenciation method",
      )

      @api.model
      def _fastapi_app_fields(self) -> List[str]:
          fields = super()._fastapi_app_fields()
          fields.append("demo_auth_method")
          return fields

Dealing with languages
~~~~~~~~~~~~~~~~~~~~~~

The fastapi addon parses the Accept-Language header of the request to determine
the language to use. This parsing is done by respecting the `RFC 7231 specification
<https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.5>`_. That means that
the language is determined by the first language found in the header that is
supported by odoo (with care of the priority order). If no language is found in
the header, the odoo default language is used. This language is then used to
initialize the Odoo's environment context used by the route handlers. All this
makes the management of languages very easy. You don't have to worry about. This
feature is also documented by default into the generated openapi documentation
of your app to instruct the api consumers how to request a specific language.


How to extend an existing app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you develop a fastapi app, in a native python app it's not possible
to extend an existing one. This limitation doesn't apply to the fastapi addon
because the fastapi endpoint model is designed to be extended. However, the
way to extend an existing app is not the same as the way to extend an odoo model.

First of all, it's important to keep in mind that when you define a route, you
are actually defining a contract between the client and the server. This
contract is defined by the route path, the method (GET, POST, PUT, DELETE,
etc.), the parameters and the response. If you want to extend an existing app,
you must ensure that the contract is not broken. Any change to the contract
will respect the `Liskov substitution principle
<https://en.wikipedia.org/wiki/Liskov_substitution_principle>`_. This means
that the client should not be impacted by the change.

What does it mean in practice? It means that you can't change the route path
or the method of an existing route. You can't change the name of a parameter
or the type of a response. You can't add a new parameter or a new response.
You can't remove a parameter or a response. If you want to change the contract,
you must create a new route.

What can you change?

* You can change the implementation of the route handler.
* You can override the dependencies of the route handler.
* You can add a new route handler.
* You can extend the model used as parameter or as response of the route handler.

Let's see how to do that.

Changing the implementation of the route handler
================================================

Let's say that you want to change the implementation of the route handler
**'/demo/echo'**. Since a route handler is just a python method, it could seems
a tedious task since we are not into a model method and therefore we can't
take advantage of the Odoo inheritance mechanism.

However, the fastapi addon provides a way to do that. Thanks to the **'odoo_env'**
dependency method, you can access the current odoo environment. With this
environment, you can access the registry and therefore the model you want to
delegate the implementation to. If you want to change the implementation of
the route handler **'/demo/echo'**, the only thing you have to do is to
inherit from the model where the implementation is defined and override the
method **'echo'**.

.. code-block:: python

  from pydantic import BaseModel
  from fastapi import Depends, APIRouter
  from odoo import models
  from odoo.addons.fastapi.dependencies import odoo_env

  class FastapiEndpoint(models.Model):

      _inherit = "fastapi.endpoint"

      def _get_fastapi_routers(self) -> List[APIRouter]:
          routers = super()._get_fastapi_routers()
          routers.append(demo_api_router)
          return routers

  demo_api_router = APIRouter()

  @demo_api_router.get(
      "/echo",
      response_model=EchoResponse,
      dependencies=[Depends(odoo_env)],
  )
  async def echo(
      message: str,
      odoo_env: Annotated[Environment, Depends(odoo_env)],
  ) -> EchoResponse:
      """Echo the message"""
      return EchoResponse(message=odoo_env["demo.fastapi.endpoint"].echo(message))

  class EchoResponse(BaseModel):
      message: str

  class DemoEndpoint(models.AbstractModel):

      _name = "demo.fastapi.endpoint"
      _description = "Demo Endpoint"

      def echo(self, message: str) -> str:
          return message

  class DemoEndpointInherit(models.AbstractModel):

      _inherit = "demo.fastapi.endpoint"

      def echo(self, message: str) -> str:
          return f"Hello {message}"


.. note::

  It's a good programming practice to implement the business logic outside
  the route handler. This way, you can easily test your business logic without
  having to test the route handler. In the example above, the business logic
  is implemented in the method **'echo'** of the model **'demo.fastapi.endpoint'**.
  The route handler just delegate the implementation to this method.


Overriding the dependencies of the route handler
================================================

As you've previously seen, the dependency injection mechanism of fastapi is
very powerful. By designing your route handler to rely on dependencies with
a specific functional scope, you can easily change the implementation of the
dependency without having to change the route handler. With such a design, you
can even define abstract dependencies that must be implemented by the concrete
application. This is the case of the **'authenticated_partner'** dependency in our
previous example. (you can find the implementation of this dependency in the
file **'odoo/addons/fastapi/dependencies.py'** and it's usage in the file
**'odoo/addons/fastapi/models/fastapi_endpoint_demo.py'**)

Adding a new route handler
==========================

Let's say that you want to add a new route handler **'/demo/echo2'**.
You could be tempted to add this new route handler in your new addons by
importing the router of the existing app and adding the new route handler to
it.

.. code-block:: python

  from odoo.addons.fastapi.models.fastapi_endpoint_demo import demo_api_router

  @demo_api_router.get(
      "/echo2",
      response_model=EchoResponse,
      dependencies=[Depends(odoo_env)],
  )
  async def echo2(
      message: str,
      odoo_env: Annotated[Environment, Depends(odoo_env)],
  ) -> EchoResponse:
      """Echo the message"""
      echo = odoo_env["demo.fastapi.endpoint"].echo2(message)
      return EchoResponse(message=f"Echo2: {echo}")

The problem with this approach is that you unconditionally add the new route
handler to the existing app even if the app is called for a different database
where your new addon is not installed.

The solution is to define a new router and to add it to the list of routers
returned by the method **'_get_fastapi_routers'** of the model
**'fastapi.endpoint'** you are inheriting from into your new addon.

.. code-block:: python

  class FastapiEndpoint(models.Model):

      _inherit = "fastapi.endpoint"

      def _get_fastapi_routers(self) -> List[APIRouter]:
          routers = super()._get_fastapi_routers()
          if self.app == "demo":
              routers.append(additional_demo_api_router)
          return routers

  additional_demo_api_router = APIRouter()

  @additional_demo_api_router.get(
      "/echo2",
      response_model=EchoResponse,
      dependencies=[Depends(odoo_env)],
  )
  async def echo2(
      message: str,
      odoo_env: Annotated[Environment, Depends(odoo_env)],
  ) -> EchoResponse:
      """Echo the message"""
      echo = odoo_env["demo.fastapi.endpoint"].echo2(message)
      return EchoResponse(message=f"Echo2: {echo}")


In this way, the new router is added to the list of routers of your app only if
the app is called for a database where your new addon is installed.

Extending the model used as parameter or as response of the route handler
=========================================================================

The fastapi python library uses the pydantic library to define the models. By
default, once a model is defined, it's not possible to extend it. However, a
companion python library called
`extendable_pydantic <https://pypi.org/project/extendable_pydantic/>`_ provides
a way to use inheritance with pydantic models to extend an existing model. If
used alone, it's your responsibility to instruct this library the list of
extensions to apply to a model and the order to apply them. This is not very
convenient. Fortunately, an dedicated odoo addon exists to make this process
complete transparent. This addon is called
`odoo-addon-extendable-fastapi <https://pypi.org/project/odoo-addon-extendable-fastapi/>`_.

When you want to allow other addons to extend a pydantic model, you must
first define the model as an extendable model by using a dedicated metaclass

.. code-block:: python

  from pydantic import BaseModel
  from extendable_pydantic import ExtendableModelMeta

  class Partner(BaseModel, metaclass=ExtendableModelMeta):
    name = 0.1
    model_config = ConfigDict(from_attributes=True)

As any other pydantic model, you can now use this model as parameter or as response
of a route handler. You can also use all the features of models defined with
pydantic.

.. code-block:: python

  @demo_api_router.get(
      "/partner",
      response_model=Location,
      dependencies=[Depends(authenticated_partner)],
  )
  async def partner(
      partner: Annotated[ResPartner, Depends(authenticated_partner)],
  ) -> Partner:
      """Return the location"""
      return Partner.model_validate(partner)


If you need to add a new field into the model **'Partner'**, you can extend it
in your new addon by defining a new model that inherits from the model **'Partner'**.

.. code-block:: python

  from typing import Optional
  from odoo.addons.fastapi.models.fastapi_endpoint_demo import Partner

  class PartnerExtended(Partner, extends=Partner):
      email: Optional[str]

If your new addon is installed in a database, a call to the route handler
**'/demo/partner'** will return a response with the new field **'email'** if a
value is provided by the odoo record.

.. code-block:: python

  {
    "name": "John Doe",
    "email": "jhon.doe@acsone.eu"
  }

If your new addon is not installed in a database, a call to the route handler
**'/demo/partner'** will only return the name of the partner.

.. code-block:: python

  {
    "name": "John Doe"
  }

.. note::

  The liskov substitution principle has also to be respected. That means that
  if you extend a model, you must add new required fields or you must provide
  default values for the new optional fields.

Managing security into the route handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default the route handlers are processed using the user configured on the
**'fastapi.endpoint'** model instance. (default is the Public user).
You have seen previously how to define a dependency that will be used to enforce
the authentication of a partner. When a method depends on this dependency, the
'authenticated_partner_id' key is added to the context of the partner environment.
(If you don't need the partner as dependency but need to get an environment
with the authenticated user, you can use the dependency 'authenticated_partner_env' instead of
'authenticated_partner'.)

The fastapi addon extends the 'ir.rule' model to add into the evaluation context
of the security rules the key 'authenticated_partner_id' that contains the id
of the authenticated partner.

As briefly introduced in a previous section, a good practice when you develop a
fastapi app and you want to protect your data in an efficient and traceable way is to:

* create a new user specific to the app but with any access rights.
* create a security group specific to the app and add the user to this group. (This
  group must implies the group 'AFastAPI Endpoint Runner' that give the
  minimal access rights)
* for each model you want to protect:

  * add a 'ir.model.access' record for the model to allow read access to your model
    and add the group to the record.
  * create a new 'ir.rule' record for the model that restricts the access to the
    records of the model to the authenticated partner by using the key
    'authenticated_partner_id' in domain of the rule. (or to the user defined on
    the 'fastapi.endpoint' model instance if the method is public)

* add a dependency on the 'authenticated_partner' to your handlers when you need
  to access the authenticated partner or ensure that the service is called by an
  authenticated partner.

.. code-block:: xml

  <record
        id="my_demo_app_user"
        model="res.users"
        context="{'no_reset_password': True, 'no_reset_password': True}"
    >
    <field name="name">My Demo Endpoint User</field>
    <field name="login">my_demo_app_user</field>
    <field name="groups_id" eval="[(6, 0, [])]" />
  </record>

  <record id="my_demo_app_group" model="res.groups">
    <field name="name">My Demo Endpoint Group</field>
    <field name="users" eval="[(4, ref('my_demo_app_user'))]" />
    <field name="implied_ids" eval="[(4, ref('group_fastapi_endpoint_runner'))]" />
  </record>

  <!-- acl for the model 'sale.order' -->
  <record id="sale_order_demo_app_access" model="ir.model.access">
    <field name="name">My Demo App: access to sale.order</field>
    <field name="model_id" ref="model_sale_order"/>
    <field name="group_id" ref="my_demo_app_group"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
  </record>

  <!-- a record rule to allows the authenticated partner to access only its sale orders -->
  <record id="demo_app_sale_order_rule" model="ir.rule">
    <field name="name">Sale Order Rule</field>
    <field name="model_id" ref="model_sale_order"/>
    <field name="domain_force">[('partner_id', '=', authenticated_partner_id)]</field>
    <field name="groups" eval="[(4, ref('my_demo_app_group'))]"/>
  </record>

How to test your fastapi app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thanks to the starlette test client, it's possible to test your fastapi app
in a very simple way. With the test client, you can call your route handlers
as if they were real http endpoints. The test client is available in the
**'fastapi.testclient'** module.

Once again the dependency injection mechanism comes to the rescue by allowing
you to inject into the test client specific implementations of the dependencies
normally provided by the normal processing of the request by the fastapi app.
(for example, you can inject a mock of the dependency 'authenticated_partner'
to test the behavior of your route handlers when the partner is not authenticated,
you can also inject a mock for the odoo_env etc...)

The fastapi addon provides a base class for the test cases that you can use to
write your tests. This base class is **'odoo.fastapi.tests.common.FastAPITransactionCase'**.
This class mainly provides the method **'_create_test_client'** that you can
use to create a test client for your fastapi app. This method encapsulates the
creation of the test client and the injection of the dependencies. It also
ensures that the odoo environment is make available into the context of the
route handlers. This method is designed to be used when you need to test your
app or when you need to test a specific router (It's therefore easy to defines
tests for routers in an addon that doesn't provide a fastapi endpoint).

With this base class, writing a test for a route handler is as simple as:

.. code-block:: python

  from odoo.fastapi.tests.common import FastAPITransactionCase

  from odoo.addons.fastapi import dependencies
  from odoo.addons.fastapi.routers import demo_router

  class FastAPIDemoCase(FastAPITransactionCase):

      @classmethod
      def setUpClass(cls) -> None:
          super().setUpClass()
          cls.default_fastapi_running_user = cls.env.ref("fastapi.my_demo_app_user")
          cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create({"name": "FastAPI Demo"})

      def test_hello_world(self) -> None:
          with self._create_test_client(router=demo_router) as test_client:
              response: Response = test_client.get("/demo/")
          self.assertEqual(response.status_code, status.HTTP_200_OK)
          self.assertDictEqual(response.json(), {"Hello": "World"})


In the previous example, we created a test client for the demo_router. We could
have created a test client for the whole app by not specifying the router but
the app instead.

.. code-block:: python

  from odoo.fastapi.tests.common import FastAPITransactionCase

  from odoo.addons.fastapi import dependencies
  from odoo.addons.fastapi.routers import demo_router

  class FastAPIDemoCase(FastAPITransactionCase):

      @classmethod
      def setUpClass(cls) -> None:
          super().setUpClass()
          cls.default_fastapi_running_user = cls.env.ref("fastapi.my_demo_app_user")
          cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create({"name": "FastAPI Demo"})

      def test_hello_world(self) -> None:
          demo_endpoint = self.env.ref("fastapi.fastapi_endpoint_demo")
          with self._create_test_client(app=demo_endpoint._get_app()) as test_client:
              response: Response = test_client.get(f"{demo_endpoint.root_path}/demo/")
          self.assertEqual(response.status_code, status.HTTP_200_OK)
          self.assertDictEqual(response.json(), {"Hello": "World"})


Overall considerations when you develop an fastapi app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Developing a fastapi app requires to follow some good practices to ensure that
the app is robust and easy to maintain. Here are some of them:

* A route handler must be as simple as possible. It must not contain any
  business logic. The business logic must be implemented into the service
  layer. The route handler must only call the service layer and return the
  result of the service layer. To ease extension on your business logic, your
  service layer can be implemented as an odoo abstract model that can be
  inherited by other addons.

* A route handler should not expose the internal data structure and api of Odoo.
  It should provide the api that is needed by the client. More widely, an app
  provides a set of services that address a set of use cases specific to
  a well defined functional domain. You must always keep in mind that your api
  will remain the same for a long time even if you upgrade your odoo version
  of modify your business logic.

* A route handler is a transactional unit of work. When you design your api
  you must ensure that the completeness of a use case is guaranteed by a single
  transaction. If you need to perform several transactions to complete a use
  case, you introduce a risk of inconsistency in your data or extra complexity
  in your client code.

* Properly handle the errors. The route handler must return a proper error
  response when an error occurs. The error response must be consistent with
  the rest of the api. The error response must be documented in the api
  documentation. By default, the **'odoo-addon-fastapi'** module handles
  the common exception types defined in the **'odoo.exceptions'** module
  and returns a proper error response with the corresponding http status code.
  An error in the route handler must always return an error response with a
  http status code different from 200. The error response must contain a
  human readable message that can be displayed to the user. The error response
  can also contain a machine readable code that can be used by the client to
  handle the error in a specific way.

* When you design your json document through the pydantic models, you must
  use the appropriate data types. For example, you must use the data type
  **'datetime.date'** to represent a date and not a string. You must also
  properly define the constraints on the fields. For example, if a field
  is optional, you must use the data type **'typing.Optional'**.
  `pydantic`_ provides everything you need to
  properly define your json document.

* Always use an appropriate pydantic model as request and/or response for
  your route handler. Constraints on the fields of the pydantic model must
  apply to the specific use case. For example, if your route handler is used
  to create a sale order, the pydantic model must not contain the field
  'id' because the id of the sale order will be generated by the route handler.
  But if the id is required afterwords, the pydantic model for the response
  must contain the field 'id' as required.

* Uses descriptive property names in your json documents. For example, avoid the
  use of documents providing a flat list of key value pairs.

* Be consistent in the naming of your fields into your json documents. For example,
  if you use 'id' to represent the id of a sale order, you must use 'id' to represent
  the id of all the other objects.

* Be consistent in the naming style of your fields. Always prefer underscore
  to camel case.

* Always use plural for the name of the fields that contain a list of items.
  For example, if you have a field 'lines' that contains a list of sale order
  lines, you must use 'lines' and not 'line'.

* You can't expect that a client will provide you the identifier of a specific
  record in odoo (for example the id of a carrier) if you don't provide a
  specific route handler to retrieve the list of available records. Sometimes,
  the client must share with odoo the identity of a specific record to be
  able to perform an appropriate action specific to this record (for example,
  the processing of a payment is different for each payment acquirer). In this
  case, you must provide a specific attribute that allows both the client and
  odoo to identify the record. The field 'provider' on a payment acquirer allows
  you to identify a specific record in odoo. This kind of approach
  allows both the client and odoo to identify the record without having to rely
  on the id of the record. (This will ensure that the client will not break
  if the id of the record is changed in odoo for example when tests are run
  on an other database).

* Always use the same name for the same kind of object. For example, if you
  have a field 'lines' that contains a list of sale order lines, you must
  use the same name for the same kind of object in all the other json documents.

* Manage relations between objects in your json documents the same way.
  By default, you should return the id of the related object in the json document.
  But this is not always possible or convenient, so you can also return the
  related object in the json document. The main advantage of returning the id
  of the related object is that it allows you to avoid the `n+1 problem
  <https://restfulapi.net/rest-api-n-1-problem/>`_ . The
  main advantage of returning the related object in the json document is that
  it allows you to avoid an extra call to retrieve the related object.
  By keeping in mind the pros and cons of each approach, you can choose the
  best one for your use case. Once it's done, you must be consistent in the
  way you manage the relations of the same object.

* It's not always a good idea to name your fields into your json documents
  with the same name as the fields of the corresponding odoo model. For example,
  in your document representing a sale order, you must not use the name 'order_line'
  for the field that contains the list of sale order lines. The name 'order_line'
  in addition to being confusing and not consistent with the best practices, is
  not auto-descriptive. The name 'lines' is much better.

* Keep a defensive programming approach. If you provide a route handler that
  returns a list of records, you must ensure that the computation of the list
  is not too long or will not drain your server resources. For example,
  for search route handlers, you must ensure that the search is limited to
  a reasonable number of records by default.

* As a corollary of the previous point, a search handler must always use the
  pagination mechanism with a reasonable default page size. The result list
  must be enclosed in a json document that contains the total number of records
  and the list of records.

* Use plural for the name of a service. For example, if you provide a service
  that allows you to manage the sale orders, you must use the name 'sale_orders'
  and not 'sale_order'.



* ... and many more.

We could write a book about the best practices to follow when you design your api
but we will stop here. This list is the result of our experience at `ACSONE SA/NV
<https://acsone.eu>`_ and it evolves over time. It's a kind of rescue kit that we
would provide to a new developer that starts to design an api. This kit must
be accompanied with the reading of some useful resources link like the `REST Guidelines
<https://www.belgif.be/specification/rest/api-guide/>`_. On a technical level,
the `fastapi  documentation <https://fastapi.tiangolo.com/>`_ provides a lot of
useful information as well, with a lot of examples. Last but not least, the
`pydantic`_ documentation is also very useful.

Miscellaneous
~~~~~~~~~~~~~

Development of a search route handler
=====================================

The **'odoo-addon-fastapi'** module provides 2 useful piece of code to help
you be consistent when writing a route handler for a search route.

1. A dependency method to use to specify the pagination parameters in the same
   way for all the search route handlers: **'odoo.addons.fastapi.paging'**.
2. A PagedCollection pydantic model to use to return the result of a search route
   handler enclosed in a json document that contains the total number of records.

.. code-block:: python

    from typing import Annotated
    from pydantic import BaseModel

    from odoo.api import Environment
    from odoo.addons.fastapi.dependencies import paging, authenticated_partner_env
    from odoo.addons.fastapi.schemas import PagedCollection, Paging

    class SaleOrder(BaseModel):
        id: int
        name: str
        model_config = ConfigDict(from_attributes=True)


    @router.get(
        "/sale_orders",
        response_model=PagedCollection[SaleOrder],
        response_model_exclude_unset=True,
    )
    def get_sale_orders(
        paging: Annotated[Paging, Depends(paging)],
        env: Annotated[Environment, Depends(authenticated_partner_env)],
    ) -> PagedCollection[SaleOrder]:
        """Get the list of sale orders."""
        count = env["sale.order"].search_count([])
        orders = env["sale.order"].search([], limit=paging.limit, offset=paging.offset)
        return PagedCollection[SaleOrder](
            total=count,
            items=[SaleOrder.model_validate(order) for order in orders],
        )

.. note::

    The **'odoo.addons.fastapi.schemas.Paging'** and **'odoo.addons.fastapi.schemas.PagedCollection'**
    pydantic models are not designed to be extended to not introduce a
    dependency between the **'odoo-addon-fastapi'** module and the **'odoo-addon-extendable'**


Customization of the error handling
===================================

The error handling a very important topic in the design of the fastapi integration
with odoo. It must ensure that the error messages are properly return to the client
and that the transaction is properly roll backed. The **'fastapi'** module provides
a way to register custom error handlers. The **'odoo.addons.fastapi.error_handlers'**
module provides the default error handlers that are registered by default when
a new instance of the **'FastAPI'** class is created. When an app is initialized in
'fastapi.endpoint' model, the method `_get_app_exception_handlers` is called to
get a dictionary of error handlers. This method is designed to be overridden
in a custom module to provide custom error handlers. You can override the handler
for a specific exception class or you can add a new handler for a new exception
or even replace all the handlers by your own handlers. Whatever you do, you must
ensure that the transaction is properly roll backed.

Some could argue that the error handling can't be extended since the error handlers
are global method not defined in an odoo model. Since the method providing the
the error handlers definitions is defined on the 'fastapi.endpoint' model, it's
not a problem at all, you just need to think another way to do it that by inheritance.

A solution could be to develop you own error handler to be able to process the
error and chain the call to the default error handler.

.. code-block:: python

    class MyCustomErrorHandler():
        def __init__(self, next_handler):
            self.next_handler = next_handler

        def __call__(self, request: Request, exc: Exception) -> JSONResponse:
            # do something with the error
            response = self.next_handler(request, exc)
            # do something with the response
            return response


With this solution, you can now register your custom error handler by overriding
the method `_get_app_exception_handlers` in your custom module.

.. code-block:: python

    class FastapiEndpoint(models.Model):
        _inherit = "fastapi.endpoint"

        def _get_app_exception_handlers(
            self,
        ) -> Dict[
            Union[int, Type[Exception]],
            Callable[[Request, Exception], Union[Response, Awaitable[Response]]],
        ]:
            handlers = super()._get_app_exception_handlers()
            access_error_handler = handlers.get(odoo.exceptions.AccessError)
            handlers[odoo.exceptions.AccessError] = MyCustomErrorHandler(access_error_handler)
            return handlers

In the previous example, we extend the error handler for the 'AccessError' exception
for all the endpoints. You can do the same for a specific app by checking the
'app' field of the 'fastapi.endpoint' record before registering your custom error
handler.

FastAPI addons directory structure
==================================

When you develop a new addon to expose an api with fastapi, it's a good practice
to follow the same directory structure and naming convention for the files
related to the api. It will help you to easily find the files related to the api
and it will help the other developers to understand your code.

Here is the directory structure that we recommend. It's based on practices that
are used in the python community when developing a fastapi app.

.. code-block::

  .
  ├── x_api
  │   ├── data
  │   │   ├── ... .xml
  │   ├── demo
  │   │   ├── ... .xml
  │   ├── i18n
  │   │   ├── ... .po
  │   ├── models
  │   │   ├── __init__.py
  │   │   ├── fastapi_endpoint.py  # your app
  │   │   └── ... .py
  │   └── routers
  │   │   ├── __init__.py
  │   │   ├── items.py
  │   │   └── ... .py
  │   ├── schemas | schemas.py
  │   │   ├── __init__.py
  │   │   ├── my_model.py  # pydantic model
  │   │   └── ... .py
  │   ├── security
  │   │   ├── ... .xml
  │   ├── views
  │   │   ├── ... .xml
  │   ├── __init__.py
  │   ├── __manifest__.py
  │   ├── dependencies.py  # custom dependencies
  │   ├── error_handlers.py  # custom error handlers


* The **'models'** directory contains the odoo models. When you define a new
  app, as for the others addons, you will add your new model inheriting from
  the **'fastapi.endpoint'** model in this directory.
* The **'routers'** directory contains the fastapi routers. You will add your
  new routers in this directory. Each route starting with the same prefix should
  be grouped in the same file. For example, all the routes starting with
  '/items' should be defined in the **'items.py'** file. The **'__init__.py'**
  file in this directory is used to import all the routers defined in the
  directory and create a global router that can be used in an app. For example,
  in your **'items.py'** file, you will define a router like this:

  .. code-block:: python

    router = APIRouter(tags=["items"])

    router.get("/items", response_model=List[Item])
    def list_items():
        pass

  In the **'__init__.py'** file, you will import the router and add it to the global
  router or your addon.

  .. code-block:: python

    from fastapi import APIRouter

    from .items import router as items_router

    router = APIRouter()
    router.include_router(items_router)

* The **'schemas.py'** will be used to define the pydantic models. For complex
  APIs with a lot of models, it will be better to create a **'schemas'** directory
  and split the models in different files.  The **'__init__.py'** file in this
  directory will be used to import all the models defined in the directory.
  For example, in your **'my_model.py'**
  file, you will define a model like this:

  .. code-block:: python

    from pydantic import BaseModel

    class MyModel(BaseModel):
        name: str
        description: str = None

  In the **'__init__.py'** file, you will import the model's classes from the
  files in the directory.

  .. code-block:: python

    from .my_model import MyModel

  This will allow to always import the models from the schemas module whatever
  the models are spread across different files or defined in the **'schemas.py'**
  file.

  .. code-block:: python

    from x_api_addon.schemas import MyModel

* The **'dependencies.py'** file contains the custom dependencies that you
  will use in your routers. For example, you can define a dependency to
  check the access rights of the user.
* The **'error_handlers.py'** file contains the custom error handlers that you
  will use in your routers. The **'odoo-addon-fastapi'** module provides the
  default error handlers for the common odoo exceptions. Chance are that you
  will not need to define your own error handlers. But if you need to do it,
  you can define them in this file.

What's next?
~~~~~~~~~~~~

The **'odoo-addon-fastapi'** module is still in its early stage of development.
It will evolve over time to integrate your feedback and to provide the missing
features. It's now up to you to try it and to provide your feedback.

.. _pydantic: https://docs.pydantic.dev/
