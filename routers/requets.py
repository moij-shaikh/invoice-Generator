from fastapi import APIRouter, Form , Depends , Path , HTTPException , status , Request , Response , File, UploadFile
from database.database import get_db
from database.models import User , Business , Services , ServiceRequest , Client

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redis_client import redis
from datetime import datetime  , timezone

from schemas.request import NewClient , RequestStatus
from services.user_auth import get_current_user_payload

router=APIRouter(tags=["Request"])

@router.get("/seller/request")
async def request_seller__get_all(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get('sub'))
    db_requests= await db.scalars(select(ServiceRequest).join(Business,ServiceRequest.business_id == Business.id).where(Business.user_id == user_id))
    db_requests_list= db_requests.all()
    if not db_requests_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Request Found")
    display_list=[
        {
            "id":req.id,
            "services":req.services,
            "work":req.work,
            "notes":req.notes,
            "status":req.status,
            "create_at":req.create_at,
        }
        for req in db_requests_list
    ]
    return display_list

@router.patch("/seller/request/{id}/status")
async def request_seller__update_status(id:int, new_status:str=Form(),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))

    db_request= await db.scalar(select(ServiceRequest).join(Business, ServiceRequest.business_id == Business.id).where(Business.user_id == user_id, ServiceRequest.id == id))
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Request Found")
    db_request.status = new_status
    try:
        await db.commit()
        if new_status == RequestStatus.ACCEPT:
            print("send buyer email")
        return "Status updated. "
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Db is down.")


@router.get("/buyer/request/view")
async def request_buyer__view_all(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_requests= await db.scalars(select(ServiceRequest).where(ServiceRequest.user_id == user_id))
    db_requests_list=db_requests.all()
    if not db_requests_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Request found. ")
    return db_requests_list

@router.get("/buyer/request/view/{id}")
async def request_buyer__get_one(id:int=Path(gt=0), payload:dict=Depends(get_current_user_payload), db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_request= await db.scalar(select(ServiceRequest).where(ServiceRequest.user_id == user_id, ServiceRequest.id ==id))
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Request found. ")
    return db_request

@router.post("/buyer/request/{id}/share")
async def request_buyer__accepted(req:Request,id:int, share_data:bool, new_client:NewClient,payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_request= await db.scalar(select(ServiceRequest).where(ServiceRequest.user_id == user_id, ServiceRequest.id ==id))
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Request found. ")
    if db_request.status.lower() != RequestStatus.ACCEPT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Request found Or request is rejected. ")

    if not share_data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you need to confirm to share data with seller. ")
    db_client=Client(
            business_id=db_request.business_id,
            name=new_client.name,
            email=new_client.email,
            phone=new_client.phone,
            address_line1=new_client.address_line1,
            address_line2=new_client.address_line2,
            city=new_client.city,
            state=new_client.state,
            country=new_client.country,
            notes="Automatic Client",
            create_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    try: 
        db.add(db_client)
        await db.flush()
        await db.commit()
        await req.app.state.arq.enqueue_job(
            "MakeJob",
            business_id=db_request.business_id,
            client_id=db_client.id,
            title=new_client.title,
            work=new_client.work,
            note=new_client.notes,
            end_at=new_client.end_at,
            job_status="quotation",
            created_at=datetime.now(timezone.utc),
            start_at=new_client.start_at,
            service_ids=[int(service_id.strip()) for service_id in db_request.services]
            )
        return{
            "message":"Data was shared successfully. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database is down. ")