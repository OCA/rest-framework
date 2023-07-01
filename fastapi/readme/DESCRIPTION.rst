This addon provides the basis to smoothly integrate the `FastAPI`_
framework into Odoo.

This integration allows you to use all the goodies from `FastAPI`_ to build custom
APIs for your Odoo server based on standard Python type hints.

**What is building an API?**

An API is a set of functions that can be called from the outside world. The
goal of an API is to provide a way to interact with your application from the
outside world without having to know how it works internally. A common mistake
when you are building an API is to expose all the internal functions of your
application and therefore create a tight coupling between the outside world and
your internal datamodel and business logic. This is not a good idea because it
makes it very hard to change your internal datamodel and business logic without
breaking the outside world.

When you are building an API, you define a contract between the outside world
and your application. This contract is defined by the functions that you expose
and the parameters that you accept. This contract is the API. When you change
your internal datamodel and business logic, you can still keep the same API
contract and therefore you don't break the outside world. Even if you change
your implementation, as long as you keep the same API contract, the outside
world will still work. This is the beauty of an API and this is why it is so
important to design a good API.

A good API is designed to be stable and to be easy to use. It's designed to
provide high-level functions related to a specific use case. It's designed to
be easy to use by hiding the complexity of the internal datamodel and business
logic. A common mistake when you are building an API is to expose all the internal
functions of your application and let the oustide world deal with the complexity
of your internal datamodel and business logic. Don't forget that on a transactional
point of view, each call to an API function is a transaction. This means that
if a specific use case requires multiple calls to your API, you should provide
a single function that does all the work in a single transaction. This why APIs
methods are called high-level and atomic functions.

.. _FastAPI:  https://fastapi.tiangolo.com/
