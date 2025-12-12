from pydantic import BaseModel

from .cofinsa_liq import COFINSAliq


class COFINS(BaseModel):
    COFINSAliq: COFINSAliq