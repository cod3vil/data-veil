"""
Property-based tests for the Desensitization Processor.

These tests verify universal properties that should hold across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from app.desensitization_processor import (
    MaskStrategy, 
    ReplaceStrategy, 
    DeleteStrategy,
    DesensitizationProcessor,
    DesensitizationRule
)
from app.recognition_engine import SensitiveItem


# Feature: data-desensitization-platform, Property 10: Masking Strategy Application
@given(
    name=st.text(
        alphabet=st.characters(
            whitelist_categories=('Lo',),  # Chinese characters
            min_codepoint=0x4E00,
            max_codepoint=0x9FFF
        ),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=100)
def test_mask_strategy_name(name):
    """
    Property 10: Masking Strategy Application
    
    For any name, when masking strategy is applied,
    the result should keep the first character and mask the rest with asterisks.
    
    Validates: Requirements 4.2, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    strategy = MaskStrategy()
    result = strategy.apply(name, 'name')
    
    # Should keep first character
    assert result[0] == name[0], f"First character should be preserved: expected {name[0]}, got {result[0]}"
    
    # Rest should be asterisks
    assert result[1:] == '*' * (len(name) - 1), \
        f"Rest should be masked: expected {'*' * (len(name) - 1)}, got {result[1:]}"
    
    # Length should be preserved
    assert len(result) == len(name), f"Length should be preserved: expected {len(name)}, got {len(result)}"


@given(
    id_card=st.from_regex(r'\d{17}[\dXx]', fullmatch=True)
)
@settings(max_examples=100)
def test_mask_strategy_id_card(id_card):
    """
    Property 10: Masking Strategy Application
    
    For any ID card number, when masking strategy is applied,
    the result should keep first 6 and last 4 digits, masking middle 8 with asterisks.
    
    Validates: Requirements 4.2, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    strategy = MaskStrategy()
    result = strategy.apply(id_card, 'id_card')
    
    # Should keep first 6 digits
    assert result[:6] == id_card[:6], f"First 6 digits should be preserved"
    
    # Middle 8 should be asterisks
    assert result[6:14] == '********', f"Middle 8 should be masked"
    
    # Should keep last 4 characters
    assert result[14:] == id_card[14:], f"Last 4 characters should be preserved"
    
    # Length should be 18
    assert len(result) == 18, f"Length should be 18"


@given(
    phone=st.from_regex(r'1[3-9]\d{9}', fullmatch=True)
)
@settings(max_examples=100)
def test_mask_strategy_phone(phone):
    """
    Property 10: Masking Strategy Application
    
    For any phone number, when masking strategy is applied,
    the result should keep first 3 and last 4 digits, masking middle 4 with asterisks.
    
    Validates: Requirements 4.2, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    strategy = MaskStrategy()
    result = strategy.apply(phone, 'phone')
    
    # Should keep first 3 digits
    assert result[:3] == phone[:3], f"First 3 digits should be preserved"
    
    # Middle 4 should be asterisks
    assert result[3:7] == '****', f"Middle 4 should be masked"
    
    # Should keep last 4 digits
    assert result[7:] == phone[7:], f"Last 4 digits should be preserved"
    
    # Length should be 11
    assert len(result) == 11, f"Length should be 11"


