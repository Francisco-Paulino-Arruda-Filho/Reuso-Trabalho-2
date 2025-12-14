from app.utils.somente_numeros import somente_numeros


def validar_cep(cep: str | int) -> bool:
    cep = somente_numeros(str(cep))

    if len(cep) != 8:
        return False

    if cep == cep[0] * 8:
        return False

    return True
