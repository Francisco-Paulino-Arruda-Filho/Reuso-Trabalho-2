from pydantic import BaseModel
from models.cofinsa_liq import COFINSAliq


class COFINS(BaseModel):
    COFINSAliq: COFINSAliq