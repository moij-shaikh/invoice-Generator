from pydantic import BaseModel , Field

class UpdateQuotation(BaseModel):
    discount:int | None =None
    status:str|None =None
