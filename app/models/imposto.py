from pydantic import BaseModel

from .icms import ICMS
from .pis import PIS
from .confins import COFINS


class Imposto(BaseModel):
    ICMS: ICMS
    PIS: PIS
    COFINS: COFINS