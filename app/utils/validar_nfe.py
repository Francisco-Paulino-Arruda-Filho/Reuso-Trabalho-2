from app.models.nfe import NFe
from math import isclose
from app.utils.validar_cnpj import validar_cnpj
from app.utils.validar_cpf import validar_cpf
from app.utils.validar_cep import validar_cep
from app.utils.ufc_validas import UFS_VALIDAS


def validar_nfe(nfe: NFe) -> None:
    erros = []

    if not nfe.cnpj_emitente and not nfe.cpf_emitente:
        erros.append("Emitente deve possuir CNPJ ou CPF")

    if nfe.cnpj_emitente and nfe.cpf_emitente:
        erros.append("Informe apenas CNPJ ou CPF do emitente, não ambos")

    if nfe.cnpj_emitente:
        if not validar_cnpj(nfe.cnpj_emitente):
            erros.append("CNPJ do emitente inválido")

    if nfe.cpf_emitente:
        if not validar_cpf(nfe.cpf_emitente):
            erros.append("CPF do emitente inválido")

    if nfe.uf_emitente not in UFS_VALIDAS:
        erros.append("UF do emitente inválida")

    if not nfe.cnpj_destinatario and not nfe.cpf_destinatario:
        erros.append("Destinatário deve possuir CNPJ ou CPF")

    if nfe.cnpj_destinatario:
        if not validar_cnpj(nfe.cnpj_destinatario):
            erros.append("CNPJ do destinatário inválido")

    if nfe.cpf_destinatario:
        if not validar_cpf(nfe.cpf_destinatario):
            erros.append("CPF do destinatário inválido")

    if nfe.cnpj_destinatario and nfe.cpf_destinatario:
        erros.append("Informe apenas CNPJ ou CPF do destinatário")

    if nfe.uf_destinatario not in UFS_VALIDAS:
        erros.append("UF do destinatário inválida")

    if not validar_cep(nfe.cep_emitente):
        erros.append("CEP do emitente inválido")

    if nfe.data_entrada_saida < nfe.data_emissao:
        erros.append("Data de entrada/saída não pode ser anterior à emissão")

    if not nfe.items or len(nfe.items) == 0:
        erros.append("NF-e deve possuir ao menos um item")

    soma_itens = 0.0

    for item in nfe.items:
        if item.quantidade_comercial <= 0:
            erros.append(f"Item {item.numero_item}: quantidade inválida")

        if item.valor_unitario_comercial <= 0:
            erros.append(f"Item {item.numero_item}: valor unitário inválido")

        if len(str(item.cfop)) != 4:
            erros.append(f"Item {item.numero_item}: CFOP inválido")

        if len(str(item.codigo_ncm)) != 8:
            erros.append(f"Item {item.numero_item}: NCM inválido")

        valor_calculado = item.quantidade_comercial * item.valor_unitario_comercial

        if not isclose(valor_calculado, item.valor_bruto, rel_tol=1e-2):
            erros.append(
                f"Item {item.numero_item}: valor bruto inconsistente "
                f"(esperado {valor_calculado:.2f}, informado {item.valor_bruto:.2f})"
            )

        soma_itens += item.valor_bruto

    if not isclose(soma_itens, nfe.valor_produtos, rel_tol=1e-2):
        erros.append(
            f"Valor dos produtos inválido "
            f"(esperado {soma_itens:.2f}, informado {nfe.valor_produtos:.2f})"
        )

    valor_total_calculado = (
        nfe.valor_produtos +
        nfe.valor_frete +
        nfe.valor_seguro
    )

    if not isclose(valor_total_calculado, nfe.valor_total, rel_tol=1e-2):
        erros.append(
            f"Valor total inválido "
            f"(esperado {valor_total_calculado:.2f}, informado {nfe.valor_total:.2f})"
        )

    if erros:
        raise ValueError(" | ".join(erros))
