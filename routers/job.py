from fastapi import APIRouter, Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices , Quotation, Invoice
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload

from datetime import datetime, timezone

from schemas.job import Update, NewJob , ShowAllJob , ShowJob, JobStatus

router=APIRouter(tags=["Job"])

@router.post("/job")
async def job__new(
    new_job:NewJob,
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
):
    services_ids=set(new_job.services_ids_str)
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id==user_id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found.")
    db_client= await db.scalar(select(Client).where(Client.id==new_job.client_id,Client.business_id==db_business.id))
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
        if not service.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{service.id}: {service.name} is not active. ")
        total_price+=service.price
    new_job=Job(
        business_id=db_business.id,
        client_id=db_client.id,
        title=new_job.title,
        work=new_job.work,
        note=new_job.note,
        end_at=new_job.end_at,
        job_status=JobStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        start_at=new_job.start_at,
        total_price=total_price
    )
    db.add(new_job)
    
    try:
        await db.flush()
        new_db_services=[]
        for service in db_services_list:
            new_db_services.append(
                JobServices(
                    job_id=new_job.id,
                    service_id=service.id
                )
            )
        db.add_all(new_db_services)
        await db.commit()
        return{
            "message":f"New Job was added. ID: {new_job.id}"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down. ")

@router.get("/job", response_model=list[ShowAllJob])
async def job__get(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))

    db_jobs= await db.scalars(select(Job).where(Job.client.has(Client.business.has(Business.user_id == user_id))))
    db_jobs_list=db_jobs.all()

    return db_jobs_list

@router.get("/job/{id}", response_model=ShowJob)
async def job__get_id(id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business, Business.id == Job.business_id).where(Job.id==id, Business.user_id == user_id))
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

@router.delete("/job/{id}")
async def job__delete(id:int=Path(gt=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business).where(Job.id == id,Business.user_id == user_id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    existing= await db.scalar(select(Quotation).join(Business, Business.id == Quotation.business_id).where(Quotation.job_id == db_job.id, Business.user_id == user_id))
    if  existing:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Quotation exists for this job. ")
    existing= await db.scalar(select(Invoice).join(Business, Business.id == Invoice.business_id).where(Invoice.job_id == db_job.id, Business.user_id == user_id))
    if  existing:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Invoice exists for this job. ")
    try:
        await db.delete(db_job)
        await db.commit()
        return {
            "message":"Job was deleted"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

@router.patch("/job/{id}")
async def job__update(user_data:Update,id:int=Path(ge=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    json_data=user_data.model_dump(exclude_none=True)
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business, Business.id == Job.business_id).where(Job.id == id, Business.user_id == user_id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")

    for field , value in json_data.items():
        setattr(db_job,field, value)
    
    try:
        db_job.update_at=datetime.now(timezone.utc)
        await db.commit()
        return {
            "message":"New Values are added. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")
    
@router.patch("/job/{id}/service/{service_id}")
async def job__update_services(service_id:int,id:int=Path(ge=0),new_service:int=Form(),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
        
    previous_service = await db.scalar(select(Services).join(Business, Business.id == Services.business_id).where(Services.id == service_id, Business.user_id== user_id))
    if not previous_service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Service Found. ")
    
    db_job= await db.scalar(select(Job).join(Business,Business.id == Job.business_id).where(Job.id == id,Business.user_id == user_id))
    if not db_job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Job Found. ")
    db_check = await db.scalar(select(Services).where(Services.id==new_service,Services.business_id==db_job.business_id))
    if not db_check:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Service Found. ")
    db_job_service= await db.scalar(select(JobServices).join(Job,JobServices.job_id == Job.id
    ).join(Business,Business.id == Job.business_id).where(JobServices.job_id == id,JobServices.service_id == service_id, Business.user_id == user_id))
    if not db_job_service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No Job Found with Service id: {id}. ")
    new_total=(db_job.total_price - previous_service.price) + db_check.price
    try:
        db_job.total_price = new_total
        db_job_service.service_id = db_check.id
        db_job.update_at=datetime.now(timezone.utc)
        await db.commit()

        return {
            "message":"Service updated successfully. "
            }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

