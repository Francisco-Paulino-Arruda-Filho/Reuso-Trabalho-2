from pydantic import BaseModel
from models.icms_tot import ICMSTot


class Total(BaseModel):
    ICMSTot: ICMSTot