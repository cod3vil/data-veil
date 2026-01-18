import pytest
from sqlalchemy import inspect
from app.models import Task, SensitiveItem, DesensitizationRule, OperationLog
from app.schemas import FileType, TaskStatus, DataType, StrategyType


def test_database_connection(test_engine):
    """Test that database connection is successful"""
    assert test_engine is not None
    connection = test_engine.connect()
    assert connection is not None
    connection.close()


def test_tables_created(test_engine):
    """Test that all required tables are created"""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    
    assert "tasks" in tables
    assert "sensitive_items" in tables
    assert "desensitization_rules" in tables
    assert "operation_logs" in tables


def test_task_table_structure(test_engine):
    """Test that tasks table has correct columns"""
    inspector = inspect(test_engine)
    columns = {col['name']: col for col in inspector.get_columns('tasks')}
    
    assert 'id' in columns
    assert 'filename' in columns
    assert 'file_size' in columns
    assert 'file_type' in columns
    assert 'upload_time' in columns
    assert 'status' in columns
    assert 'content' in columns
    assert 'file_metadata' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_sensitive_items_table_structure(test_engine):
    """Test that sensitive_items table has correct columns"""
    inspector = inspect(test_engine)
    columns = {col['name']: col for col in inspector.get_columns('sensitive_items')}
    
    assert 'id' in columns
    assert 'task_id' in columns
    assert 'type' in columns
    assert 'value' in columns
    assert 'start_pos' in columns
    assert 'end_pos' in columns
    assert 'confidence' in columns
    assert 'created_at' in columns


def test_desensitization_rules_table_structure(test_engine):
    """Test that desensitization_rules table has correct columns"""
    inspector = inspect(test_engine)
    columns = {col['name']: col for col in inspector.get_columns('desensitization_rules')}
    
    assert 'id' in columns
    assert 'name' in columns
    assert 'data_type' in columns
    assert 'strategy' in columns
    assert 'is_system' in columns
    assert 'enabled' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_operation_logs_table_structure(test_engine):
    """Test that operation_logs table has correct columns"""
    inspector = inspect(test_engine)
    columns = {col['name']: col for col in inspector.get_columns('operation_logs')}
    
    assert 'id' in columns
    assert 'task_id' in columns
    assert 'operation_type' in columns
    assert 'user_id' in columns
    assert 'details' in columns
    assert 'created_at' in columns


def test_create_task(test_db):
    """Test creating a task record"""
    task = Task(
        filename="test.pdf",
        file_size=1024,
        file_type=FileType.PDF.value,
        status=TaskStatus.UPLOADED.value
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    
    assert task.id is not None
    assert task.filename == "test.pdf"
    assert task.file_size == 1024
    assert task.file_type == FileType.PDF.value
    assert task.status == TaskStatus.UPLOADED.value


def test_create_sensitive_item(test_db):
    """Test creating a sensitive item record"""
    # First create a task
    task = Task(
        filename="test.pdf",
        file_size=1024,
        file_type=FileType.PDF.value,
        status=TaskStatus.UPLOADED.value
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    
    # Create sensitive item
    item = SensitiveItem(
        task_id=task.id,
        type=DataType.PHONE.value,
        value="13812345678",
        start_pos=0,
        end_pos=11,
        confidence=0.95
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    
    assert item.id is not None
    assert item.task_id == task.id
    assert item.type == DataType.PHONE.value
    assert item.value == "13812345678"


def test_create_desensitization_rule(test_db):
    """Test creating a desensitization rule record"""
    rule = DesensitizationRule(
        name="手机号脱敏",
        data_type=DataType.PHONE.value,
        strategy=StrategyType.MASK.value,
        is_system=True,
        enabled=True
    )
    test_db.add(rule)
    test_db.commit()
    test_db.refresh(rule)
    
    assert rule.id is not None
    assert rule.name == "手机号脱敏"
    assert rule.data_type == DataType.PHONE.value
    assert rule.strategy == StrategyType.MASK.value


def test_create_operation_log(test_db):
    """Test creating an operation log record"""
    log = OperationLog(
        operation_type="upload",
        user_id="test_user",
        details={"filename": "test.pdf"}
    )
    test_db.add(log)
    test_db.commit()
    test_db.refresh(log)
    
    assert log.id is not None
    assert log.operation_type == "upload"
    assert log.user_id == "test_user"
    assert log.details["filename"] == "test.pdf"
