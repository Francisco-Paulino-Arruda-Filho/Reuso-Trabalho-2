from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import date
from typing import Union
from app.models.nfe import NFe


def build_nfe_xml(nfe: NFe) -> str:
    def add(parent, tag, value):
        el = SubElement(parent, tag)
        el.text = str(value)
        return el

    def format_date(d: Union[date, str]):
        if isinstance(d, date):
            return d.isoformat()
        return d

    nfe_el = Element("NFe", xmlns="http://www.portalfiscal.inf.br/nfe")
    inf_nfe = SubElement(nfe_el, "infNFe", versao="4.00", Id="NFe00000000000000000000000000000000000000000000")

    ide = SubElement(inf_nfe, "ide")
    add(ide, "natOp", nfe.natureza_operacao)
    add(ide, "mod", 55)
    add(ide, "tpNF", nfe.tipo_documento)
    add(ide, "finNFe", nfe.finalidade_emissao)
    add(ide, "dhEmi", format_date(nfe.data_emissao))
    add(ide, "dhSaiEnt", format_date(nfe.data_entrada_saida))

    emit = SubElement(inf_nfe, "emit")

    if nfe.cnpj_emitente:
        add(emit, "CNPJ", nfe.cnpj_emitente)
    else:
        add(emit, "CPF", nfe.cpf_emitente)

    add(emit, "xNome", nfe.nome_emitente)

    if nfe.nome_fantasia_emitente:
        add(emit, "xFant", nfe.nome_fantasia_emitente)

    ender_emit = SubElement(emit, "enderEmit")
    add(ender_emit, "xLgr", nfe.logradouro_emitente)
    add(ender_emit, "nro", nfe.numero_emitente)
    add(ender_emit, "xBairro", nfe.bairro_emitente)
    add(ender_emit, "xMun", nfe.municipio_emitente)
    add(ender_emit, "UF", nfe.uf_emitente)
    add(ender_emit, "CEP", nfe.cep_emitente)

    if nfe.inscricao_estadual_emitente:
        add(emit, "IE", nfe.inscricao_estadual_emitente)

    dest = SubElement(inf_nfe, "dest")

    if nfe.cnpj_destinatario:
        add(dest, "CNPJ", nfe.cnpj_destinatario)
    else:
        add(dest, "CPF", nfe.cpf_destinatario)

    add(dest, "xNome", nfe.nome_destinatario)

    if nfe.inscricao_estadual_destinatario:
        add(dest, "IE", nfe.inscricao_estadual_destinatario)

    ender_dest = SubElement(dest, "enderDest")
    add(ender_dest, "xLgr", nfe.logradouro_destinatario)
    add(ender_dest, "nro", nfe.numero_destinatario)
    add(ender_dest, "xBairro", nfe.bairro_destinatario)
    add(ender_dest, "xMun", nfe.municipio_destinatario)
    add(ender_dest, "UF", nfe.uf_destinatario)
    add(ender_dest, "xPais", nfe.pais_destinatario)
    add(ender_dest, "CEP", nfe.cep_destinatario)

    if nfe.telefone_destinatario:
        add(ender_dest, "fone", nfe.telefone_destinatario)

    for item in nfe.items:
        det = SubElement(inf_nfe, "det", nItem=str(item.numero_item))

        prod = SubElement(det, "prod")
        add(prod, "cProd", item.codigo_produto)
        add(prod, "xProd", item.descricao)
        add(prod, "NCM", item.codigo_ncm)
        add(prod, "CFOP", item.cfop)

        add(prod, "uCom", item.unidade_comercial)
        add(prod, "qCom", f"{item.quantidade_comercial:.4f}")
        add(prod, "vUnCom", f"{item.valor_unitario_comercial:.4f}")
        add(prod, "vProd", f"{item.valor_bruto:.2f}")

        add(prod, "uTrib", item.unidade_tributavel)
        add(prod, "qTrib", f"{item.quantidade_tributavel:.4f}")
        add(prod, "vUnTrib", f"{item.valor_unitario_tributavel:.4f}")

        imposto = SubElement(det, "imposto")

        icms = SubElement(imposto, "ICMS")
        icms00 = SubElement(icms, "ICMS00")
        add(icms00, "orig", item.icms_origem)
        add(icms00, "CST", item.icms_situacao_tributaria)

        pis = SubElement(imposto, "PIS")
        pis_nt = SubElement(pis, "PISNT")
        add(pis_nt, "CST", item.pis_situacao_tributaria)

        cofins = SubElement(imposto, "COFINS")
        cofins_nt = SubElement(cofins, "COFINSNT")
        add(cofins_nt, "CST", item.cofins_situacao_tributaria)
    total = SubElement(inf_nfe, "total")
    icms_tot = SubElement(total, "ICMSTot")

    add(icms_tot, "vProd", f"{nfe.valor_produtos:.2f}")
    add(icms_tot, "vFrete", f"{nfe.valor_frete:.2f}")
    add(icms_tot, "vSeg", f"{nfe.valor_seguro:.2f}")
    add(icms_tot, "vNF", f"{nfe.valor_total:.2f}")

    transp = SubElement(inf_nfe, "transp")
    add(transp, "modFrete", nfe.modalidade_frete)

    rough_xml = tostring(nfe_el, encoding="utf-8")
    reparsed = minidom.parseString(rough_xml)

    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")