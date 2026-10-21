Declare params on `http_api` routes:

    from odoo import http
    from odoo.addons.http_api_cerberus.params import CerberusParam

    class PartnerAPI(http.Controller):

        def _get_search_schema(self):
            return {
                "name": {"type": "string", "required": True},
                "limit": {"type": "integer", "coerce": int, "default": 10},
            }

        @http.route(
            "/api/partner/search",
            type="http_api",
            auth="user",
            methods=["GET"],
            input=CerberusParam("_get_search_schema"),
            output=CerberusParam(
                {"id": {"type": "integer"}, "name": {"type": "string"}},
                as_list=True,
            ),
        )
        def search(self, name, limit):
            partners = http.request.env["res.partner"].search(
                [("name", "ilike", name)], limit=limit
            )
            return [{"id": p.id, "name": p.name} for p in partners]

The schema can be:

- a dict
- a callable `(ctx, direction) -> dict` (`direction` is `input` or `output`)
- the name of a method returning the schema. The method is looked up on
  `ctx.owner` if any (eg: a service), otherwise on the controller of the route
- a `cerberus.Validator` instance (not thread safe, prefer the other options)

Options:

| Option | Default | Meaning |
|---|---|---|
| `purge_unknown` | `True` | drop keys not declared in the schema |
| `validator_cls` | `cerberus.Validator` | subclass providing custom rules or coercers |
| `as_list` | `False` | data is a list of items matching the schema |
| `min_items`, `max_items` | `None` | bounds for lists |
| `unique_items` | `None` | documentation only |
| `cache` | `False` | cache the resolved schema per database and direction. Use it only when the schema does not depend on the request |
| `strict_output` | `True` | if `False`, invalid results are logged and returned anyway |

Invalid input raises `ApiValidationError`:
the details of the errors are returned in the `errors` key of the response.
