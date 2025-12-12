from pydantic import BaseModel


class KeyInfo(BaseModel):
    X509Data: dict