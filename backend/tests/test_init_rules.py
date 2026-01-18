"""
Tests for pre-configured desensitization rules initialization.

Validates Requirement 4.1: Pre-configured rules for common sensitive data types
"""
import pytest
from app.models import DesensitizationRule
from app.init_rules import init_preconfigured_rules, PRECONFIGURED_RULES


def test_preconfigured_rules_exist(test_db):
    """
    Test that all expected pre-configured rules are created in the database.
    
    Validates Requirement 4.1: The system SHALL provide pre-configured 
    desensitization rules for common sensitive data types including names, 
    ID cards, phone numbers, addresses, and bank cards.
    """
    # Initialize the pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query all system rules
    rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    # Verify we have the expected number of rules
    assert len(rules) == len(PRECONFIGURED_RULES), \
        f"Expected {len(PRECONFIGURED_RULES)} rules, found {len(rules)}"
    
    # Verify all expected data types are present
    expected_data_types = {
        "name",
        "id_card",
        "phone",
        "address",
        "bank_card",
        "email"
    }
    
    actual_data_types = {rule.data_type for rule in rules}
    
    assert actual_data_types == expected_data_types, \
        f"Missing data types: {expected_data_types - actual_data_types}"


def test_preconfigured_rules_properties(test_db):
    """
    Test that pre-configured rules have correct properties.
    
    Validates that each rule:
    - Has a name
    - Has a data type
    - Has a strategy (mask, replace, or delete)
    - Is marked as system rule
    - Is enabled by default
    """
    # Initialize the pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query all system rules
    rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    for rule in rules:
        # Verify rule has a name
        assert rule.name, f"Rule for {rule.data_type} has no name"
        
        # Verify rule has a data type
        assert rule.data_type in ["name", "id_card", "phone", "address", "bank_card", "email"], \
            f"Invalid data type: {rule.data_type}"
        
        # Verify rule has a valid strategy
        assert rule.strategy in ["mask", "replace", "delete"], \
            f"Invalid strategy: {rule.strategy}"
        
        # Verify rule is marked as system rule
        assert rule.is_system == True, \
            f"Rule {rule.name} is not marked as system rule"
        
        # Verify rule is enabled by default
        assert rule.enabled == True, \
            f"Rule {rule.name} is not enabled by default"


def test_preconfigured_rules_idempotent(test_db):
    """
    Test that initializing rules multiple times is idempotent.
    
    Running the initialization multiple times should not create duplicate rules.
    """
    # Initialize rules first time
    init_preconfigured_rules(test_db)
    
    # Count rules after first initialization
    first_count = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).count()
    
    # Initialize rules second time
    init_preconfigured_rules(test_db)
    
    # Count rules after second initialization
    second_count = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).count()
    
    # Verify count is the same
    assert first_count == second_count, \
        "Initializing rules multiple times created duplicates"
    
    # Verify we still have the expected number
    assert first_count == len(PRECONFIGURED_RULES), \
        f"Expected {len(PRECONFIGURED_RULES)} rules, found {first_count}"


def test_each_data_type_has_rule(test_db):
    """
    Test that each required data type has at least one rule.
    
    Validates Requirement 4.1: Pre-configured rules for:
    - names
    - ID cards
    - phone numbers
    - addresses
    - bank cards
    - emails
    """
    # Initialize the pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Required data types from Requirement 4.1
    required_data_types = [
        "name",
        "id_card",
        "phone",
        "address",
        "bank_card",
        "email"
    ]
    
    for data_type in required_data_types:
        rule = test_db.query(DesensitizationRule).filter(
            DesensitizationRule.data_type == data_type,
            DesensitizationRule.is_system == True
        ).first()
        
        assert rule is not None, \
            f"No pre-configured rule found for data type: {data_type}"
        
        assert rule.enabled == True, \
            f"Pre-configured rule for {data_type} is not enabled"


def test_default_strategy_is_mask(test_db):
    """
    Test that all pre-configured rules use masking strategy by default.
    
    This ensures consistent behavior across all rule types.
    """
    # Initialize the pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query all system rules
    rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    for rule in rules:
        assert rule.strategy == "mask", \
            f"Rule {rule.name} does not use mask strategy (uses {rule.strategy})"


def test_rule_names_are_descriptive(test_db):
    """
    Test that rule names are descriptive and in Chinese.
    
    This ensures the UI can display meaningful names to users.
    """
    # Initialize the pre-configured rules
    init_preconfigured_rules(test_db)
    
    # Query all system rules
    rules = test_db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    for rule in rules:
        # Verify name is not empty
        assert len(rule.name) > 0, f"Rule for {rule.data_type} has empty name"
        
        # Verify name contains Chinese characters (basic check)
        # Chinese characters are in the Unicode range \u4e00-\u9fff
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in rule.name)
        assert has_chinese, \
            f"Rule name '{rule.name}' does not contain Chinese characters"
