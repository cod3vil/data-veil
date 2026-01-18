from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models import Task, SensitiveItem, DesensitizationRule, OperationLog
from app.schemas import (
    TaskResponse, SensitiveItemResponse, DesensitizationRuleResponse,
    PreviewRequest, PreviewResponse, ExportRequest, FileType, TaskStatus
)
from app.config import settings
from app.document_parser import DocumentParser
from app.recognition_engine import RecognitionEngine
from app.desensitization_processor import DesensitizationProcessor
from app.file_exporter import FileExporter
from app.logging_service import LoggingService
from app.exceptions import (
    FileUploadError,
    DocumentParsingError,
    RecognitionError,
    DesensitizationProcessingError,
    ExportError
)
from fastapi.responses import StreamingResponse
import io

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".md"}


@router.post("/upload", response_model=TaskResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document file for desensitization.
    
    - Validates file format (PDF, DOCX, XLSX, TXT, MD)
    - Validates file size (max 50MB)
    - Saves file to upload directory
    - Creates task record in database
    """
    # Validate file format
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise FileUploadError(
            message=f"Unsupported file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
            error_code="UNSUPPORTED_FORMAT",
            details={"file_extension": file_ext, "allowed_extensions": list(ALLOWED_EXTENSIONS)}
        )
    
    # Read file content to validate size
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > settings.max_file_size:
        raise FileUploadError(
            message=f"File size exceeds maximum limit of {settings.max_file_size} bytes",
            error_code="FILE_SIZE_EXCEEDED",
            details={"file_size": file_size, "max_size": settings.max_file_size}
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Generate unique filename
    task_id = uuid.uuid4()
    file_path = os.path.join(settings.upload_dir, f"{task_id}{file_ext}")
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Determine file type
    file_type_map = {
        ".pdf": FileType.PDF,
        ".docx": FileType.DOCX,
        ".xlsx": FileType.XLSX,
        ".txt": FileType.TXT,
        ".md": FileType.MD
    }
    file_type = file_type_map[file_ext]
    
    # Create task record
    task = Task(
        id=task_id,
        filename=file.filename,
        file_size=file_size,
        file_type=file_type.value,
        status=TaskStatus.UPLOADED.value
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Log upload operation using logging service
    LoggingService.log_upload(
        db=db,
        task_id=task_id,
        filename=file.filename,
        file_size=file_size,
        file_type=file_type.value
    )
    
    return task


@router.post("/tasks/{task_id}/parse", response_model=TaskResponse)
async def parse_document(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Parse uploaded document and extract text content.
    
    - Retrieves task from database
    - Calls DocumentParser to extract text
    - Updates task status and content
    """
    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task is in correct status
    if task.status != TaskStatus.UPLOADED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in 'uploaded' status, current status: {task.status}"
        )
    
    # Get file path
    file_ext = os.path.splitext(task.filename)[1].lower()
    file_path = os.path.join(settings.upload_dir, f"{task_id}{file_ext}")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Parse document
        parser = DocumentParser()
        parsed_doc = parser.parse(file_path, task.file_type)
        
        # Update task
        task.content = parsed_doc.content
        task.file_metadata = parsed_doc.metadata
        task.status = TaskStatus.PARSED.value
        
        db.commit()
        db.refresh(task)
        
        return task
    except DocumentParsingError:
        # Re-raise custom parsing errors
        task.status = TaskStatus.FAILED.value
        db.commit()
        raise
    except Exception as e:
        # Wrap unexpected errors in DocumentParsingError
        task.status = TaskStatus.FAILED.value
        db.commit()
        raise DocumentParsingError(
            message=f"Failed to parse document: {str(e)}",
            error_code="PARSING_FAILED",
            details={"file_type": task.file_type, "original_error": str(e)}
        )


@router.post("/tasks/{task_id}/identify", response_model=List[SensitiveItemResponse])
async def identify_sensitive_data(
    task_id: uuid.UUID,
    use_nlp: bool = True,
    db: Session = Depends(get_db)
):
    """
    Identify sensitive information in parsed document.
    
    - Retrieves task from database
    - Calls RecognitionEngine to identify sensitive data
    - Saves identified items to database
    """
    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task is in correct status
    if task.status != TaskStatus.PARSED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Task must be in 'parsed' status, current status: {task.status}"
        )
    
    if not task.content:
        raise HTTPException(status_code=400, detail="Task has no content to analyze")
    
    try:
        # Identify sensitive data
        engine = RecognitionEngine()
        sensitive_items = engine.identify_sensitive_data(task.content, use_nlp=use_nlp)
        
        # Delete existing sensitive items for this task
        db.query(SensitiveItem).filter(SensitiveItem.task_id == task_id).delete()
        
        # Save identified items
        db_items = []
        for item in sensitive_items:
            db_item = SensitiveItem(
                task_id=task_id,
                type=item.type,
                value=item.value,
                start_pos=item.start_pos,
                end_pos=item.end_pos,
                confidence=item.confidence
            )
            db.add(db_item)
            db_items.append(db_item)
        
        # Update task status
        task.status = TaskStatus.IDENTIFIED.value
        
        db.commit()
        
        # Refresh all items to get their IDs
        for item in db_items:
            db.refresh(item)
        
        return db_items
    except RecognitionError:
        # Re-raise custom recognition errors
        task.status = TaskStatus.FAILED.value
        db.commit()
        raise
    except Exception as e:
        # Wrap unexpected errors in RecognitionError
        task.status = TaskStatus.FAILED.value
        db.commit()
        raise RecognitionError(
            message=f"Failed to identify sensitive data: {str(e)}",
            error_code="RECOGNITION_FAILED",
            details={"use_nlp": use_nlp, "original_error": str(e)}
        )


