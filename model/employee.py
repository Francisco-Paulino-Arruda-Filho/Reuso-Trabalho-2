from datetime import date
from uuid import uuid4
from pydantic import BaseModel


class Employee(BaseModel):
    id: int
    id_department: int
    name: str
    cpf: str
    position: str
    admission_date: date
    id_crud_verify: str = str(uuid4())