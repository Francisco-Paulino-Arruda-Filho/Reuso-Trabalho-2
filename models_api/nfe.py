from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from models_api.nfe_item import NFeItem

class NFe(BaseModel):
    natureza_operacao: str

    data_emissao: date
    data_entrada_saida: date

    tipo_documento: int
    finalidade_emissao: int

    cnpj_emitente: Optional[str] = None
    cpf_emitente: Optional[str] = None

    nome_emitente: str
    nome_fantasia_emitente: Optional[str] = None

    logradouro_emitente: str
    numero_emitente: int
    bairro_emitente: str
    municipio_emitente: str
    uf_emitente: str
    cep_emitente: str

    inscricao_estadual_emitente: Optional[str] = None

    nome_destinatario: str
    cpf_destinatario: Optional[str] = None
    cnpj_destinatario: Optional[str] = None

    inscricao_estadual_destinatario: Optional[str] = None
    telefone_destinatario: Optional[int] = None

    logradouro_destinatario: str
    numero_destinatario: int
    bairro_destinatario: str
    municipio_destinatario: str
    uf_destinatario: str
    pais_destinatario: str
    cep_destinatario: int

    valor_frete: float
    valor_seguro: float
    valor_total: float
    valor_produtos: float

    modalidade_frete: int

    items: List[NFeItem]
