from pydantic import BaseModel , Field

class GetBusiness(BaseModel):
    business_name:str
    owner_name:str
    email:str
    phone:str
    website:str
    address_line1:str
    address_line2:str
    city:str
    state:str
    country:str
    currency:str
class UpdateBusiness(BaseModel):
    gst_number:str|None=Field(default=None)
    business_name:str|None=Field(default=None)
    owner_name:str|None=Field(default=None)
    email:str|None=Field(default=None)
    phone:str|None=Field(default=None)
    website:str|None=Field(default=None)
    address_line1:str|None=Field(default=None)
    address_line2:str|None=Field(default=None)
    city:str|None=Field(default=None)
    state:str|None=Field(default=None)
    country:str|None=Field(default=None)
    currency:str|None=Field(default=None)