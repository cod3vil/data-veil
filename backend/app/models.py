from sqlalchemy import Column, String, BigInteger, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, TypeDecorator, CHAR, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


# Custom UUID type for cross-database compatibility
class UUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


class Task(Base):
    """Task model for tracking desensitization tasks"""
    __tablename__ = "tasks"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(10), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), nullable=False, default="uploaded")
    content = Column(Text, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_upload_time', 'upload_time'),
    )


class SensitiveItem(Base):
    """Sensitive item model for storing identified sensitive data"""
    __tablename__ = "sensitive_items"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)
    value = Column(Text, nullable=False)
    start_pos = Column(Integer, nullable=False)
    end_pos = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_sensitive_items_task_id', 'task_id'),
    )


class DesensitizationRule(Base):
    """Desensitization rule model"""
    __tablename__ = "desensitization_rules"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    data_type = Column(String(20), nullable=False)
    strategy = Column(String(20), nullable=False)
    is_system = Column(Boolean, nullable=False, default=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OperationLog(Base):
    """Operation log model for audit purposes"""
    __tablename__ = "operation_logs"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    operation_type = Column(String(50), nullable=False)
    user_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_operation_logs_task_id', 'task_id'),
        Index('idx_operation_logs_created_at', 'created_at'),
    )
