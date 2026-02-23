## Getting an odoo environment

If you need to get an odoo env based on the provided api key, you can
use authenticated_env_by_auth_api_key.

``` python
@router.get("/example_with_authenticated_env")
def example_with_authenticated_env(
    env: Annotated[Environment, Depends(authenticated_env_by_auth_api_key)],
) -> None:
    # env.user is the user attached to the provided key
    pass
```

## Getting the authenticated partner

If want to get the partned related to the the provided api key, you can
use authenticated_partner_by_api_key

``` python
@router.get("/example_with_authenticated_partner")
def example_with_authenticated_partner(
    partner: Annotated[Partner, Depends(authenticated_partner_by_api_key)],
) -> None:
    # partner is the partner related to the provided key key.user_id.partner_id
    pass
```

## Configuration

For this to work, the api key must be defined on the Endpoint. A new
field auth_api_key_group_id has been added to the Endpoint model.
