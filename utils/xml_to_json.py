import xmltodict

def xml_to_dict(xml_str: str):
    return xmltodict.parse(xml_str)