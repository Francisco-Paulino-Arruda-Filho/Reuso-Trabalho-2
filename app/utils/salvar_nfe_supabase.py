from datetime import datetime, timezone
from uuid import uuid4
from fastapi.encoders import jsonable_encoder

from app.models.nfe import NFe 
from app.services.nfe.nfe import NFeService


async def salvar_nfe_supabase(nfe: NFe, xml_str: str):
    """Wrapper that uses NFeService to create the record in Supabase."""
    svc = NFeService()
    return await svc.create_from_model(nfe, xml_str)
