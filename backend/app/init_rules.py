"""
Database initialization script for pre-configured desensitization rules.

This script inserts the default desensitization rules into the database
according to Requirement 4.1.
"""
from sqlalchemy.orm import Session
from app.models import DesensitizationRule
from app.database import SessionLocal, engine, Base
from app.logging_config import get_logger
import uuid

logger = get_logger(__name__)


# Pre-configured desensitization rules
# Requirements: 4.1 - Pre-configured rules for common sensitive data types
PRECONFIGURED_RULES = [
    {
        "id": "rule-name-mask",
        "name": "姓名脱敏（掩码）",
        "data_type": "name",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
    {
        "id": "rule-id-card-mask",
        "name": "身份证脱敏（掩码）",
        "data_type": "id_card",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
    {
        "id": "rule-phone-mask",
        "name": "手机号脱敏（掩码）",
        "data_type": "phone",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
    {
        "id": "rule-address-mask",
        "name": "地址脱敏（掩码）",
        "data_type": "address",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
    {
        "id": "rule-bank-card-mask",
        "name": "银行卡脱敏（掩码）",
        "data_type": "bank_card",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
    {
        "id": "rule-email-mask",
        "name": "邮箱脱敏（掩码）",
        "data_type": "email",
        "strategy": "mask",
        "is_system": True,
        "enabled": True,
    },
]


def init_preconfigured_rules(db: Session) -> None:
    """
    Initialize pre-configured desensitization rules in the database.
    
    This function checks if rules already exist and only inserts missing ones.
    It's idempotent and safe to run multiple times.
    
    Args:
        db: Database session
    """
    logger.info("Initializing pre-configured desensitization rules")
    
    # Check existing rules
    existing_rules = db.query(DesensitizationRule).filter(
        DesensitizationRule.is_system == True
    ).all()
    
    existing_data_types = {rule.data_type for rule in existing_rules}
    
    # Insert missing rules
    inserted_count = 0
    for rule_data in PRECONFIGURED_RULES:
        if rule_data["data_type"] not in existing_data_types:
            rule = DesensitizationRule(
                name=rule_data["name"],
                data_type=rule_data["data_type"],
                strategy=rule_data["strategy"],
                is_system=rule_data["is_system"],
                enabled=rule_data["enabled"],
            )
            db.add(rule)
            inserted_count += 1
            logger.info(
                "Inserted rule",
                rule_name=rule_data["name"],
                data_type=rule_data["data_type"]
            )
    
    if inserted_count > 0:
        db.commit()
        logger.info(f"Successfully inserted {inserted_count} pre-configured rules")
    else:
        logger.info("All pre-configured rules already exist, skipping insertion")


def run_migration():
    """
    Run the migration to initialize pre-configured rules.
    
    This function can be called directly or imported and used in the application
    startup process.
    """
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create session and initialize rules
    db = SessionLocal()
    try:
        init_preconfigured_rules(db)
    except Exception as e:
        logger.error(f"Failed to initialize rules: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    """
    Run this script directly to initialize pre-configured rules:
    python -m app.init_rules
    """
    from app.logging_config import configure_logging
    configure_logging(log_level="INFO", json_logs=False)
    
    logger.info("Starting rule initialization migration")
    run_migration()
    logger.info("Migration completed successfully")
