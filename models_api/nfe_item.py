from pydantic import BaseModel

class NFeItem(BaseModel):
    numero_item: int
    codigo_produto: int
    descricao: str
    cfop: int

    unidade_comercial: str
    quantidade_comercial: float
    valor_unitario_comercial: float

    valor_unitario_tributavel: float
    unidade_tributavel: str
    quantidade_tributavel: float

    codigo_ncm: int
    valor_bruto: float

    icms_situacao_tributaria: int
    icms_origem: int

    pis_situacao_tributaria: str
    cofins_situacao_tributaria: str
