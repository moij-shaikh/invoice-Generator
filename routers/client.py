from fastapi import APIRouter , Depends , Path , HTTPException , status 
from database.database import get_db
from database.models import Client , Business

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime  , timezone

from schemas.client import NewClient , UpdateClient , GetClient
from services.user_auth import get_current_user_payload 

router=APIRouter(prefix="/client",tags=["Client"])

@router.post("")
async def client__new(new_client:NewClient,payload:dict=Depends(get_current_user_payload), db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id==user_id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No User Found")
    new_client=Client(
        business_id=db_business.id,
        name=new_client.name,
        email=new_client.email,
        phone=new_client.phone,
        address_line1=new_client.address_line1,
        address_line2=new_client.address_line2,
        city=new_client.city,
        state=new_client.state,
        country=new_client.country,
        notes=new_client.notes,
        create_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    try:
        db.add(new_client)
        await db.commit()
        return{
            "message":"New Client Created."
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")

@router.get("",response_model=list[GetClient])
async def client__get(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    data= await db.scalars(select(Client).join(Business).where(Business.user_id==user_id))
    return data.all()


@router.delete("/{id}")
async def client__delete(id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_client= await db.scalar(select(Client).where(Client.id==id,Client.business.has(Business.user_id==user_id)))
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Client Found")
    try:
        await db.delete(db_client)
        await db.commit()
        return {
            "message":f"{db_client.id}: {db_client.name} was deleted."
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")

@router.patch("/{id}")
async def client__update(user_data:UpdateClient,id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_client= await db.scalar(select(Client).where(Client.id == id , Client.business.has(Business.user_id ==  user_id)))
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Client Found")
    updated_data=user_data.model_dump(exclude_unset=True)
    for field , value in updated_data.items():
        setattr(db_client,field,value)
    db_client.updated_at=datetime.now(timezone.utc)
    try:

        await db.commit()
        await db.refresh(db_client)
        return {
            "message":f"{db_client.id}: {db_client.name}s Values are updated successfully. "
        }
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is down.")