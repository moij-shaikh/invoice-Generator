from database.models import Job, Services, JobServices , Business, Client
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError 

async def send_verification_email(ctx,otp,email):
    import smtplib
    from email.message import EmailMessage
    msg=EmailMessage()
    msg["From"]=""
    msg["To"]=email
    msg["Subject"]="Account Verification by MS"
    msg.add_alternative(f"<a href=''>Click</a>",subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login("sender","pass")

async def MakeJob(
    ctx,
    business_id,
    client_id,
    title,
    work,
    note,
    end_at,
    job_status,
    created_at,
    start_at,
    service_ids
    ):
    async with ctx["db"]() as db:
        service_ids=set(service_ids)
        if not service_ids:
            raise ValueError("At least one service is required. ")
        if start_at > end_at:
            raise ValueError("Start date cannot be after end. ")
        db_business= await db.scalar(select(Business).where(Business.id == business_id , Business.is_deleted == False))
        if not db_business:
            raise ValueError("Business does not exist.")
        db_client= await db.scalar(select(Client).where(
            Client.id == client_id, 
            Client.business_id == business_id, 
            Client.is_deleted == False
        ))
        if not db_client:
            raise ValueError("Client does not belong to this business.")
        db_services = await db.scalars(select(Services).where(Services.id.in_(service_ids), Services.business_id ==business_id, Services.is_deleted==False , Services.is_active == True))
        db_services_list=db_services.all()
        if len(db_services_list)!= len(service_ids):
            raise ValueError("some services dose not exists. ")
        total_price=0
        for service in db_services_list:
            subtotal+= service.price
            gst = subtotal *(service.gst_percentage / 100)
            total_price= subtotal + gst
        new_job=Job(
                business_id=business_id,
                client_id=client_id,
                title=title,
                work=work,
                note=note,
                end_at=end_at,
                job_status=job_status,
                created_at=created_at,
                start_at=start_at,
                total_price=total_price
            )
        
            
        try:
            db.add(new_job)
            await db.flush()
            db.add_all([
                JobServices(
                    job_id=new_job.id,
                    service_id=service.id,
                    quantity=0
                )
                for id in db_services_list
            ])
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            print("Error occurred")
            raise
        
