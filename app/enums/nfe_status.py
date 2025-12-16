from enum import Enum


class StatusNFe(str, Enum):
    CRIADA = "CRIADA"
    PROCESSANDO = "PROCESSANDO"
    AUTORIZADA = "AUTORIZADA"
    REJEITADA = "REJEITADA"
    ERRO = "ERRO"
