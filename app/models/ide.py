from pydantic import BaseModel


class Ide(BaseModel):
    cUF: str
    cNF: str
    natOp: str
    indPag: str
    mod: str
    serie: str
    nNF: str
    dEmi: str
    dSaiEnt: str
    tpNF: str
    cMunFG: str
    tpImp: str
    tpEmis: str
    cDV: str
    tpAmb: str
    finNFe: str
    procEmi: str
    verProc: str