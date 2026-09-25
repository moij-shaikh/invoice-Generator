from pydantic import BaseModel , Field

class NewService(BaseModel):
    name:str
    description:str
    pricing_type:str
    price:float
    unit:str
    gst_percentage:float
    is_active:bool

class UpdateService(BaseModel):
    name:str|None=None
    description:str|None=None
    pricing_type:str|None=None
    price:float|None=None
    unit:str|None=None
    gst_percentage:float|None=None
    is_active:bool|None=None