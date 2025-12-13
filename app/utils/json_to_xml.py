from xml.etree.ElementTree import Element, SubElement, tostring
from models.nfe import NFe

def dict_to_xml(tag, data):
    elem = Element(tag)
    for key, value in data.items():
        if isinstance(value, dict):
            elem.append(dict_to_xml(key, value))
        elif isinstance(value, list):
            for item in value:
                elem.append(dict_to_xml(key, item))
        else:
            child = SubElement(elem, key)
            child.text = str(value)
    return elem

def nfe_json_to_xml(nfe: NFe) -> str:
    root = Element("NFe")
    infNFe = SubElement(root, "infNFe", {"versao": "1.10"})

    xml_body = dict_to_xml("nfeData", nfe.model_dump())
    for child in xml_body:
        infNFe.append(child)

    return tostring(root, encoding="unicode")
