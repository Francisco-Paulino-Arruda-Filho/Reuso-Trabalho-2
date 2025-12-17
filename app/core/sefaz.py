import logging
from lxml import etree

from app.services.sefaz.sefaz_soap_client import SEFAZSoapClient
from app.services.xml_signer.xml_signer import XMLSigner

logger = logging.getLogger(__name__)

class SefazAPI:
    def __init__(self, signer: XMLSigner, wsdl_provider):
        self.signer = signer
        self.wsdl_provider = wsdl_provider

    def _parse_response(self, response: str) -> dict:
       # Ensure response is a string and strip whitespace that might cause parsing errors
        if not isinstance(response, str):
            response = str(response)

        response = response.strip()

        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        cstat = root.find('.//nfe:cStat', ns)
        xmotivo = root.find('.//nfe:xMotivo', ns)

        if cstat is not None and cstat.text == '100':
            return {
                'status': 'AUTORIZADA',
                'protocolo': root.find('.//nfe:nProt', ns).text,
                'chave_nfe': root.find('.//nfe:chNFe', ns).text,
                'autorizado_em': root.find('.//nfe:dhRecbto', ns).text if root.find('.//nfe:dhRecbto', ns) is not None else None,
            }

        return {
            'status': 'REJEITADA',
            'codigo': cstat.text if cstat else None,
            'mensagem': xmotivo.text if xmotivo else None,
        }

    def send_nfe(self, xml: str, uf: str) -> dict:
        wsdl = self.wsdl_provider.get(uf)
        if not wsdl:
            raise ValueError("UF não suportada")

        xml_signed = self.signer.sign(xml)

        client = SEFAZSoapClient(wsdl)
        response = client.autorizar(xml_signed)

        return self._parse_response(response)
