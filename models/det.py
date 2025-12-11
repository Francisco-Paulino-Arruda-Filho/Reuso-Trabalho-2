
from pydantic import BaseModel

from models.imposto import Imposto
from models.produto import Prod

class Det(BaseModel):
    nItem: int
    prod: Prod
    imposto: Imposto
