
from pydantic import BaseModel

from models.imposto import Imposto
from models.produto import Prod


class Det(BaseModel):
    nItem: str
    prod: Prod
    imposto: Imposto