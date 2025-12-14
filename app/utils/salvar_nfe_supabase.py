from datetime import datetime, timezone
from uuid import uuid4
from fastapi.encoders import jsonable_encoder

from app.infra.supabase_client import supabase
from app.models.nfe import NFe 


def salvar_nfe_supabase(nfe: NFe, xml_str: str):
    agora = datetime.now(timezone.utc)

    payload = {
        "id": str(uuid4()),
        "ref": agora.strftime("%y%m%d%H%M"),
        "status": "CRIADA",

        "chave_nfe": None,
        "numero": None,
        "serie": None,

        "xml_url": None,
        "danfe_url": None,

        "payload_envio": jsonable_encoder(nfe),

        "payload_retorno": None,

        "ambiente": "producao",

        "data_emissao": (
            nfe.data_emissao.isoformat()
            if nfe.data_emissao
            else None
        ),

        "autorizado_em": None,

        "criado_em": agora.isoformat(),
        "atualizado_em": agora.isoformat(),
    }

    response = supabase.table("nfe").insert(payload).execute()

    if not response.data:
        raise Exception("Erro ao inserir NF-e no Supabase")

    return response.data[0]
