from zeep import Client
from requests import Session
from lxml import etree
from zeep.transports import Transport
import logging
from zeep.plugins import HistoryPlugin
from zeep import Client, Settings
from lxml import etree

logger = logging.getLogger(__name__)


class SEFAZSoapClient:
    def __init__(self, wsdl_url: str, verify_ssl=True):
        # Plugin para capturar histórico de requisições/respostas
        self.history = HistoryPlugin()

        # Configurar session HTTP
        session = Session()
        session.verify = verify_ssl
        transport = Transport(session=session)

        # Criar client zeep com configurações robustas
        settings = Settings(
            strict=False,  # Mais tolerante com WSDLs
            xml_huge_tree=True,  # Permite XMLs grandes
            xsd_ignore_sequence_order=True  # Mais flexível
        )

        self.client = Client(
            wsdl=wsdl_url,
            transport=transport,
            settings=settings,
            plugins=[self.history]
        )

    def autorizar(self, xml: str) -> str:
        """
        Envia XML para autorização e retorna a resposta XML raw

        Esta abordagem usa o HistoryPlugin do zeep para capturar
        a resposta HTTP real, similar ao que sistemas de boleto fazem.
        """
        try:
            # Faz a chamada SOAP
            logger.debug("Enviando requisição SOAP...")

            # Tenta chamar o serviço
            try:
                result = self.client.service.nfeAutorizacaoLote(xml)
                logger.debug(
                    f"Resultado zeep (type={type(result)}): {str(result)[:200]}")
            except TypeError as e:
                logger.warning(
                    f"Chamada direta falhou: {e}, tentando com dict...")
                result = self.client.service.nfeAutorizacaoLote(
                    {'nfeDadosMsg': xml})

            # CRÍTICO: Em vez de usar o resultado deserializado do zeep,
            # pegamos a resposta HTTP raw do histórico
            if self.history.last_received:
                response_content = self.history.last_received['envelope']
                logger.debug(
                    f"Response envelope (primeiros 300 chars): {etree.tostring(response_content, encoding='unicode')[:300]}")

                # Extrair o corpo da resposta SOAP
                xml_response = self._extract_nfe_result(response_content)

                if not xml_response or not xml_response.strip():
                    logger.error("Resposta extraída está vazia!")
                    logger.error(
                        f"Envelope completo: {etree.tostring(response_content, encoding='unicode')}")
                    raise ValueError("Resposta SEFAZ está vazia após extração")

                return xml_response
            else:
                logger.error("Não há histórico de resposta disponível")
                raise ValueError("Não foi possível capturar resposta SOAP")

        except Exception as e:
            logger.exception(f"Erro ao enviar para SEFAZ: {e}")
            raise

    def _extract_nfe_result(self, soap_envelope) -> str:
        """
        Extrai o resultado da NFe do envelope SOAP

        O envelope SOAP tem esta estrutura:
        <soap:Envelope>
          <soap:Body>
            <nfeAutorizacaoLoteResult>
              <retEnviNFe>...</retEnviNFe>
            </nfeAutorizacaoLoteResult>
          </soap:Body>
        </soap:Envelope>

        Precisamos retornar apenas o <retEnviNFe>...</retEnviNFe>
        """
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'soap-env': 'http://schemas.xmlsoap.org/soap/envelope/',
            'nfe': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4'
        }

        try:
            # Procurar pelo resultado dentro do Body
            # Tenta diferentes variações de namespace
            result = (
                soap_envelope.find('.//nfe:nfeAutorizacaoLoteResult', namespaces) or
                soap_envelope.find('.//{http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4}nfeAutorizacaoLoteResult') or
                soap_envelope.find('.//nfeAutorizacaoLoteResult')
            )

            if result is not None and len(result) > 0:
                # Pega o primeiro filho (retEnviNFe)
                nfe_result = result[0]
                xml_str = etree.tostring(nfe_result, encoding='unicode')
                logger.debug(
                    f"NFe result extraído (primeiros 200 chars): {xml_str[:200]}")
                return xml_str

            # Se não encontrou, tenta procurar diretamente pelo retEnviNFe
            ret_envi = soap_envelope.find(
                './/{http://www.portalfiscal.inf.br/nfe}retEnviNFe')
            if ret_envi is not None:
                xml_str = etree.tostring(ret_envi, encoding='unicode')
                logger.debug(
                    f"retEnviNFe encontrado diretamente (primeiros 200 chars): {xml_str[:200]}")
                return xml_str

            # Última tentativa: retornar o Body inteiro
            body = soap_envelope.find(
                './/soap:Body', namespaces) or soap_envelope.find('.//soap-env:Body', namespaces)
            if body is not None and len(body) > 0:
                logger.warning(
                    "Usando primeiro elemento do Body como fallback")
                return etree.tostring(body[0], encoding='unicode')

            logger.error(
                "Não foi possível extrair resultado NFe do envelope SOAP")
            logger.error(
                f"Envelope: {etree.tostring(soap_envelope, encoding='unicode')}")
            raise ValueError("Estrutura SOAP inesperada")

        except Exception as e:
            logger.exception(f"Erro ao extrair resultado NFe: {e}")
            raise
