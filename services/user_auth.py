from jose import jwt , JWTError 
from config import JWT_ALGORITHM , JWT_SECRET_KEY
from datetime import datetime , timezone , timedelta
import secrets
from fastapi import Depends , status , HTTPException
from fastapi.security import OAuth2PasswordBearer

def make_access_token(sub:str,role:str)->str:
    payload={
        "sub":sub,
        "role":role,
        "exp":datetime.now(timezone.utc) + timedelta(minutes=10),
        "token_id":str(secrets.token_urlsafe(4))
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)
    return token
def make_refresh_token(sub:str,role:str)->str:
    payload={
        "sub":sub,
        "role":role,
        "exp":datetime.now(timezone.utc) + timedelta(days=10)
    }
    token=jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)
    return token

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login",scheme_name="User")

def get_current_user_payload(token:str=Depends(get_jwt_token)):
    try:
        payload=jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login First")