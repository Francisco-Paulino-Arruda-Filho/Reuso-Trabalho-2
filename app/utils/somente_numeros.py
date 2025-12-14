import re


def somente_numeros(valor: str) -> str:
    return re.sub(r"\D", "", valor)