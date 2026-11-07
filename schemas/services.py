from pydantic import BaseModel , Field, ConfigDict
from datetime import datetime
class NewService(BaseModel):
    name:str
    description:str 
    pricing_type:str
    price:float= Field(gt=0)
    unit:str
    gst_percentage:float = Field(ge=0)
    is_active:bool

class ShowAllServices(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    name:str
    pricing_type:str
    price:float 
    unit:str
    is_active:bool

class ShowServices(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    name:str
    description:str
    pricing_type:str
    price:float
    unit:str
    gst_percentage:float
    is_active:bool
    create_at:datetime
    update_at:datetime

class UpdateService(BaseModel):
    name:str|None=None
    description:str|None=None
    pricing_type:str|None=None
    price:float|None=None
    unit:str|None=None
    gst_percentage:float|None=None
    is_active:bool|None=None