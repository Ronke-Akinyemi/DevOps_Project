from pydantic import BaseModel


class Student(BaseModel):
    name : str
    level : str
