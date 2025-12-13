from pydantic import BaseModel

from .icms_tot import ICMSTot


class Total(BaseModel):
    ICMSTot: ICMSTot