from pydantic import BaseModel
from models.icms import ICMS
from models.pis import PIS
from models.confins import COFINS


class Imposto(BaseModel):
    ICMS: ICMS
    PIS: PIS
    COFINS: COFINS