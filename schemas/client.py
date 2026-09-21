from pydantic import BaseModel , Field
from datetime import datetime

class NewClient(BaseModel):
    name:str
    email:str
    phone:str
    address_line1:str
    address_line2:str
    city:str
    state:str
    country:str
    notes:str

class GetClient(BaseModel):
    name:str
    email:str
    phone:str
    address_line1:str
    address_line2:str
    city:str
    state:str
    country:str
    notes:str

class UpdateClient(BaseModel):
    name:str|None=None
    email:str|None=None
    phone:str|None=None
    address_line1:str|None=None
    address_line2:str|None=None
    city:str|None=None
    state:str|None=None
    country:str|None=None
    notes:str|None=None
