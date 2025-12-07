from uuid import uuid4
from pydantic import BaseModel

class Department(BaseModel):
    id: int
    name: str
    manager: str
    location: str
    number_of_employees: int
    id_crud_verify: str = str(uuid4())