import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives.serialization import pkcs12
from signxml import XMLSigner as Signer
from app.core.xml_signer import XMLSigner

class XMLSignerReal(XMLSigner):
    def __init__(self, pfx_path: str, password: str):
        self.pfx_path = pfx_path
        self.password = password

    def sign(self, xml: str) -> str:
        with open(self.pfx_path, "rb") as f:
            pfx = f.read()

        key, cert, _ = pkcs12.load_key_and_certificates(
            pfx, self.password.encode()
        )

        root = ET.fromstring(xml)

        signed = Signer(
            method="rsa-sha1",
            digest_algorithm="sha1"
        ).sign(root, key=key, cert=cert)

        return ET.tostring(signed, encoding="unicode")
