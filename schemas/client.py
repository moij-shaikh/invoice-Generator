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
    create_at:datetime
    updated_at:datetime


