from core.database import Base
from sqlalchemy import (String,
                        Boolean,
                        Float,
                        Enum,
                        DateTime,
                        ForeignKey,
                        CheckConstraint,
                        UniqueConstraint,
                        JSON)
from sqlalchemy.orm import mapped_column,Mapped,relationship
from datetime import datetime
from app.utils.enums import AccountTypeEnum,KycStatusEnum
from typing import Optional

#NOTE - Base User Model
class BaseUser(Base):
    __tablename__ = 'user'
    id: Mapped[int]= mapped_column('id',primary_key=True,autoincrement=True)
    username:Mapped[str]=mapped_column(String(30),nullable=True,index=True,)
    profile_pic:Mapped[str] = mapped_column(String(255),nullable=True,)
    email :Mapped[str]= mapped_column(String,nullable=False,)
    phone_number:Mapped[str]=mapped_column(String(15),nullable=True,index=True,)
    password:Mapped[str]=mapped_column(String,nullable=False,)
    location:Mapped[str]=mapped_column(String(70),nullable=True,)
    account_type:Mapped[AccountTypeEnum]= mapped_column(Enum(AccountTypeEnum),nullable=False,default=AccountTypeEnum.client)
    is_active:Mapped[bool] = mapped_column(Boolean,default= True,)
    created_at: Mapped[datetime]= mapped_column(DateTime,default=datetime.now,)
    updated_at:Mapped[datetime]= mapped_column(DateTime,default=datetime.now,onupdate=datetime.now,)
    verified:Mapped[bool] = mapped_column(Boolean,default=False,)
    kyc_status:Mapped[KycStatusEnum]=mapped_column(Enum(KycStatusEnum),default=KycStatusEnum.pending,nullable= True,)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    fullname:Mapped[str]=mapped_column(String(50),nullable=True,)
    
    account_info = relationship("AccountInfo", back_populates="user",lazy='selectin',cascade='all, delete-orphan')
    
    #SECTION -  Chat Relationships
    sent_messages = relationship("Chat", foreign_keys="[Chat.sender_id]", back_populates="sender", lazy="selectin")
    received_messages = relationship("Chat", foreign_keys="[Chat.receiver_id]", back_populates="receiver", lazy="selectin")
    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": account_type,
    }
    __table_args__ = (
        UniqueConstraint("email", "account_type", name="uq_email_type"),
        UniqueConstraint("username", "account_type", name="uq_username_type"),
        
        CheckConstraint(
            f"account_type IN {tuple(item.value for item in AccountTypeEnum)}",
            name="check_account_type"
        ),
        CheckConstraint(
            f"kyc_status IN {tuple(item.value for item in KycStatusEnum)}",
            name="check_kyc_status"
        ),
                      )

    
    
#NOTE -  Buyer Model
class Client(BaseUser):
    __tablename__ = 'client'
    id: Mapped[int]= mapped_column(ForeignKey('user.id',ondelete='CASCADE'),primary_key=True,)
    properties = relationship('Property',back_populates='client',lazy='selectin')
    appointments=relationship('Appointment',back_populates='client',cascade='all, delete-orphan',lazy='selectin')
    payment_confirmations = relationship("PaymentConfirmation", back_populates="client", lazy="selectin",cascade='all, delete-orphan')
    
    __mapper_args__ = {
        "polymorphic_identity": AccountTypeEnum.client,
    }
   
#NOTE -  agent Model 
class Agent(BaseUser):
    __tablename__ = 'agent'
    id: Mapped[int]= mapped_column(ForeignKey('user.id',ondelete='CASCADE'),primary_key=True,)
    
    agency_name:Mapped[Optional[str]]=mapped_column(String(50),nullable=True,)
    rating:Mapped[float] = mapped_column(Float,nullable=True,default=0.0)
    listings = relationship('Property',back_populates='agent',cascade='all, delete-orphan',lazy='selectin')
    appointments=relationship('Appointment',back_populates='agent',cascade='all, delete-orphan',lazy='selectin')
    availabilities = relationship("Agent", back_populates="agent",cascade='all, delete-orphan',lazy='selectin')
    payment_confirmations = relationship("PaymentConfirmation", back_populates="agent", lazy="selectin",cascade = 'all, delete-orphan')
    __mapper_args__ = {
        "polymorphic_identity": AccountTypeEnum.agent,
    }