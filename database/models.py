from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column,relationship
from sqlalchemy import DateTime , ForeignKey
from datetime import datetime
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]
    password:Mapped[str]
    is_verified:Mapped[bool]=mapped_column(default=False)
    is_blocked:Mapped[bool]=mapped_column(default=False)
    is_active:Mapped[bool]=mapped_column(default=True)
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    last_login:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    business:Mapped["Business"]=relationship("Business",back_populates="user")

class Business(Base):
    __tablename__="business"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    gst_number:Mapped[str | None]=mapped_column(default=None)
    business_name:Mapped[str]
    owner_name:Mapped[str]
    email:Mapped[str]=mapped_column(unique=True)
    phone:Mapped[str]
    website:Mapped[str| None]=mapped_column(default=None)
    address_line1:Mapped[str]
    address_line2:Mapped[str | None]=mapped_column(default=None)
    city:Mapped[str]
    state:Mapped[str]
    country:Mapped[str]
    currency:Mapped[str]
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    user:Mapped["User"]=relationship("User",back_populates="business")
    clients:Mapped[list["Client"]]=relationship("Client",back_populates="business")

class Client(Base):
    __tablename__="client"
    id:Mapped[int]=mapped_column(primary_key=True)
    business_id:Mapped[int]=mapped_column(ForeignKey("business.id",ondelete='CASCADE'))
    name:Mapped[str]
    email:Mapped[str]
    phone:Mapped[str]
    address_line1:Mapped[str]
    address_line2:Mapped[str| None]=mapped_column(default=None)
    city:Mapped[str]
    state:Mapped[str]
    country:Mapped[str]
    notes:Mapped[str]
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    business:Mapped["Business"]=relationship("Business",back_populates="clients")

class Services(Base):
    __tablename__="services"
    id:Mapped[int]=mapped_column(primary_key=True)
    business_id:Mapped[int]=mapped_column(ForeignKey("business.id",ondelete="CASCADE"))
    name:Mapped[str]
    description:Mapped[str]
    pricing_type:Mapped[str]
    price:Mapped[float]
    unit:Mapped[str]
    gst_percentage:Mapped[float]
    is_active:Mapped[bool]
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    update_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))

class Job(Base):
    __tablename__="jobs"
    id:Mapped[int]=mapped_column(primary_key=True)
    business_id:Mapped[int]=mapped_column(ForeignKey("business.id",ondelete="CASCADE"))
    client_id:Mapped[int]=mapped_column(ForeignKey("client.id",ondelete="CASCADE"))
    job_status:Mapped[str]
    total_price:Mapped[int]
    title:Mapped[str]
    work:Mapped[str]
    note:Mapped[str]
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    start_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    end_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
class JobServices(Base):
    __tablename__="jobservices"
    id:Mapped[int]=mapped_column(primary_key=True)
    job_id:Mapped[int]=mapped_column(ForeignKey("jobs.id",ondelete="CASCADE"))
    service_id:Mapped[int]=mapped_column(ForeignKey("services.id",ondelete="CASCADE"))