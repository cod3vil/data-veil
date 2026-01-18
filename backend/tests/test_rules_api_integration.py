"""
Integration test to verify the rules API endpoint works with initialized rules.

This test ensures that the /api/v1/rules endpoint returns the pre-configured
rules after they are initialized.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.init_rules import init_preconfigured_rules
from app.models import DesensitizationRule


def test_rules_api_returns_initialized_rules(test_db):
    """
    Test that querying rules from database returns all pre-configured rules.
    
    This simulates what the GET /api/v1/rules endpoint does.
    """
    # Initialize pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query rules (simulating the API endpoint)
    rules = test_db.query(DesensitizationRule).all()
    
    # Verify we have rules
    assert len(rules) >= 6, "Should have at least 6 pre-configured rules"
    
    # Verify all required data types are present
    data_types = {rule.data_type for rule in rules}
    required_types = {"name", "id_card", "phone", "address", "bank_card", "email"}
    
    assert required_types.issubset(data_types), \
        f"Missing required data types: {required_types - data_types}"
    
    # Verify rules have all required fields for API response
    for rule in rules:
        assert rule.id is not None
        assert rule.name is not None
        assert rule.data_type is not None
        assert rule.strategy is not None
        assert rule.enabled is not None


def test_enabled_rules_can_be_filtered(test_db):
    """
    Test that enabled rules can be filtered from the database.
    
    This is useful for the API to return only active rules.
    """
    # Initialize pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query only enabled rules
    enabled_rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.enabled == True
    ).all()
    
    # All pre-configured rules should be enabled by default
    assert len(enabled_rules) >= 6
    
    # Verify all are actually enabled
    for rule in enabled_rules:
        assert rule.enabled == True


def test_system_rules_can_be_distinguished(test_db):
    """
    Test that system rules can be distinguished from user-created rules.
    
    This ensures the API can differentiate between pre-configured and custom rules.
    """
    # Initialize pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query system rules
    system_rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    # All pre-configured rules should be system rules
    assert len(system_rules) >= 6
    
    # Verify all are marked as system
    for rule in system_rules:
        assert rule.is_system == True
