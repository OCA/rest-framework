from extendable_pydantic import ExtendableModelMeta

from pydantic import BaseModel


class ListMetadata(BaseModel, metaclass=ExtendableModelMeta):
    size: int = None
