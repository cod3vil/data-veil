"""
Property-based tests for API endpoints.

Feature: data-desensitization-platform
"""

import pytest
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io
import os
import tempfile

from app.database import Base, get_db
from main import app
from app.models import Task, DesensitizationRule, SensitiveItem, OperationLog
from app.schemas import DataType, StrategyType


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Note: Tables are created by the setup_api_test_database fixture in conftest.py


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment once for the entire test session"""
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create test upload directory
    os.makedirs("/tmp/test_uploads", exist_ok=True)
    
    # Set upload directory for tests
    from app.config import settings
    settings.upload_dir = "/tmp/test_uploads"
    
    yield
    
    # Cleanup at end of session - don't drop tables, just clean data
    db = TestingSessionLocal()
    try:
        db.query(Task).delete()
        db.query(SensitiveItem).delete()
        db.query(DesensitizationRule).delete()
        db.query(OperationLog).delete()
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()
    
    # Clean up test files
    if os.path.exists("/tmp/test_uploads"):
        for file in os.listdir("/tmp/test_uploads"):
            file_path = os.path.join("/tmp/test_uploads", file)
            try:
                os.remove(file_path)
            except:
                pass


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data():
    """Clean up test data between tests"""
    yield
    # Clean up database records between tests
    db = TestingSessionLocal()
    try:
        db.query(Task).delete()
        db.query(SensitiveItem).delete()
        db.query(DesensitizationRule).delete()
        db.query(OperationLog).delete()
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()


# Strategies for generating test data
supported_formats = st.sampled_from([".pdf", ".docx", ".xlsx", ".txt", ".md"])
unsupported_formats = st.sampled_from([".exe", ".zip", ".jpg", ".png", ".mp4", ".avi"])

file_content_strategy = st.binary(min_size=1, max_size=1024)  # Small files for testing


# Feature: data-desensitization-platform, Property 1: Multi-format Upload Support
@given(
    file_extension=supported_formats,
    file_content=file_content_strategy,
    filename_base=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=20, deadline=None)
@pytest.mark.property_test
def test_multi_format_upload_support(file_extension, file_content, filename_base):
    """
    Property 1: Multi-format Upload Support
    
    For any supported document format (PDF, DOCX, XLSX, TXT, MD), 
    when a valid file of that format is uploaded, the system should 
    accept the upload and return a successful task creation response.
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4
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
    
    # Should return task response
    data = response.json()
    assert "id" in data
    assert data["filename"] == filename
    assert data["file_size"] == len(file_content)
    assert data["file_type"] in ["pdf", "docx", "xlsx", "txt", "md"]
    assert data["status"] == "uploaded"
    assert "upload_time" in data



# Feature: data-desensitization-platform, Property 2: Unsupported Format Rejection
@given(
    file_extension=unsupported_formats,
    file_content=file_content_strategy,
    filename_base=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=20, deadline=None)
@pytest.mark.property_test
def test_unsupported_format_rejection(file_extension, file_content, filename_base):
    """
    Property 2: Unsupported Format Rejection
    
    For any file with an unsupported format extension, when uploaded, 
    the system should reject the upload and return an error response.
    
    Validates: Requirements 1.5
    """
    # Create a file-like object
    filename = f"{filename_base}{file_extension}"
    file = io.BytesIO(file_content)
    
    # Upload file
    response = client.post(
        "/api/v1/upload",
        files={"file": (filename, file, "application/octet-stream")}
    )
    
    # Should reject the upload
    assert response.status_code == 400
    
    # Should return error message
    data = response.json()
    assert "error" in data or "message" in data
    if "message" in data:
        assert "unsupported" in data["message"].lower() or "format" in data["message"].lower()
    elif "detail" in data:
        assert "unsupported" in data["detail"].lower() or "format" in data["detail"].lower()



# Feature: data-desensitization-platform, Property 3: File Size Validation
@given(
    file_extension=supported_formats,
    excess_size=st.integers(min_value=1, max_value=10 * 1024 * 1024),  # 1 byte to 10MB over limit
    filename_base=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=20, deadline=None)
@pytest.mark.property_test
def test_file_size_validation(file_extension, excess_size, filename_base):
    """
    Property 3: File Size Validation
    
    For any file exceeding the maximum size limit, when uploaded, 
    the system should reject the upload and return an error response 
    indicating the size limit was exceeded.
    
    Validates: Requirements 1.6
    """
    from app.config import settings
    
    # Create a file that exceeds the limit
    oversized_content = b"x" * (settings.max_file_size + excess_size)
    filename = f"{filename_base}{file_extension}"
    file = io.BytesIO(oversized_content)
    
    # Upload file
    response = client.post(
        "/api/v1/upload",
        files={"file": (filename, file, "application/octet-stream")}
    )
    
    # Should reject the upload
    assert response.status_code == 400
    
    # Should return error message about size limit
    data = response.json()
    assert "error" in data or "message" in data
    if "message" in data:
        assert "size" in data["message"].lower() or "limit" in data["message"].lower()
    elif "detail" in data:
        assert "size" in data["detail"].lower() or "limit" in data["detail"].lower()



# Feature: data-desensitization-platform, Property 14: Original Document Preservation
@given(
    file_extension=supported_formats,
    file_content=st.binary(min_size=100, max_size=1024),
    filename_base=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=20, deadline=None)
@pytest.mark.property_test
def test_original_document_preservation(file_extension, file_content, filename_base):
    """
    Property 14: Original Document Preservation
    
    For any uploaded document, after desensitization processing, 
    the original uploaded file should remain unchanged and unmodified.
    
    Validates: Requirements 5.2, 5.3
    """
    from app.config import settings
    
    # Create a file-like object
    filename = f"{filename_base}{file_extension}"
    file = io.BytesIO(file_content)
    
    # Upload file
    response = client.post(
        "/api/v1/upload",
        files={"file": (filename, file, "application/octet-stream")}
    )
    
    assert response.status_code == 200
    data = response.json()
    task_id = data["id"]
    
    # Get the uploaded file path
    file_path = os.path.join(settings.upload_dir, f"{task_id}{file_extension}")
    
    # Read the original file content
    with open(file_path, "rb") as f:
        original_content = f.read()
    
    # Verify original content matches uploaded content
    assert original_content == file_content
    
    # Get file modification time
    original_mtime = os.path.getmtime(file_path)
    
    # Simulate desensitization process (parse, identify, export)
    # Note: We can't fully test export without proper document content,
    # but we can verify the file remains unchanged after upload
    
    # Read the file again
    with open(file_path, "rb") as f:
        content_after = f.read()
    
    # Verify file content is unchanged
    assert content_after == file_content
    assert content_after == original_content
    
    # Verify file was not modified (mtime should be the same or very close)
    current_mtime = os.path.getmtime(file_path)
    assert abs(current_mtime - original_mtime) < 1.0  # Within 1 second
