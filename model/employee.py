from datetime import date
from uuid import uuid4
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    id_department: int
    name: str
    cpf: str
    position: str
    admission_date: date

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    id_crud_verify: str = uuid4().hex