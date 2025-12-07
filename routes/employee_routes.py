from fastapi import APIRouter, HTTPException
from typing import List
from model.employee import Employee
from services.employee_service import read_csv_employee, write_csv_employee, ARQUIVO_EMPLOYEE
from services.department_service import read_csv_department
from logger import logger
from fastapi.responses import Response
from io import BytesIO, StringIO
import zipfile
import csv
from hashlib import sha256
import xml.etree.ElementTree as ET

router = APIRouter(prefix="/employees", tags=["Funcionários"])

@router.get("/quantity")
def count_employees():
    count = len(read_csv_employee())

    logger.info("Retornando quantidade de funcionários")

    return { "quantidade": count }

@router.get("/SHA256")
def calculate_hash_256():
    with open(ARQUIVO_EMPLOYEE, "rb") as file:
        data = file.read()
        encrypted_data = sha256(data).hexdigest()

        logger.info("Calculando o hash de funcionários")

        return { "hash_sha_256": encrypted_data}

@router.get("/xml")
def convert_csv_to_xml():
    root = ET.Element("employees")

    for row in read_csv_employee():
        employee = ET.SubElement(root, "employee")

        for key, emp in row.dict().items():
            field = ET.SubElement(employee, key)
            field.text = str(emp)

    xml_bytes_io = BytesIO()
    tree = ET.ElementTree(root)
    tree.write(xml_bytes_io, encoding="UTF-8", xml_declaration=True)
    xml_string = xml_bytes_io.getvalue()

    logger.info("Convertendo para xml o csv de funcionários")

    return Response(
        content=xml_string,
        media_type="aplication/xml"
    )

@router.post("/employee", response_model=Employee)
def create_employee(employee: Employee):
    if not any(d.id == employee.id_department for d in read_csv_department()):
        raise HTTPException(status_code=400, detail="Departamento não encontrado")
    employees = read_csv_employee()
    employees.append(employee)
    write_csv_employee(employees)
    logger.info("Funcionário criado com sucesso")
    return employee

@router.get("/", response_model=List[Employee])
def get_employees():
    logger.info("Retornando todos os funcionários")
    return read_csv_employee()

@router.put("/{employee_id}", response_model=Employee)
def update_employee(employee_id: int, employee: Employee):
    if not any(d.id == employee.id_department for d in read_csv_department()):
        raise HTTPException(status_code=400, detail="Departamento não encontrado")
    employees = read_csv_employee()
    for i, e in enumerate(employees):
        if e.id == employee_id:
            employees[i] = employee
            write_csv_employee(employees)
            logger.info(f"Funcionário com ID {employee_id} atualizado com sucesso")
            return employee
    raise HTTPException(status_code=404, detail="Funcionário não encontrado")

@router.delete("/{employee_id}")
def delete_employee(employee_id: int):
    employees = read_csv_employee()
    for i, e in enumerate(employees):
        if e.id == employee_id:
            del employees[i]
            write_csv_employee(employees)
            logger.info(f"Funcionário com ID {employee_id} deletado com sucesso")
            return {"message": "Funcionário deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Funcionário não encontrado")

@router.get("/name", response_model=List[Employee])
def get_employee_by_name(name: str):
    employees = read_csv_employee()
    if not name:
        raise HTTPException(status_code=400, detail="Nome do funcionário não pode ser vazio")
    filtered_employees = [e for e in employees if e.name == name]
    if not filtered_employees:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    logger.info(f"Retornando funcionários com o nome: {name}")
    return filtered_employees

@router.get("/cpf", response_model=Employee)
def get_employee_by_cpf(cpf: str):
    employees = read_csv_employee()
    if not cpf:
        raise HTTPException(status_code=400, detail="CPF do funcionário não pode ser vazio")
    for e in employees:
        if e.cpf == cpf:
            logger.info(f"Retornando funcionário com CPF: {cpf}")
            return e
    raise HTTPException(status_code=404, detail="Funcionário não encontrado")

@router.get("/department/{department_id}", response_model=List[Employee])
def get_employees_by_department(department_id: int):
    employees = read_csv_employee()
    if not department_id:
        raise HTTPException(status_code=400, detail="ID do departamento não pode ser vazio")
    filtered_employees = [e for e in employees if e.id_department == department_id]
    if not filtered_employees:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    logger.info(f"Retornando funcionários do departamento com ID: {department_id}")
    return filtered_employees

@router.get("/zip")
def get_employees_zip():
    departments = read_csv_employee()
    if not departments:
        raise HTTPException(status_code=404, detail="Nenhum funcionário encontrado")

    csv_string_io = StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=departments[0].dict().keys())
    writer.writeheader()
    for dept in departments:
        writer.writerow(dept.dict())

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("employee.csv", csv_string_io.getvalue())

    zip_buffer.seek(0)

    logger.info("employee.csv convertido para .zip")

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=employee.zip"}
    )

@router.get("/{employee_id}", response_model=Employee)
def get_employee(employee_id: int):
    for e in read_csv_employee():
        if e.id == employee_id:
            logger.info(f"Retornando funcionário de ID: {employee_id}")
            return e
    raise HTTPException(status_code=404, detail="Funcionário não encontrado")