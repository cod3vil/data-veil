"""
Property-based tests for operation logging.

Feature: data-desensitization-platform
"""

import pytest
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io
import os
import uuid

from app.database import Base, get_db
from main import app
from app.models import Task, OperationLog, DesensitizationRule, SensitiveItem
from app.schemas import DataType, StrategyType


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_logging.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    
    # Create test upload directory
    os.makedirs("/tmp/test_uploads_logging", exist_ok=True)
    
    # Set upload directory for tests
    from app.config import settings
    settings.upload_dir = "/tmp/test_uploads_logging"
    
    # Create default desensitization rules
    db = TestingSessionLocal()
    rules = [
        DesensitizationRule(
            name="手机号脱敏",
            data_type=DataType.PHONE.value,
            strategy=StrategyType.MASK.value,
            is_system=True,
            enabled=True
        ),
        DesensitizationRule(
            name="身份证脱敏",
            data_type=DataType.ID_CARD.value,
            strategy=StrategyType.MASK.value,
            is_system=True,
            enabled=True
        ),
    ]
    for rule in rules:
        db.add(rule)
    db.commit()
    db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    
    # Clean up test files
    if os.path.exists("/tmp/test_uploads_logging"):
        for file in os.listdir("/tmp/test_uploads_logging"):
            os.remove(os.path.join("/tmp/test_uploads_logging", file))


# Strategies for generating test data
supported_formats = st.sampled_from([".pdf", ".docx", ".xlsx", ".txt", ".md"])
file_content_strategy = st.binary(min_size=1, max_size=1024)


