from pydantic import BaseModel

from .reference import Reference

class SignedInfo(BaseModel):
    CanonicalizationMethod: dict
    SignatureMethod: dict
    Reference: Reference