from pydantic import BaseModel
from models.icms00 import ICMS00


class ICMS(BaseModel):
    ICMS00: ICMS00