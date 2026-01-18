"""
Logging service for operation audit trail.

This module provides a centralized service for logging all operations
in the desensitization platform for audit and compliance purposes.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from app.models import OperationLog


class LoggingService:
    """Service for logging operations to the database"""
    
    @staticmethod
    def log_upload(
        db: Session,
        task_id: uuid.UUID,
        filename: str,
        file_size: int,
        file_type: str,
        user_id: Optional[str] = None
    ) -> OperationLog:
        """
        Log file upload operation.
        
        Args:
            db: Database session
            task_id: Task UUID
            filename: Original filename
            file_size: File size in bytes
            file_type: File type (pdf, docx, xlsx, txt, md)
            user_id: Optional user identifier
            
        Returns:
            Created OperationLog instance
        """
        log = OperationLog(
            task_id=task_id,
            operation_type="upload",
            user_id=user_id,
            details={
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def log_desensitization(
        db: Session,
        task_id: uuid.UUID,
        applied_rules: list,
        total_items: int,
        desensitized_items: int,
        user_id: Optional[str] = None
    ) -> OperationLog:
        """
        Log desensitization operation.
        
        Args:
            db: Database session
            task_id: Task UUID
            applied_rules: List of rule IDs or names that were applied
            total_items: Total number of sensitive items identified
            desensitized_items: Number of items that were desensitized
            user_id: Optional user identifier
            
        Returns:
            Created OperationLog instance
        """
        log = OperationLog(
            task_id=task_id,
            operation_type="desensitization",
            user_id=user_id,
            details={
                "applied_rules": applied_rules,
                "total_items": total_items,
                "desensitized_items": desensitized_items,
                "timestamp": datetime.now().isoformat()
            }
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def log_download(
        db: Session,
        task_id: uuid.UUID,
        filename: str,
        output_format: str,
        user_id: Optional[str] = None
    ) -> OperationLog:
        """
        Log file download operation.
        
        Args:
            db: Database session
            task_id: Task UUID
            filename: Downloaded filename
            output_format: Output file format
            user_id: Optional user identifier
            
        Returns:
            Created OperationLog instance
        """
        log = OperationLog(
            task_id=task_id,
            operation_type="download",
            user_id=user_id,
            details={
                "filename": filename,
                "output_format": output_format,
                "timestamp": datetime.now().isoformat()
            }
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_logs_by_task(
        db: Session,
        task_id: uuid.UUID
    ) -> list:
        """
        Retrieve all logs for a specific task.
        
        Args:
            db: Database session
            task_id: Task UUID
            
        Returns:
            List of OperationLog instances
        """
        return db.query(OperationLog).filter(
            OperationLog.task_id == task_id
        ).order_by(OperationLog.created_at).all()
    
    @staticmethod
    def get_logs_by_operation_type(
        db: Session,
        operation_type: str
    ) -> list:
        """
        Retrieve all logs for a specific operation type.
        
        Args:
            db: Database session
            operation_type: Type of operation (upload, desensitization, download)
            
        Returns:
            List of OperationLog instances
        """
        return db.query(OperationLog).filter(
            OperationLog.operation_type == operation_type
        ).order_by(OperationLog.created_at.desc()).all()
