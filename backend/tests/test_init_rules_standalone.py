"""
Standalone test to verify the migration script can run independently.

This test verifies that the init_rules module can be imported and used
without requiring a running PostgreSQL instance.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.init_rules import init_preconfigured_rules, PRECONFIGURED_RULES, run_migration
from app.models import DesensitizationRule


def test_migration_script_with_sqlite():
    """
    Test that the migration script works with SQLite database.
    
    This simulates running the migration in a test environment.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Run the initialization
        init_preconfigured_rules(db)
        
        # Verify rules were created
        rules = db.query(DesensitizationRule).filter(
            DesensitizationRule.is_system == True
        ).all()
        
        assert len(rules) == len(PRECONFIGURED_RULES)
        
        # Verify all expected data types exist
        data_types = {rule.data_type for rule in rules}
        expected_types = {"name", "id_card", "phone", "address", "bank_card", "email"}
        assert data_types == expected_types
        
    finally:
        db.close()


def test_preconfigured_rules_constant():
    """
    Test that PRECONFIGURED_RULES constant has the expected structure.
    
    This ensures the migration data is properly defined.
    """
    # Verify we have rules defined
    assert len(PRECONFIGURED_RULES) > 0
    
    # Verify each rule has required fields
    required_fields = {"id", "name", "data_type", "strategy", "is_system", "enabled"}
    
    for rule in PRECONFIGURED_RULES:
        assert set(rule.keys()) == required_fields, \
            f"Rule {rule.get('name')} missing required fields"
        
        # Verify field types
        assert isinstance(rule["name"], str)
        assert isinstance(rule["data_type"], str)
        assert isinstance(rule["strategy"], str)
        assert isinstance(rule["is_system"], bool)
        assert isinstance(rule["enabled"], bool)
        
        # Verify values
        assert rule["is_system"] == True
        assert rule["enabled"] == True
        assert rule["strategy"] in ["mask", "replace", "delete"]


def test_all_required_data_types_in_preconfigured_rules():
    """
    Test that PRECONFIGURED_RULES includes all required data types.
    
    Validates Requirement 4.1: Pre-configured rules for names, ID cards,
    phone numbers, addresses, bank cards, and emails.
    """
    data_types = {rule["data_type"] for rule in PRECONFIGURED_RULES}
    
    required_types = {
        "name",
        "id_card",
        "phone",
        "address",
        "bank_card",
        "email"
    }
    
    assert data_types == required_types, \
        f"Missing required data types: {required_types - data_types}"
