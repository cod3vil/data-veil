"""
Desensitization Processor Module for applying desensitization rules to sensitive data.

This module provides functionality to:
1. Apply different desensitization strategies (mask, replace, delete)
2. Process documents with consistent desensitization (same value -> same result)
3. Handle different data types with appropriate strategies
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class DesensitizationRule:
    """Data model for desensitization rules"""
    id: str
    name: str
    data_type: str  # name, id_card, phone, address, bank_card, email
    strategy: str  # mask, replace, delete
    enabled: bool = True


class DesensitizationStrategy(ABC):
    """Abstract base class for desensitization strategies"""
    
    @abstractmethod
    def apply(self, value: str, data_type: str) -> str:
        """
        Apply the desensitization strategy to a value.
        
        Args:
            value: The sensitive value to desensitize
            data_type: The type of sensitive data (name, id_card, phone, etc.)
            
        Returns:
            The desensitized value
        """
        pass


class MaskStrategy(DesensitizationStrategy):
    """Strategy that masks sensitive data with asterisks"""
    
    def apply(self, value: str, data_type: str) -> str:
        """
        Apply masking based on data type.
        
        Different data types have different masking patterns:
        - name: Keep first character, mask rest (张三 → 张*)
        - id_card: Keep first 6 and last 4, mask middle (110101199001011234 → 110101********1234)
        - phone: Keep first 3 and last 4, mask middle (13812345678 → 138****5678)
        - address: Keep province and city, mask details
        - bank_card: Keep first 4 and last 4, mask middle
        - email: Keep domain, mask username
        
        Args:
            value: The sensitive value to mask
            data_type: The type of sensitive data
            
        Returns:
            The masked value
        """
        if not value:
            return value
        
        if data_type == 'name':
            # Keep first character, mask rest
            if len(value) <= 1:
                return value
            return value[0] + '*' * (len(value) - 1)
        
        elif data_type == 'id_card':
            # Keep first 6 and last 4 digits, mask middle 8
            if len(value) < 18:
                return value
            return value[:6] + '*' * 8 + value[-4:]
        
        elif data_type == 'phone':
            # Keep first 3 and last 4 digits, mask middle 4
            if len(value) < 11:
                return value
            return value[:3] + '****' + value[-4:]
        
        elif data_type == 'address':
            # Keep province and city, mask detailed address
            return self._mask_address(value)
        
        elif data_type == 'bank_card':
            # Keep first 4 and last 4 digits, mask middle
            if len(value) < 8:
                return value
            middle_length = len(value) - 8
            return value[:4] + '*' * middle_length + value[-4:]
        
        elif data_type == 'email':
            # Keep domain, mask username
            return self._mask_email(value)
        
        else:
            # Default: mask all but first and last character
            if len(value) <= 2:
                return '*' * len(value)
            return value[0] + '*' * (len(value) - 2) + value[-1]
    
    def _mask_address(self, address: str) -> str:
        """
        Mask address keeping province and city information.
        
        Examples:
        - 北京市朝阳区XX路10号 → 北京市朝阳区******
        - 上海市浦东新区世纪大道100号 → 上海市浦东新区******
        
        Args:
            address: The address to mask
            
        Returns:
            The masked address
        """
        # Common patterns for Chinese addresses
        # Try to find province/city pattern
        patterns = [
            r'(.*?[省市].*?[市区县])',  # Province + City/District
            r'(.*?[市区县])',  # City/District only
        ]
        
        for pattern in patterns:
            match = re.match(pattern, address)
            if match:
                prefix = match.group(1)
                return prefix + '******'
        
        # If no pattern matches, mask everything after first few characters
        if len(address) > 6:
            return address[:6] + '******'
        return '******'
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email keeping domain visible.
        
        Examples:
        - user@example.com → u***@example.com
        - longusername@domain.com → l***@domain.com
        
        Args:
            email: The email to mask
            
        Returns:
            The masked email
        """
        if '@' not in email:
            return email
        
        username, domain = email.split('@', 1)
        if len(username) <= 1:
            masked_username = '*'
        else:
            masked_username = username[0] + '***'
        
        return f"{masked_username}@{domain}"