# Feature: data-desensitization-platform, Property 18: Upload Operation Logging
@given(
    file_extension=supported_formats,
    file_content=file_content_strategy,
    filename_base=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_upload_operation_logging(file_extension, file_content, filename_base):
    """
    Property 18: Upload Operation Logging
    
    For any file upload operation, a log entry should be created 
    containing timestamp, filename, file size, and user identifier.
    
    Validates: Requirements 8.1
    """
    # Create a file-like object
    filename = f"{filename_base}{file_extension}"
    file = io.BytesIO(file_content)
    
    # Upload file
    response = client.post(
        "/api/v1/upload",
        files={"file": (filename, file, "application/octet-stream")}
    )
    
    # Should accept the upload
    assert response.status_code == 200
    data = response.json()
    task_id = data["id"]
    
    # Query the database for the log entry
    db = TestingSessionLocal()
    try:
        log_entry = db.query(OperationLog).filter(
            OperationLog.task_id == uuid.UUID(task_id),
            OperationLog.operation_type == "upload"
        ).first()
        
        # Log entry should exist
        assert log_entry is not None
        
        # Log should contain required fields
        assert log_entry.task_id == uuid.UUID(task_id)
        assert log_entry.operation_type == "upload"
        assert log_entry.created_at is not None  # Timestamp
        
        # Log details should contain filename, file_size, file_type
        assert log_entry.details is not None
        assert "filename" in log_entry.details
        assert log_entry.details["filename"] == filename
        assert "file_size" in log_entry.details
        assert log_entry.details["file_size"] == len(file_content)
        assert "file_type" in log_entry.details
        assert log_entry.details["file_type"] in ["pdf", "docx", "xlsx", "txt", "md"]
        
        # Timestamp should be in details
        assert "timestamp" in log_entry.details
        
    finally:
        db.close()



# Feature: data-desensitization-platform, Property 19: Desensitization Operation Logging
@given(
    text_content=st.text(min_size=50, max_size=500),
    phone_number=st.from_regex(r'1[3-9]\d{9}', fullmatch=True)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_desensitization_operation_logging(text_content, phone_number):
    """
    Property 19: Desensitization Operation Logging
    
    For any desensitization operation, a log entry should be created 
    containing timestamp, applied rules, and processing results.
    
    Validates: Requirements 8.2
    """
    # Create a task with content containing sensitive data
    db = TestingSessionLocal()
    try:
        # Create task
        task = Task(
            filename="test.txt",
            file_size=100,
            file_type="txt",
            status="identified",
            content=f"{text_content} {phone_number}"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Create sensitive item
        sensitive_item = SensitiveItem(
            task_id=task.id,
            type="phone",
            value=phone_number,
            start_pos=len(text_content) + 1,
            end_pos=len(text_content) + 1 + len(phone_number),
            confidence=0.95
        )
        db.add(sensitive_item)
        db.commit()
        db.refresh(sensitive_item)
        
        # Get a rule
        rule = db.query(DesensitizationRule).filter(
            DesensitizationRule.data_type == DataType.PHONE.value
        ).first()
        
        # Call preview endpoint (which triggers desensitization logging)
        response = client.post(
            f"/api/v1/tasks/{task.id}/preview",
            json={
                "rules": [str(rule.id)],
                "sensitive_items": [str(sensitive_item.id)]
            }
        )
        
        # Should succeed
        assert response.status_code == 200
        
        # Query the database for the log entry
        log_entry = db.query(OperationLog).filter(
            OperationLog.task_id == task.id,
            OperationLog.operation_type == "desensitization"
        ).first()
        
        # Log entry should exist
        assert log_entry is not None
        
        # Log should contain required fields
        assert log_entry.task_id == task.id
        assert log_entry.operation_type == "desensitization"
        assert log_entry.created_at is not None  # Timestamp
        
        # Log details should contain applied_rules and processing results
        assert log_entry.details is not None
        assert "applied_rules" in log_entry.details
        assert isinstance(log_entry.details["applied_rules"], list)
        assert str(rule.id) in log_entry.details["applied_rules"]
        
        # Should contain processing results
        assert "total_items" in log_entry.details
        assert "desensitized_items" in log_entry.details
        assert log_entry.details["total_items"] >= 0
        assert log_entry.details["desensitized_items"] >= 0
        
        # Timestamp should be in details
        assert "timestamp" in log_entry.details
        
    finally:
        db.close()


# Feature: data-desensitization-platform, Property 20: Download Operation Logging
@given(
    text_content=st.text(
        alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),  # Exclude control and surrogate characters
            min_codepoint=32,  # Start from space character
            max_codepoint=126  # ASCII printable characters
        ),
        min_size=50,
        max_size=500
    ),
    output_format=st.sampled_from(["txt", "md"])  # Only test formats that handle all text
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
def test_download_operation_logging(text_content, output_format):
    """
    Property 20: Download Operation Logging
    
    For any file download operation, a log entry should be created 
    containing timestamp and filename.
    
    Validates: Requirements 8.3
    """
    # Create a task with content
    db = TestingSessionLocal()
    try:
        # Create task
        task = Task(
            filename="test.txt",
            file_size=100,
            file_type="txt",
            status="identified",
            content=text_content
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Get a rule
        rule = db.query(DesensitizationRule).first()
        
        # Call export endpoint (which triggers download logging)
        response = client.post(
            f"/api/v1/tasks/{task.id}/export",
            json={
                "rules": [str(rule.id)],
                "output_format": output_format
            }
        )
        
        # Should succeed
        assert response.status_code == 200
        
        # Query the database for the log entry
        log_entry = db.query(OperationLog).filter(
            OperationLog.task_id == task.id,
            OperationLog.operation_type == "download"
        ).first()
        
        # Log entry should exist
        assert log_entry is not None
        
        # Log should contain required fields
        assert log_entry.task_id == task.id
        assert log_entry.operation_type == "download"
        assert log_entry.created_at is not None  # Timestamp
        
        # Log details should contain filename and output_format
        assert log_entry.details is not None
        assert "filename" in log_entry.details
        assert isinstance(log_entry.details["filename"], str)
        assert "desensitized" in log_entry.details["filename"]  # Should contain "desensitized"
        assert log_entry.details["filename"].endswith(f".{output_format}")
        
        assert "output_format" in log_entry.details
        assert log_entry.details["output_format"] == output_format
        
        # Timestamp should be in details
        assert "timestamp" in log_entry.details
        
    finally:
        db.close()
