from pydantic import BaseModel , Field
from datetime import datetime

class NewRequest(BaseModel):
    services:str
    work:str
    notes:str|None=None