from fastapi import APIRouter, Form , Depends , Path , HTTPException , status

from database.database import get_db
from database.models import User

from services.utils import pass_hasher

router=APIRouter(prefix="/user")

@router.post("/register")
async def user__register_new_user(
    email:str=Form(),
    password:str=Form(),
):
    user=User()