from fastapi import APIRouter, Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices , Quotation, Invoice
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload

from datetime import datetime, timezone

from schemas.job import Update, NewJob,  JobStatus
from schemas.quotation import QuotationStatus
from schemas.invoice import InvoiceStatus

router=APIRouter(tags=["Job"])

@router.post("/job")
async def job__new(
    new_job:NewJob,
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
):
    if not new_job.services:
        raise HTTPException(status_code=400, detail="At least one service is required.")
    services_ids=set()
    
    for item in new_job.services:
        if item.service_id in services_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate keys. ")
        if item.service_id not in services_ids:
            services_ids.add(item.service_id)
            
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id==user_id, Business.is_deleted == False))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found.")
    db_client= await db.scalar(select(Client).where(Client.id==new_job.client_id,Client.business_id==db_business.id, Client.is_deleted == False))
    if not db_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Client Found.")
    db_services= await db.scalars(select(Services).where(Services.id.in_(services_ids),Services.business_id==db_business.id, Services.is_deleted == False))
    db_services_list=db_services.all()
    if not db_services_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Services Found.")
    if len(services_ids) != len(db_services_list):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="One or more services were not found.")
    service_dict={service.id:service for service in db_services_list}
    if new_job.start_at > new_job.end_at:
        raise HTTPException(status_code=400,detail="Start date cannot be after end date.")
    total_price=0
    total_gst=0
    for item  in new_job.services:
        service=service_dict[item.service_id]
        if not service.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{service.id}: {service.name} is not active. ")
        subtotal=service.price * item.quantity
        gst=subtotal*(service.gst_percentage/100)
        total_price += subtotal
        total_gst +=gst
    final_total=total_price+total_gst
    db_job=Job(
        business_id=db_business.id,
        client_id=db_client.id,
        title=new_job.title,
        work=new_job.work,
        note=new_job.note,
        end_at=new_job.end_at,
        job_status=JobStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        start_at=new_job.start_at,
        total_price=final_total
    )
    
    try:
        db.add(db_job)
        await db.flush()
        new_db_services=[]
        for item in new_job.services:
            service=service_dict[item.service_id]
            new_db_services.append(
                JobServices(
                    job_id=db_job.id,
                    service_id=service.id,
                    quantity=item.quantity
                )
            )
            
        db.add_all(new_db_services)
        await db.commit()
        return{
            "message":f"New Job was added. ID: {db_job.id}"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down. ")

@router.get("/job")
async def job__get(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_business = await db.scalar(select(Business).where(Business.user_id == user_id,Business.is_deleted == False))
    if not db_business:
        raise HTTPException(status_code=404,detail="No Business Found.")
    db_jobs= await db.scalars(select(Job).where(Job.business_id == db_business.id))
    db_jobs_list=db_jobs.all()
    return db_jobs_list

@router.get("/job/{id}")
async def job__get_id(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id == user_id, Business.is_deleted == False))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found")
    db_job= await db.scalar(select(Job).join(Business, Business.id == Job.business_id).where(Job.id==id, Business.user_id == user_id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    db_services= await db.execute(select(Services,JobServices).join(JobServices,JobServices.service_id == Services.id).where(JobServices.job_id == id , Services.is_deleted ==False, Services.is_active==True))
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
                "price":service.price,
                "quantity":job_service.quantity,
                "gst":service.gst_percentage
            }
            for service, job_service in db_services_list

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
    if existing:
        if existing.quotation_status not in  {QuotationStatus.PENDING , QuotationStatus.CANCEL, QuotationStatus.REJECTED}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Job can not be modified. ")
    existing= await db.scalar(select(Invoice).join(Business, Business.id == Invoice.business_id).where(Invoice.job_id == db_job.id, Business.user_id == user_id))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice exist for this job.  ")          
    if db_job.job_status == JobStatus.DONE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already done. ")
    if db_job.job_status in {JobStatus.CANCEL, JobStatus.REJECTED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already cancelled. ")
        
    try:
        db_job.job_status=JobStatus.CANCEL
        db_job.update_at=datetime.now(timezone.utc)
        await db.commit()
        return {
           "message": "Job cancelled successfully."
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

@router.patch("/job/{id}")
async def job__update(user_data:Update,id:int=Path(gt=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    json_data=user_data.model_dump(exclude_none=True)
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business, Business.id == Job.business_id).where(Job.id == id, Business.user_id == user_id))
    
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    existing_quotation= await db.scalar(select(Quotation).join(Business, Quotation.business_id == Business.id).where(Business.user_id == user_id, Quotation.job_id == id))
    if existing_quotation:
        if existing_quotation.quotation_status not in {QuotationStatus.PENDING, QuotationStatus.CANCEL, QuotationStatus.REJECTED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job can not be modified.  ")
    existing_invoice=await db.scalar(select(Invoice).join(Business, Business.id == Invoice.business_id).where(Business.user_id == user_id, Invoice.job_id == id))
    if existing_invoice:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice exist for this job.  ")
    
    if db_job.job_status== JobStatus.CANCEL.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can not modify cancelled job. ")
    if db_job.job_status== JobStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is rejected. ")
    if db_job.job_status== JobStatus.DONE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can not modify already completed job.  ")
    if db_job.job_status== JobStatus.WORKING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is under development can not modify it.  ")
    
    new_start = json_data.get("start_at", db_job.start_at)
    new_end = json_data.get("end_at", db_job.end_at)

    if new_start > new_end:
        raise HTTPException( status_code=400, detail="Start date cannot be after end date.")
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
async def job__update_services(service_id:int,id:int=Path(gt=0),new_service:int=Form(gt=0), quantity:float=Form(gt=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business,Business.id == Job.business_id).where(Job.id == id,Business.user_id == user_id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Job Found. ")
    if db_job.job_status in {JobStatus.CANCEL, JobStatus.REJECTED, JobStatus.DONE, JobStatus.WORKING}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job cannot be modified.  ")

    db_job_service= await db.scalar(select(JobServices).join(Job,JobServices.job_id == Job.id
    ).join(Business,Business.id == Job.business_id).where(JobServices.service_id == service_id, Business.user_id == user_id, JobServices.job_id==db_job.id))
    if not db_job_service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No Job Found with Service id: {service_id}. ")
    
    existing_quotation= await db.scalar(select(Quotation).join(Business, Quotation.business_id == Business.id).where(Business.user_id == user_id, Quotation.job_id == id))
    if existing_quotation:
         if existing_quotation.quotation_status not in {QuotationStatus.PENDING, QuotationStatus.CANCEL, QuotationStatus.REJECTED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job can not be modified.  ")
    existing_invoice=await db.scalar(select(Invoice).join(Business, Business.id == Invoice.business_id).where(Business.user_id == user_id, Invoice.job_id == id))
    if existing_invoice:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An Invoice exist for this job.  ")
    
    
    previous_service = await db.scalar(select(Services).join(Business, Business.id == Services.business_id).where(Services.id == service_id, Business.user_id== user_id))
    existing_service= await db.scalar(select(JobServices).join(Services, JobServices.service_id == Services.id).join(Business, Services.business_id == Business.id)
                                      .where(
                                          Business.user_id ==  user_id, 
                                          JobServices.job_id == id, 
                                          JobServices.service_id == new_service
                                      ))
    if existing_service:
        raise HTTPException(status_code=409,detail="This service already exists in the job.")
    if not previous_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Service Found. ")

    
    db_check = await db.scalar(select(Services).where(Services.id==new_service,Services.business_id==db_job.business_id, Services.is_deleted==False))
    if not db_check:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Service Found. ")
    if db_check.is_deleted or not db_check.is_active:
        raise HTTPException( status_code=409, detail="Selected service is inactive or deleted.")
    price=db_check.price * quantity
    gst=price * (db_check.gst_percentage/100)
    total=price+gst
    previous_subtotal=previous_service.price * db_job_service.quantity
    previous_gst=previous_subtotal* (previous_service.gst_percentage/100)
    previous_total=previous_subtotal+ previous_gst
    try:
        db_job.total_price -= previous_total
        db_job.total_price += total
        
        db_job_service.service_id = db_check.id
        db_job_service.quantity=quantity
        db_job.update_at=datetime.now(timezone.utc)
        await db.commit()

        return {
            "message":"Service updated successfully. "
            }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

