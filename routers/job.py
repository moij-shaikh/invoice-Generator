from fastapi import APIRouter, Request, Response,Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload

from datetime import datetime, timezone

router=APIRouter()

@router.post("/job")
async def job__new(
    client_id:int=Form(...),
    services_ids_str:str=Form(...),
    title:str=Form(...),
    work:str=Form(...),
    note:str=Form(...),
    end_at:datetime=Form(),
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
):
    services_ids=[int(x) for x in services_ids_str.split(",")]
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id==user_id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found.")
    db_client= await db.scalar(select(Client).where(Client.id==client_id,Client.business_id==db_business.id))
    if not db_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Client Found.")
    db_services= await db.scalars(select(Services).where(Services.id.in_(services_ids),Services.business_id==db_business.id))
    db_services_list=db_services.all()
    if not db_services_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Services Found.")
    if len(services_ids) != len(db_services_list):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="One or more services were not found.")
    total_price=0
    for service in db_services_list:
        total_price+=service.price
    new_job=Job(
        business_id=db_business.id,
        client_id=db_client.id,
        title=title,
        work=work,
        note=note,
        end_at=end_at,
        job_status="quotation",
        created_at=datetime.now(timezone.utc),
        start_at=datetime.now(timezone.utc),
        total_price=total_price
    )
    db.add(new_job)
    await db.flush()
    new_db_services=[]
    for service in db_services_list:
        new_db_services.append(
            JobServices(
                job_id=new_job.id,
                service_id=service.id
            )
        )
    try:
        db.add_all(new_db_services)
        await db.commit()
        return{
            "message":f"{new_job.id}"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down. ")

@router.get("/job")
async def job__get(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))

    db_jobs= await db.scalars(select(Job).where(Job.client.has(Client.business.has(Business.user_id == user_id))))
    db_jobs_list=db_jobs.all()

    return db_jobs_list

@router.get("/job/{id}")
async def job__get_id(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).where(Job.id==id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    db_services= await db.scalars(select(Services).join(JobServices,JobServices.service_id == Services.id).where(JobServices.job_id == id))
    db_services_list=db_services.all()

    display_list={
        "job id":db_job.id,
        "title":db_job.title,
        "work":db_job.work,
        "note":db_job.note,
        "created at":db_job.created_at,
        "started at":db_job.start_at,
        "end at":db_job.end_at,
        "total":db_job.total_price,
        "services":[
            {
                "services id" : service.id,
                "name":service.name,
                "pricing_type":service.pricing_type,
                "unit":service.unit,
                "price":service.price
            }
            for service in db_services_list

        ]
    }
    return display_list