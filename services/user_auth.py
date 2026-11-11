from jose import jwt
from jose.exceptions import JWTError , ExpiredSignatureError 
from config import JWT_ALGORITHM , JWT_SECRET_KEY
from datetime import datetime , timezone , timedelta
import secrets
from fastapi import Depends , status , HTTPException , Request , Response
from fastapi.security import OAuth2PasswordBearer
from redis_client import redis
from database.database import get_db
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
def make_access_token(sub:str,role:str="user")->str:
    payload={
        "sub":str(sub),
        "role":role,
        "exp":datetime.now(timezone.utc) + timedelta(minutes=10),
        "token_id":str(secrets.token_urlsafe(4))
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)
    return token

def make_refresh_token(sub:str,role:str,token_id:str|None=None)->str:
    payload={
        "sub":str(sub),
        "role":role,
        "exp":datetime.now(timezone.utc) + timedelta(days=10),
        "token_id":token_id
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)
    return token

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login",scheme_name="User")

async def get_current_user_payload(token:str=Depends(get_jwt_token), db:AsyncSession=Depends(get_db))->dict:
    try:
        payload=jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
        user_id=int(payload.get('sub'))
        db_user= await db.get(User, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No User found. ")
        if db_user.is_deleted == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has been deleted. ")
        if db_user.is_blocked == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has been blocked. ")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login First")

async def user__logout(res:Response,req:Request):
    cookie=req.cookies.get("refresh_token")
    if not cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Already Logout.")
    try:
        payload=jwt.decode(cookie,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
        token_id=payload.get("token_id")
        redis_token= await redis.get(f"refresh_token:{token_id}")
        if not redis_token:
            res.delete_cookie("refresh_token")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Already Logout.")
        await redis.delete(f"refresh_token:{token_id}")
        res.delete_cookie("refresh_token")
        return "logout successfully"

    except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login First")

async def refresh_endpoint(req:Request, res:Response,db:AsyncSession=Depends(get_db)):
    cookie=req.cookies.get("refresh_token")
    if not cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login. token")
    try:
        payload=jwt.decode(cookie,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
        
        token_id=payload.get("token_id")
        user_id=payload.get("sub")
        redis_token=await redis.get(f"refresh_token:{token_id}")
        if not redis_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login. redis")
        db_user= await db.get(User, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No User found. ")
        if db_user.is_deleted == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has been deleted. ")
        if db_user.is_blocked == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has been blocked. ")
        token_id=str(secrets.token_urlsafe(4))
        refresh_token=make_refresh_token(user_id, token_id=token_id, role="user")
        
        await redis.set(f"refresh_token:{token_id}", user_id, ex=60*60*24*10)
        res.set_cookie(key="refresh_token", value=redis_token, samesite="strict",httponly=True,max_age=60*60*24*10)
        access_token=make_access_token(user_id)
        return access_token
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT Error")
    

