To support pydantic models that map to Odoo models, Pydantic model
instances can be created from arbitrary odoo model instances by mapping
fields from odoo models to fields defined by the pydantic model. 


To ease the mapping, the addon provide an utility class (using `pydantic>2.0`) `odoo.addons.pydantic.utils.PydanticOdooBaseModel`:

``` python
from odoo.addons.pydantic.utils import PydanticOdooBaseModel


class Group(PydanticOdooBaseModel):
    name: str

class UserInfo(PydanticOdooBaseModel):
    name: str
    groups: List[Group] = pydantic.Field(alias="groups_id")

user = self.env.user
user_info = UserInfo.from_orm(user)
```

See the official [Pydantic
documentation](https://docs.pydantic.dev/) to discover all the
available functionalities.
