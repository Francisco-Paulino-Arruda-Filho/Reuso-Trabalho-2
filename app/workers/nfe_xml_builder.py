from app.models.nfe import NFe
from app.utils.build_nfe_xml import build_nfe_xml


class NFeXMLBuilder:
    """Constrói o XML da NF-e"""

    def build(self, record: dict) -> str:
        payload_envio = record.get("payload_envio") or {}
        nfe = NFe(**payload_envio)
        return build_nfe_xml(nfe)