class ReplaceStrategy(DesensitizationStrategy):
    """Strategy that replaces sensitive data with placeholder text"""
    
    # Placeholder mappings for different data types
    PLACEHOLDERS = {
        'name': '[姓名]',
        'id_card': '[身份证]',
        'phone': '[电话]',
        'address': '[地址]',
        'bank_card': '[银行卡]',
        'email': '[邮箱]',
    }
    
    def apply(self, value: str, data_type: str) -> str:
        """
        Replace sensitive data with appropriate placeholder.
        
        Args:
            value: The sensitive value to replace
            data_type: The type of sensitive data
            
        Returns:
            The placeholder text for this data type
        """
        return self.PLACEHOLDERS.get(data_type, '[敏感信息]')


class DeleteStrategy(DesensitizationStrategy):
    """Strategy that deletes sensitive data entirely"""
    
    def apply(self, value: str, data_type: str) -> str:
        """
        Delete sensitive data by returning empty string.
        
        Args:
            value: The sensitive value to delete
            data_type: The type of sensitive data
            
        Returns:
            Empty string
        """
        return ''



class DesensitizationProcessor:
    """Main processor for applying desensitization rules to text"""
    
    def __init__(self):
        """Initialize the desensitization processor with available strategies"""
        self.strategies: Dict[str, DesensitizationStrategy] = {
            'mask': MaskStrategy(),
            'replace': ReplaceStrategy(),
            'delete': DeleteStrategy(),
        }
    
    def _find_rule(
        self, 
        data_type: str, 
        rules: List[DesensitizationRule]
    ) -> Optional[DesensitizationRule]:
        """
        Find the appropriate rule for a given data type.
        
        Args:
            data_type: The type of sensitive data
            rules: List of available desensitization rules
            
        Returns:
            The matching rule if found and enabled, None otherwise
        """
        for rule in rules:
            if rule.data_type == data_type and rule.enabled:
                return rule
        return None
    
    def process(
        self, 
        text: str, 
        sensitive_items: List,  # List of SensitiveItem objects
        rules: List[DesensitizationRule]
    ) -> str:
        """
        Apply desensitization rules to text.
        
        This method ensures consistent desensitization: the same sensitive value
        is always replaced with the same desensitized value within a document.
        
        Args:
            text: The original text to desensitize
            sensitive_items: List of identified sensitive items
            rules: List of desensitization rules to apply
            
        Returns:
            The desensitized text
        """
        if not text or not sensitive_items:
            return text
        
        # Create value mapping for consistency
        # Same value should always map to same desensitized value
        value_mapping: Dict[str, str] = {}
        
        # Sort items by position in reverse order
        # This allows us to replace from end to start without position shifts
        sorted_items = sorted(
            sensitive_items, 
            key=lambda x: x.start_pos, 
            reverse=True
        )
        
        result = text
        
        for item in sorted_items:
            # Find the appropriate rule for this item's data type
            rule = self._find_rule(item.type, rules)
            
            if rule and rule.enabled:
                # Get the strategy for this rule
                strategy = self.strategies.get(rule.strategy)
                
                if strategy:
                    # Create a unique key for this value and type combination
                    cache_key = f"{item.type}:{item.value}"
                    
                    # Use cached value if exists, otherwise generate new one
                    if cache_key in value_mapping:
                        new_value = value_mapping[cache_key]
                    else:
                        new_value = strategy.apply(item.value, item.type)
                        value_mapping[cache_key] = new_value
                    
                    # Replace the sensitive value in the text
                    # Using reverse order ensures positions remain valid
                    result = (
                        result[:item.start_pos] + 
                        new_value + 
                        result[item.end_pos:]
                    )
        
        return result
