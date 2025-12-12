from pydantic import BaseModel

from models.inf_nfe import InfNFe



class NFePayload(BaseModel):
    infNFe: InfNFe