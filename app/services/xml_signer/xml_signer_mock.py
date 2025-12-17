from app.services.xml_signer.xml_signer import XMLSigner


class XMLSignerMock(XMLSigner):
    def sign(self, xml: str) -> str:
        return xml
