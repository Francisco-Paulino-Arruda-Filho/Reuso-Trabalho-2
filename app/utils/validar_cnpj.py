from app.utils.somente_numeros import somente_numeros


def validar_cnpj(cnpj: str) -> bool:
    cnpj = somente_numeros(cnpj)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_2 = [6] + pesos_1

    soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    d1 = 11 - (soma % 11)
    d1 = 0 if d1 >= 10 else d1

    if d1 != int(cnpj[12]):
        return False

    soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
    d2 = 11 - (soma % 11)
    d2 = 0 if d2 >= 10 else d2

    return d2 == int(cnpj[13])
