from typing import Any, Dict
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.dom import minidom

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .models.nfe_payload import NFePayload
from .core.rate_limit import check_rate_limit

MOCK_JSON_PATH = "./nfes/nfe1.json"

with open(MOCK_JSON_PATH, "r", encoding="utf-8") as f:
    MOCK_JSON = f.read()

NS = "http://www.portalfiscal.inf.br/nfe"
ET.register_namespace('', NS)


def prettify(elem: ET.Element) -> bytes:
    rough = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(encoding="utf-8", standalone="no")


def dict_to_xml(parent: ET.Element, data: Any):
    if data is None:
        return
    if isinstance(data, dict):
        for key, val in data.items():
            if val is None:
                child = ET.SubElement(parent, key)
                child.text = ""
            elif isinstance(val, (dict)):
                child = ET.SubElement(parent, key)
                dict_to_xml(child, val)
            elif isinstance(val, list):
                for item in val:
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, item)
            else:
                child = ET.SubElement(parent, key)
                if isinstance(val, Decimal):
                    child.text = format(val, 'f')
                else:
                    child.text = str(val)
    elif isinstance(data, list):
        for item in data:
            dict_to_xml(parent, item)
    else:
        parent.text = str(data)


def build_nfe_xml(payload: Dict) -> bytes:
    inf = payload["infNFe"]
    root = ET.Element(f"{{{NS}}}NFe")
    inf_elem = ET.SubElement(root, "infNFe")
    if "Id" in inf:
        inf_elem.set("Id", inf["Id"])
    if "versao" in inf:
        inf_elem.set("versao", str(inf["versao"]))

    for key in inf:
        if key in ("Id", "versao"):
            continue
        value = inf[key]
        child = ET.SubElement(inf_elem, key)
        dict_to_xml(child, value)

    return prettify(root)


app = FastAPI(title="Mock NFe API - validate JSON and return XML")


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    cnpj = request.headers.get("X-CNPJ")

    if not cnpj:
        return JSONResponse(
            status_code=400,
            content={"error": "X-CNPJ header obrigatório"}
        )

    await check_rate_limit(cnpj)

    return await call_next(request)


@app.get("/nfe/mock")
def get_mock():
    return MOCK_JSON


@app.post("/nfe", response_class=Response)
def post_nfe(payload: NFePayload):
    try:
        payload_dict = payload.dict(by_alias=True, exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    xml_bytes = build_nfe_xml(payload_dict)
    return Response(content=xml_bytes, media_type="application/xml")
