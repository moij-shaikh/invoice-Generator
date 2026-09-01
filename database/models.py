from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column
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
    is_verified:Mapped[bool]=mapped_column(default=False)
    is_active:Mapped[bool]=mapped_column(default=True)
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    last_login:Mapped[datetime]=mapped_column(DateTime(timezone=True))

class Business(Base):
    __tablename__="business"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    business_name:Mapped[str]
    owner_name:Mapped[str]
    email:Mapped[str]=mapped_column(unique=True)
    phone:Mapped[str]
    website:Mapped[str]
    address_line1:Mapped[str]
    address_line2:Mapped[str]
    city:Mapped[str]
    state:Mapped[str]
    country:Mapped[str]
    currency:Mapped[str]
    create_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))