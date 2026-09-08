from fastapi import APIRouter, Form , Depends , Path , HTTPException , status , Request , Response
from fastapi.security import OAuth2PasswordRequestForm
from database.database import get_db
from database.models import User , Business

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession

from redis_client import redis

import secrets
from datetime import datetime , timedelta , timezone

from services.user_auth import make_access_token , make_refresh_token , get_current_user_payload , user__logout , refresh_endpoint
from services.utils import pass_hasher

router=APIRouter(prefix="/user")

@router.post("",tags=["User"])
async def user__register_new_user(
    req:Request,
    email:str=Form(),
    password:str=Form(),
    db:AsyncSession=Depends(get_db)
):
    user=User(
        email=email,
        password=pass_hasher.hash(password),
        create_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    try:
        await db.commit()
        token=secrets.token_urlsafe(8)
        await redis.set(f"email_verification_token:{token}",email,ex=60*5)
        # await req.app.state.arq.enqueue_job("")
        return {
            "message":f"User was successfully Registered and Verification email was sended. {token}"
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

@router.delete("")
async def user__delete(
    res:Response,
    user_id:int=Form(),
    email:str=Form(),
    password:str=Form(),
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
):
    db_user= await db.scalar(select(User).where(User.id==user_id,User.email==email))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No user Found")
    if not pass_hasher.verify(password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Your are not Authorized")
    try:
        await db.delete(db_user)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")


@router.get("/verifies",tags=["Auth"])
async def user__verify_email(
    token:str,
    db:AsyncSession=Depends(get_db)
):
    user_email=await redis.get(f"email_verification_token:{token}")
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token was either wrong or expired")
    db_user= await db.scalar(select(User).where(User.email==user_email))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No user Found")
    db_user.is_verified=True
    try:
        await db.commit()
        return{
            "message":f"{db_user.email} you have been successfully verified"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

@router.post("/login",tags=["User"])
async def user__login(
    res:Response,
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:AsyncSession=Depends(get_db)
):
    password=form_data.password
    email=form_data.username
    db_user= await db.scalar(select(User).where(User.email == email))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No user Found")
    if not pass_hasher.verify(password,db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Your are not Authorized")
    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Verify Your Email")
    if db_user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Your Account has been blocked")

    access_token=make_access_token(db_user.id)
    token_id=str(secrets.token_urlsafe(4))
    refresh_token=make_refresh_token(db_user.id,token_id=token_id,role="user")
    res.set_cookie(key="refresh_token",value=refresh_token,samesite="strict",httponly=True,max_age=60*60*24*10)
    await redis.set(f"refresh_token:{token_id}",db_user.id,ex=60*60*24*10)
    db_user.last_login=datetime.now(timezone.utc)
    return {
        "token_type":"bearer",
        "access_token":access_token
    }

@router.post("/logout",tags=["User"])
async def user__logout(payload:dict=Depends(get_current_user_payload),message:str=Depends(user__logout)):
    return {
        "message":message
    }
@router.post("/refresh",tags=["Auth"])
async def user__refresh_token(token:str=Depends(refresh_endpoint)):
    return {
        "token_type":"bearer",
        "access_token":token
    }