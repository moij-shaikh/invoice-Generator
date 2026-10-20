from pydantic import BaseModel
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
    
    work:str
    notes:str
    end_at:datetime
    start_at:datetime
    title:str