@router.get("/rules", response_model=List[DesensitizationRuleResponse])
async def get_desensitization_rules(db: Session = Depends(get_db)):
    """
    Get all pre-configured desensitization rules.
    
    - Queries all rules from database
    - Returns list of rules with their configurations
    """
    rules = db.query(DesensitizationRule).all()
    return rules


@router.post("/tasks/{task_id}/preview", response_model=PreviewResponse)
async def preview_desensitization(
    task_id: uuid.UUID,
    request: PreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview desensitization results.
    
    - Retrieves task and sensitive items
    - Applies selected rules to generate preview
    - Returns original and desensitized content comparison
    """
    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.content:
        raise HTTPException(status_code=400, detail="Task has no content")
    
    # Get sensitive items
    query = db.query(SensitiveItem).filter(SensitiveItem.task_id == task_id)
    
    # Filter by specific items if provided
    if request.sensitive_items:
        item_uuids = [uuid.UUID(item_id) for item_id in request.sensitive_items]
        query = query.filter(SensitiveItem.id.in_(item_uuids))
    
    sensitive_items = query.all()
    
    # Get selected rules
    rule_uuids = [uuid.UUID(rule_id) for rule_id in request.rules]
    rules = db.query(DesensitizationRule).filter(DesensitizationRule.id.in_(rule_uuids)).all()
    
    # Convert to processor format
    from app.recognition_engine import SensitiveItem as ProcessorSensitiveItem
    from app.desensitization_processor import DesensitizationRule as ProcessorRule
    
    processor_items = [
        ProcessorSensitiveItem(
            id=str(item.id),
            type=item.type,
            value=item.value,
            start_pos=item.start_pos,
            end_pos=item.end_pos,
            confidence=item.confidence
        )
        for item in sensitive_items
    ]
    
    processor_rules = [
        ProcessorRule(
            id=str(rule.id),
            name=rule.name,
            data_type=rule.data_type,
            strategy=rule.strategy,
            enabled=rule.enabled
        )
        for rule in rules
    ]
    
    # Apply desensitization
    processor = DesensitizationProcessor()
    desensitized_content = processor.process(task.content, processor_items, processor_rules)
    
    # Calculate statistics
    total_items = len(sensitive_items)
    desensitized_items = len([item for item in processor_items if any(
        rule.data_type == item.type and rule.enabled for rule in processor_rules
    )])
    
    # Log desensitization operation
    LoggingService.log_desensitization(
        db=db,
        task_id=task_id,
        applied_rules=[str(rule.id) for rule in rules],
        total_items=total_items,
        desensitized_items=desensitized_items
    )
    
    return PreviewResponse(
        original=task.content,
        desensitized=desensitized_content,
        statistics={
            "total_items": total_items,
            "desensitized_items": desensitized_items
        }
    )


@router.post("/tasks/{task_id}/export")
async def export_desensitized_document(
    task_id: uuid.UUID,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export desensitized document.
    
    - Applies desensitization rules
    - Exports to specified format
    - Returns file download response
    """
    # Get task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.content:
        raise HTTPException(status_code=400, detail="Task has no content")
    
    # Get sensitive items
    sensitive_items = db.query(SensitiveItem).filter(SensitiveItem.task_id == task_id).all()
    
    # Get selected rules
    rule_uuids = [uuid.UUID(rule_id) for rule_id in request.rules]
    rules = db.query(DesensitizationRule).filter(DesensitizationRule.id.in_(rule_uuids)).all()
    
    # Convert to processor format
    from app.recognition_engine import SensitiveItem as ProcessorSensitiveItem
    from app.desensitization_processor import DesensitizationRule as ProcessorRule
    
    processor_items = [
        ProcessorSensitiveItem(
            id=str(item.id),
            type=item.type,
            value=item.value,
            start_pos=item.start_pos,
            end_pos=item.end_pos,
            confidence=item.confidence
        )
        for item in sensitive_items
    ]
    
    processor_rules = [
        ProcessorRule(
            id=str(rule.id),
            name=rule.name,
            data_type=rule.data_type,
            strategy=rule.strategy,
            enabled=rule.enabled
        )
        for rule in rules
    ]
    
    # Apply desensitization
    processor = DesensitizationProcessor()
    desensitized_content = processor.process(task.content, processor_items, processor_rules)
    
    # Export to specified format
    exporter = FileExporter()
    
    # Determine output format
    output_format = request.output_format.value
    original_format = task.file_type
    
    # Export file
    file_bytes = exporter.export(
        desensitized_content,
        original_format,
        output_format,
        task.file_metadata or {}
    )
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = os.path.splitext(task.filename)[0]
    filename = f"{original_name}_desensitized_{timestamp}.{output_format}"
    
    # Update task status
    task.status = TaskStatus.COMPLETED.value
    db.commit()
    
    # Log download operation using logging service
    LoggingService.log_download(
        db=db,
        task_id=task_id,
        filename=filename,
        output_format=output_format
    )
    
    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
