from contextlib import contextmanager
from enum import Enum
from typing import Generator, Any, Optional

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import Session, relationship

from config.database_config import SessionLocal
from helper import DateUtils
from models.base_model import BaseModel


class ServicePackage(Enum):
    TRIAL = "TRIAL"
    BASIC = "BASIC"
    PRO = "PRO"
    BUSINESS = "BUSINESS"


class GroupPackage(BaseModel):
    __tablename__ = "group_package"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chat_group.chat_id"), unique=True, nullable=False)
    package = Column(
        SQLAlchemyEnum(ServicePackage), nullable=False, default=ServicePackage.TRIAL
    )
    is_paid = Column(Boolean, default=False)
    package_start_date = Column(DateTime, nullable=True)
    package_end_date = Column(DateTime, nullable=True)
    last_paid_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=DateUtils.now, nullable=False)
    updated_at = Column(DateTime, default=DateUtils.now, onupdate=DateUtils.now, nullable=False)
    
    # One-to-one relationship with chat_group
    chat = relationship("Chat", backref="group_package", uselist=False)


class GroupPackageService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def get_package_by_chat_id(self, chat_id: int) -> Optional[GroupPackage]:
        """Get group package info for a chat"""
        with self._get_db() as db:
            package = db.query(GroupPackage).filter(
                GroupPackage.chat_id == chat_id
            ).first()
            return package

    async def create_group_package(self, chat_id: int, package: ServicePackage = ServicePackage.TRIAL) -> GroupPackage:
        """Create a new group package record for a chat"""
        with self._get_db() as db:
            group_package = GroupPackage(
                chat_id=chat_id,
                package=package,
                is_paid=False if package == ServicePackage.TRIAL else True,
                created_at=DateUtils.now(),
                updated_at=DateUtils.now()
            )
            
            try:
                db.add(group_package)
                db.commit()
                db.refresh(group_package)
                return group_package
            except Exception as e:
                db.rollback()
                raise e

    async def update_package(
        self, 
        chat_id: int, 
        package: ServicePackage,
        package_start_date: Optional[DateTime] = None,
        package_end_date: Optional[DateTime] = None,
        last_paid_date: Optional[DateTime] = None
    ) -> Optional[GroupPackage]:
        """Update package information for a chat"""
        with self._get_db() as db:
            group_package = db.query(GroupPackage).filter(
                GroupPackage.chat_id == chat_id
            ).first()
            
            if group_package:
                group_package.package = package
                group_package.is_paid = False if package == ServicePackage.TRIAL else True
                group_package.updated_at = DateUtils.now()
                
                if package_start_date:
                    group_package.package_start_date = package_start_date
                if package_end_date:
                    group_package.package_end_date = package_end_date
                if last_paid_date:
                    group_package.last_paid_date = last_paid_date
                    
                db.commit()
                db.refresh(group_package)
                return group_package
            return None

    async def get_or_create_group_package(self, chat_id: int) -> GroupPackage:
        """Get existing group package or create a new one with TRIAL package"""
        existing = await self.get_package_by_chat_id(chat_id)
        if existing:
            return existing
        return await self.create_group_package(chat_id, ServicePackage.TRIAL)