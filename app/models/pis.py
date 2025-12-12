from pydantic import BaseModel

from .pisa_liq import PISAliq 

class PIS(BaseModel):
    PISAliq: PISAliq