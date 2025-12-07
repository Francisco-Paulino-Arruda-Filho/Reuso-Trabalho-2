from uuid import uuid4
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    name: str
    manager: str
    location: str
    number_of_employees: int

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    id_crud_verify: str = uuid4().hex