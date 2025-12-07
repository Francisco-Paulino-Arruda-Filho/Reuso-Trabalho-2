from fastapi import APIRouter, HTTPException
from typing import List
from model.department import Department
from services.department_service import read_csv_department, write_csv_department, ARQUIVO_DEPARTMENT
from logger import logger
from fastapi.responses import Response
from io import BytesIO, StringIO
import zipfile
import csv
from hashlib import sha256
import xml.etree.ElementTree as ET

router = APIRouter(prefix="/departments", tags=["Departamentos"])

@router.get("/zip")
def get_departments_zip():
    departments = read_csv_department()
    if not departments:
        raise HTTPException(status_code=404, detail="Nenhum departamento encontrado")

    csv_string_io = StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=departments[0].dict().keys())
    writer.writeheader()
    for dept in departments:
        writer.writerow(dept.dict())

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("departments.csv", csv_string_io.getvalue())

    zip_buffer.seek(0)

    logger.info("department.csv convertido para .zip")

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=departments.zip"}
    )

@router.get("/quantity")
def count_departments():
    count = len(read_csv_department())

    logger.info("Retornando quantidade de departamentos")

    return {"quantidade": count}

@router.get("/SHA256")
def calculate_hash_256():
    with open(ARQUIVO_DEPARTMENT, "rb") as file:
        data = file.read()
        encrypted_data = sha256(data).hexdigest()

        logger.info("Calculando o hash de departamentos")

        return { "hash_sha_256": encrypted_data}

@router.get("/xml")
def convert_csv_to_xml():
    root = ET.Element("departments")

    for row in read_csv_department():
        department = ET.SubElement(root, "department")

        for key, dp in row.dict().items():
            field = ET.SubElement(department, key)
            field.text = str(dp)

    xml_bytes_io = BytesIO()
    tree = ET.ElementTree(root)
    tree.write(xml_bytes_io, encoding="UTF-8", xml_declaration=True)
    xml_string = xml_bytes_io.getvalue()

    logger.info("Convertendo para xml o csv de departamentos")

    return Response(
        content=xml_string,
        media_type="aplication/xml"
    )

@router.post("/department", response_model=Department)
def create_department(department: Department):
    departments = read_csv_department()
    departments.append(department)
    write_csv_department(departments)
    logger.info("Departamento criado com sucesso")
    return department

@router.get("/", response_model=List[Department])
def get_departments():
    logger.info("Retornando todos os departamentos")
    return read_csv_department()

@router.get("/{department_id}", response_model=Department)
def get_department(department_id: int):
    for d in read_csv_department():
        if d.id == department_id:
            logger.info(f"Retornando departamento de ID: {department_id}")
            return d
    raise HTTPException(status_code=404, detail="Departamento não encontrado")

@router.put("/{department_id}", response_model=Department)
def update_department(department_id: int, department: Department):
    departments = read_csv_department()
    for i, d in enumerate(departments):
        if d.id == department_id:
            departments[i] = department
            write_csv_department(departments)
            logger.info(f"Departamento com ID {department_id} atualizado com sucesso")
            return department
    raise HTTPException(status_code=404, detail="Departamento não encontrado")

@router.delete("/{department_id}")
def delete_department(department_id: int):
    departments = read_csv_department()
    for i, d in enumerate(departments):
        if d.id == department_id:
            del departments[i]
            write_csv_department(departments)
            logger.info(f"Departamento com ID {department_id} deletado com sucesso")
            return {"message": "Departamento deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Departamento não encontrado")

@router.get("/departments/name", response_model=List[Department])
def get_department_by_name(name: str):
    departments  = read_csv_department()
    if not name:
        raise HTTPException(status_code=400, detail="Nome do departamento não pode ser vazio")
    filtered_departments = [d for d in departments if d.name == name]
    if not filtered_departments:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    logger.info(f"Retornando departamentos com o nome: {name}")
    return filtered_departments


