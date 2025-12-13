from pydantic import BaseModel
from .signed_info import SignedInfo
from .key_info import KeyInfo

class Signature(BaseModel):
    SignedInfo: SignedInfo
    SignatureValue: str
    KeyInfo: KeyInfo