@given(
    bank_card=st.from_regex(r'\d{16,19}', fullmatch=True)
)
@settings(max_examples=100)
def test_mask_strategy_bank_card(bank_card):
    """
    Property 10: Masking Strategy Application
    
    For any bank card number, when masking strategy is applied,
    the result should keep first 4 and last 4 digits, masking middle with asterisks.
    
    Validates: Requirements 4.2, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    strategy = MaskStrategy()
    result = strategy.apply(bank_card, 'bank_card')
    
    # Should keep first 4 digits
    assert result[:4] == bank_card[:4], f"First 4 digits should be preserved"
    
    # Should keep last 4 digits
    assert result[-4:] == bank_card[-4:], f"Last 4 digits should be preserved"
    
    # Middle should be asterisks
    middle_length = len(bank_card) - 8
    assert result[4:-4] == '*' * middle_length, f"Middle should be masked"
    
    # Length should be preserved
    assert len(result) == len(bank_card), f"Length should be preserved"


@given(
    local_part=st.from_regex(r'[a-zA-Z0-9._%+-]+', fullmatch=True).filter(lambda x: 1 <= len(x) <= 20),
    domain=st.from_regex(r'[a-zA-Z0-9.-]+', fullmatch=True).filter(lambda x: 1 <= len(x) <= 20),
    tld=st.from_regex(r'[a-zA-Z]{2,}', fullmatch=True).filter(lambda x: 2 <= len(x) <= 10)
)
@settings(max_examples=100)
def test_mask_strategy_email(local_part, domain, tld):
    """
    Property 10: Masking Strategy Application
    
    For any email address, when masking strategy is applied,
    the result should keep the domain visible and mask the username.
    
    Validates: Requirements 4.2, 4.5, 4.6, 4.7, 4.8, 4.9
    """
    email = f"{local_part}@{domain}.{tld}"
    strategy = MaskStrategy()
    result = strategy.apply(email, 'email')
    
    # Should contain @ symbol
    assert '@' in result, f"Result should contain @ symbol"
    
    # Domain should be preserved
    assert f"@{domain}.{tld}" in result, f"Domain should be preserved"
    
    # Username should be masked
    masked_username = result.split('@')[0]
    if len(local_part) <= 1:
        # Single character username becomes just '*'
        assert masked_username == '*', f"Single char username should be masked to *"
    else:
        # Multi-character username: first char + ***
        assert masked_username[0] == local_part[0], f"First character of username should be preserved"
        assert '***' in masked_username, f"Username should contain ***"


# Feature: data-desensitization-platform, Property 11: Replacement Strategy Application
@given(
    value=st.text(min_size=1, max_size=100),
    data_type=st.sampled_from(['name', 'id_card', 'phone', 'address', 'bank_card', 'email'])
)
@settings(max_examples=100)
def test_replace_strategy(value, data_type):
    """
    Property 11: Replacement Strategy Application
    
    For any sensitive data value and its corresponding data type,
    when replacement strategy is applied, the result should be
    the appropriate placeholder text for that data type.
    
    Validates: Requirements 4.3
    """
    strategy = ReplaceStrategy()
    result = strategy.apply(value, data_type)
    
    # Expected placeholders
    expected_placeholders = {
        'name': '[姓名]',
        'id_card': '[身份证]',
        'phone': '[电话]',
        'address': '[地址]',
        'bank_card': '[银行卡]',
        'email': '[邮箱]',
    }
    
    # Result should be the expected placeholder
    assert result == expected_placeholders[data_type], \
        f"Expected placeholder {expected_placeholders[data_type]}, got {result}"
    
    # Result should not contain the original value (unless it's a substring of the placeholder)
    # Note: We skip this check if the original value is very short (1-2 chars) as it might
    # coincidentally appear in the placeholder (e.g., '[' in '[姓名]')
    if len(value) > 2:
        assert value not in result, f"Result should not contain original value"


# Feature: data-desensitization-platform, Property 12: Deletion Strategy Application
@given(
    value=st.text(min_size=1, max_size=100),
    data_type=st.sampled_from(['name', 'id_card', 'phone', 'address', 'bank_card', 'email'])
)
@settings(max_examples=100)
def test_delete_strategy(value, data_type):
    """
    Property 12: Deletion Strategy Application
    
    For any sensitive data value, when deletion strategy is applied,
    the result should be an empty string.
    
    Validates: Requirements 4.4
    """
    strategy = DeleteStrategy()
    result = strategy.apply(value, data_type)
    
    # Result should be empty string
    assert result == '', f"Expected empty string, got '{result}'"
    
    # Result should not contain the original value
    assert value not in result, f"Result should not contain original value"


# Feature: data-desensitization-platform, Property 13: Complete Rule Application
@given(
    phone=st.from_regex(r'1[3-9]\d{9}', fullmatch=True),
    id_card=st.from_regex(r'\d{17}[\dXx]', fullmatch=True),
    text_before=st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
        min_size=0,
        max_size=50
    ),
    text_middle=st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
        min_size=1,
        max_size=50
    ),
    text_after=st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
        min_size=0,
        max_size=50
    )
)
@settings(max_examples=100)
def test_complete_rule_application(phone, id_card, text_before, text_middle, text_after):
    """
    Property 13: Complete Rule Application
    
    For any text with identified sensitive items and selected desensitization rules,
    when desensitization is performed, all sensitive items matching enabled rules
    should be desensitized.
    
    Validates: Requirements 5.1
    """
    # Ensure phone and id_card don't appear in surrounding text
    assume(phone not in text_before)
    assume(phone not in text_middle)
    assume(phone not in text_after)
    assume(id_card not in text_before)
    assume(id_card not in text_middle)
    assume(id_card not in text_after)
    
    # Create text with known sensitive data
    text = f"{text_before}{phone}{text_middle}{id_card}{text_after}"
    
    # Create sensitive items
    phone_start = len(text_before)
    phone_end = phone_start + len(phone)
    id_card_start = phone_end + len(text_middle)
    id_card_end = id_card_start + len(id_card)
    
    sensitive_items = [
        SensitiveItem(
            type='phone',
            value=phone,
            start_pos=phone_start,
            end_pos=phone_end,
            confidence=1.0
        ),
        SensitiveItem(
            type='id_card',
            value=id_card,
            start_pos=id_card_start,
            end_pos=id_card_end,
            confidence=1.0
        )
    ]
    
    # Create rules (both enabled with mask strategy)
    rules = [
        DesensitizationRule(
            id='rule1',
            name='手机号脱敏',
            data_type='phone',
            strategy='mask',
            enabled=True
        ),
        DesensitizationRule(
            id='rule2',
            name='身份证脱敏',
            data_type='id_card',
            strategy='mask',
            enabled=True
        )
    ]
    
    # Process the text
    processor = DesensitizationProcessor()
    result = processor.process(text, sensitive_items, rules)
    
    # Original sensitive values should not appear in result
    assert phone not in result, f"Original phone number should not appear in result"
    assert id_card not in result, f"Original ID card should not appear in result"
    
    # Masked values should appear
    masked_phone = phone[:3] + '****' + phone[-4:]
    masked_id_card = id_card[:6] + '********' + id_card[-4:]
    
    assert masked_phone in result, f"Masked phone should appear in result"
    assert masked_id_card in result, f"Masked ID card should appear in result"
    
    # Surrounding text should be preserved
    assert text_before in result, f"Text before should be preserved"
    assert text_middle in result, f"Text middle should be preserved"
    assert text_after in result, f"Text after should be preserved"


# Feature: data-desensitization-platform, Property 15: Consistent Value Desensitization
@given(
    phone=st.from_regex(r'1[3-9]\d{9}', fullmatch=True),
    text_parts=st.lists(
        st.text(
            alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
            min_size=1,
            max_size=20
        ),
        min_size=3,
        max_size=5
    )
)
@settings(max_examples=100)
def test_consistent_value_desensitization(phone, text_parts):
    """
    Property 15: Consistent Value Desensitization
    
    For any text containing multiple occurrences of the same sensitive value,
    when desensitization is applied, all occurrences should be replaced
    with the same desensitized value.
    
    Validates: Requirements 5.5
    """
    # Ensure phone doesn't appear in text parts
    for part in text_parts:
        assume(phone not in part)
    
    # Create text with multiple occurrences of the same phone number
    # Insert phone between each text part
    text = text_parts[0]
    positions = []
    
    for i in range(1, len(text_parts)):
        start_pos = len(text)
        text += phone
        end_pos = len(text)
        positions.append((start_pos, end_pos))
        text += text_parts[i]
    
    # Create sensitive items for each occurrence
    sensitive_items = [
        SensitiveItem(
            type='phone',
            value=phone,
            start_pos=start,
            end_pos=end,
            confidence=1.0
        )
        for start, end in positions
    ]
    
    # Create rule
    rules = [
        DesensitizationRule(
            id='rule1',
            name='手机号脱敏',
            data_type='phone',
            strategy='mask',
            enabled=True
        )
    ]
    
    # Process the text
    processor = DesensitizationProcessor()
    result = processor.process(text, sensitive_items, rules)
    
    # Original phone should not appear in result
    assert phone not in result, f"Original phone number should not appear in result"
    
    # Expected masked value
    masked_phone = phone[:3] + '****' + phone[-4:]
    
    # Count occurrences of masked phone in result
    masked_count = result.count(masked_phone)
    
    # Should have same number of masked occurrences as original occurrences
    assert masked_count == len(positions), \
        f"Expected {len(positions)} occurrences of masked phone, found {masked_count}"
    
    # All occurrences should be identical (consistency check)
    # Find all masked phone positions in result
    masked_positions = []
    start = 0
    while True:
        pos = result.find(masked_phone, start)
        if pos == -1:
            break
        masked_positions.append(pos)
        start = pos + 1
    
    # All found masked values should be identical
    for pos in masked_positions:
        found_value = result[pos:pos + len(masked_phone)]
        assert found_value == masked_phone, \
            f"All masked values should be identical: expected {masked_phone}, found {found_value}"


# Test with disabled rules
@given(
    phone=st.from_regex(r'1[3-9]\d{9}', fullmatch=True),
    text_before=st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
        min_size=0,
        max_size=50
    ),
    text_after=st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Nd')),
        min_size=0,
        max_size=50
    )
)
@settings(max_examples=100)
def test_disabled_rule_not_applied(phone, text_before, text_after):
    """
    Property 13: Complete Rule Application
    
    For any text with identified sensitive items, when a rule is disabled,
    the corresponding sensitive items should NOT be desensitized.
    
    Validates: Requirements 5.1
    """
    assume(phone not in text_before)
    assume(phone not in text_after)
    
    text = f"{text_before}{phone}{text_after}"
    
    # Create sensitive item
    phone_start = len(text_before)
    phone_end = phone_start + len(phone)
    
    sensitive_items = [
        SensitiveItem(
            type='phone',
            value=phone,
            start_pos=phone_start,
            end_pos=phone_end,
            confidence=1.0
        )
    ]
    
    # Create rule but DISABLED
    rules = [
        DesensitizationRule(
            id='rule1',
            name='手机号脱敏',
            data_type='phone',
            strategy='mask',
            enabled=False  # Disabled!
        )
    ]
    
    # Process the text
    processor = DesensitizationProcessor()
    result = processor.process(text, sensitive_items, rules)
    
    # Original text should be unchanged (rule was disabled)
    assert result == text, f"Text should be unchanged when rule is disabled"
    assert phone in result, f"Original phone should still appear when rule is disabled"
