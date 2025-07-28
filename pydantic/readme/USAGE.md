To support pydantic models that map to Odoo models, Pydantic model
instances can be created from arbitrary odoo model instances by mapping
fields from odoo models to fields defined by the pydantic model. 


To ease the mapping, the addon provide 2 utility classes:

* Using `pydantic>2.0`, `odoo.addons.pydantic.utils.PydanticOdooBaseModel`:

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

* Using `pydantic<2.0`, `odoo.addons.pydantic.utils.GenericOdooGetter`:

``` python
import pydantic
from odoo.addons.pydantic import utils

class Group(pydantic.BaseModel):
    name: str

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter

class UserInfo(pydantic.BaseModel):
    name: str
    groups: List[Group] = pydantic.Field(alias="groups_id")

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter

user = self.env.user
user_info = UserInfo.from_orm(user)
```

See the official [Pydantic
documentation](https://docs.pydantic.dev/) to discover all the
available functionalities.
