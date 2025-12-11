from pydantic import BaseModel
from typing import Optional
from .produto import Prod
from .imposto import Imposto

class Dest(BaseModel):
    nItem: str
    prod: Prod
    imposto: Imposto
    infAdProd: Optional[str] = None
