from pydantic import BaseModel
from models.reference import Reference

class SignedInfo(BaseModel):
    CanonicalizationMethod: dict
    SignatureMethod: dict
    Reference: Reference