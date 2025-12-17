import logging
from lxml import etree
from lxml import etree

from app.services.sefaz.sefaz_soap_client import SEFAZSoapClient

logger = logging.getLogger(__name__)


class XMLSigner:
    def sign(self, xml: str) -> str:
        raise NotImplementedError


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


# class SefazNFeClient():
#     _pfx_path: str
#     _pfx_password: str

#     def __init__(self, pfx_path: str, pfx_password: str):
#         self._pfx_path = pfx_path
#         self._pfx_password = pfx_password

#     def sign_xml(self, xml_str: str) -> str:
#         return xml_str

#     def send_nfe(self, xml_asigned: str, uf: str) -> dict:
#         wsdl_url = self.get_wsdl_url(uf)
#         if not wsdl_url:
#             raise ValueError(f"UF inválida ou não suportada: {uf}")

#         session = Session()
#         session.verify = True  # Verifica certificados SSL
#         transport = Transport(session=session)
#         client = Client(wsdl=wsdl_url, transport=transport)

#         nfe_dados = {
#             'xml': xml_asigned
#         }

#         try:
#             response = client.service.NFeAutorizacaoLote(nfe_dados)
#             root = etree.fromstring(response.encode())

#             ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}

#             codigo_status = root.find('.//ns:cStat', namespaces=ns)
#             mensagem = root.find('.//ns:xMotivo', namespaces=ns)
#             codigo = codigo_status.text if codigo_status is not None else None

#             if codigo == "100":  # Autorizada
#                 protocolo = root.find('.//ns:nProt', namespaces=ns)
#                 chave = root.find('.//ns:chNFe', namespaces=ns)
#                 data_autorizacao = root.find('.//ns:dhRecbto', namespaces=ns)
#                 return {
#                     'status': 'AUTORIZADA',
#                     'codigo': codigo_status.text,
#                     'mensagem': mensagem.text,
#                     'protocolo': protocolo.text,
#                     'chave_nfe': chave.text,
#                     'autorizado_em': data_autorizacao.text
#                 }
#             else:
#                 return {
#                     'status': 'REJEITADA',
#                     'codigo': codigo_status.text,
#                     'mensagem': f'{codigo_status.text} - {mensagem.text}'
#                 }

#         except Exception as e:
#             logger.exception("Erro ao comunicar com SEFAZ: %s", e)
#             raise

#     def get_wsdl_url(self, uf: str) -> str:
#         WSDL_URLS = {
#             "SP": "https://nfe.fazenda.sp.gov.br/ws/NFeAutorizacao4.asmx?wsdl",
#             "RJ": "https://nfe.fazenda.rj.gov.br/ws/NFeAutorizacao4.asmx?wsdl",
#             # Adicionar outras UFs conforme necessário
#         }

#         return WSDL_URLS.get(uf, "")
