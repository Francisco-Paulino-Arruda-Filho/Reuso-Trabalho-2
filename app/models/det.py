from pydantic import BaseModel

from .imposto import Imposto
from .produto import Prod

class Det(BaseModel):
    nItem: int
    prod: Prod
    imposto: Imposto
