import xml.etree.ElementTree as ET

def assinar_xml(xml_string: str) -> str:
    """
    Assina digitalmente o XML da NF-e
    Em produção, usar certificado A1 ou A3 com biblioteca como python-pkcs11 ou cryptography
    """

    root = ET.fromstring(xml_string)

    # Adiciona elemento Signature simulado
    signature = ET.Element(
        'Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
    signed_info = ET.SubElement(signature, 'SignedInfo')
    ET.SubElement(signed_info, 'CanonicalizationMethod',
                  Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
    ET.SubElement(signed_info, 'SignatureMethod',
                  Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')

    # Em produção: adicionar valores reais de assinatura
    ET.SubElement(
        signature, 'SignatureValue').text = 'ASSINATURA_SIMULADA_BASE64'

    nfe_elem = root.find('.//{http://www.portalfiscal.inf.br/nfe}NFe')
    if nfe_elem is not None:
        nfe_elem.append(signature)

    return ET.tostring(root, encoding='unicode')
