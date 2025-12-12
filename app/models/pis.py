from pydantic import BaseModel
from models.pisa_liq import PISAliq 

class PIS(BaseModel):
    PISAliq: PISAliq