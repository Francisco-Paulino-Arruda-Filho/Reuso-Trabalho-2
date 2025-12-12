from pydantic import BaseModel


class Reference(BaseModel):
    URI: str
    DigestValue: str
