"""
Recognition Engine Module for identifying sensitive information in documents.

This module provides functionality to identify sensitive data using:
1. Regular expressions for structured data (phone, ID card, email, bank card)
2. NLP models for unstructured data (names, addresses)
"""

import re
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from app.logging_config import get_logger
from app.exceptions import RecognitionError

logger = get_logger(__name__)


@dataclass
class SensitiveItem:
    """Data model for identified sensitive information"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # name, id_card, phone, address, bank_card, email
    value: str = ""
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate the sensitive item after initialization"""
        if self.end_pos < self.start_pos:
            raise ValueError(f"end_pos ({self.end_pos}) must be >= start_pos ({self.start_pos})")


# Regex patterns for structured sensitive data
# Order matters: more specific patterns should be checked first
REGEX_PATTERNS = {
    'id_card': r'\d{17}[\dXx]',  # Check ID card first (18 chars)
    'bank_card': r'\d{16,19}',   # Then bank card (16-19 chars)
    'phone': r'1[3-9]\d{9}',     # Phone (11 chars starting with 1[3-9])
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # More robust email pattern
}


class RecognitionEngine:
    """Engine for identifying sensitive information in text"""
    
    def __init__(self):
        """Initialize the recognition engine"""
        self.regex_patterns = REGEX_PATTERNS
        self.nlp_model = None
    
    def _regex_recognition(self, text: str) -> List[SensitiveItem]:
        """
        Use regex patterns to identify structured sensitive data.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of identified sensitive items
        """
        items = []
        matched_positions = set()  # Track matched positions to avoid overlaps
        
        # Process patterns in order (more specific first)
        for data_type, pattern in self.regex_patterns.items():
            # Find all matches for this pattern
            for match in re.finditer(pattern, text):
                start, end = match.start(), match.end()
                
                # Check if this position overlaps with already matched positions
                overlaps = any(
                    pos in matched_positions 
                    for pos in range(start, end)
                )
                
                if not overlaps:
                    item = SensitiveItem(
                        type=data_type,
                        value=match.group(),
                        start_pos=start,
                        end_pos=end,
                        confidence=1.0  # Regex matches have 100% confidence
                    )
                    items.append(item)
                    
                    # Mark these positions as matched
                    for pos in range(start, end):
                        matched_positions.add(pos)
        
        return items
    
    def _load_nlp_model(self):
        """
        Load the NLP model for entity recognition.
        Uses spaCy with Chinese model (zh_core_web_sm).
        """
        if self.nlp_model is None:
            try:
                import spacy
                logger.info("loading_nlp_model", model="zh_core_web_sm")
                self.nlp_model = spacy.load("zh_core_web_sm")
                logger.info("nlp_model_loaded", model="zh_core_web_sm")
            except OSError as e:
                logger.warning("nlp_model_not_found", model="zh_core_web_sm", error=str(e))
                # Model not found, try to download it
                import subprocess
                logger.info("downloading_nlp_model", model="zh_core_web_sm")
                subprocess.run(["python", "-m", "spacy", "download", "zh_core_web_sm"], check=True)
                import spacy
                self.nlp_model = spacy.load("zh_core_web_sm")
                logger.info("nlp_model_downloaded_and_loaded", model="zh_core_web_sm")
            except Exception as e:
                logger.error("nlp_model_load_failed", model="zh_core_web_sm", error=str(e))
                raise RecognitionError(
                    message=f"Failed to load NLP model: {str(e)}",
                    error_code="NLP_MODEL_LOAD_FAILED",
                    details={"model": "zh_core_web_sm", "error": str(e)}
                )
        return self.nlp_model
    
    def _nlp_recognition(self, text: str) -> List[SensitiveItem]:
        """
        Use NLP model to identify unstructured sensitive data (names, addresses).
        
        Args:
            text: The text to analyze
            
        Returns:
            List of identified sensitive items
        """
        items = []
        
        # Load NLP model if not already loaded
        nlp = self._load_nlp_model()
        
        # Process the text
        doc = nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            # Map spaCy entity types to our data types
            if ent.label_ == "PERSON":
                data_type = "name"
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                # GPE: Geopolitical entity, LOC: Location, FAC: Facility
                data_type = "address"
            else:
                # Skip other entity types
                continue
            
            item = SensitiveItem(
                type=data_type,
                value=ent.text,
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                confidence=0.8  # NLP matches have lower confidence
            )
            items.append(item)
        
        return items
    
    def _deduplicate(self, items: List[SensitiveItem]) -> List[SensitiveItem]:
        """
        Remove duplicate sensitive items based on position overlap.
        
        When multiple items overlap (e.g., regex and NLP both identify the same text),
        keep the one with higher confidence. If confidence is equal, prefer regex matches.
        
        Args:
            items: List of sensitive items that may contain duplicates
            
        Returns:
            Deduplicated list of sensitive items
        """
        if not items:
            return []
        
        # Sort by start position
        sorted_items = sorted(items, key=lambda x: (x.start_pos, x.end_pos))
        
        deduplicated = []
        
        for item in sorted_items:
            # Check if this item overlaps with any existing item
            overlaps = False
            for i, existing in enumerate(deduplicated):
                # Check for overlap
                if not (item.end_pos <= existing.start_pos or item.start_pos >= existing.end_pos):
                    overlaps = True
                    # Keep the item with higher confidence
                    if item.confidence > existing.confidence:
                        deduplicated[i] = item
                    elif item.confidence == existing.confidence:
                        # If confidence is equal, prefer regex (confidence = 1.0)
                        if item.confidence == 1.0:
                            deduplicated[i] = item
                    break
            
            if not overlaps:
                deduplicated.append(item)
        
        return deduplicated
    
    def identify_sensitive_data(
        self, 
        text: str, 
        use_nlp: bool = True
    ) -> List[SensitiveItem]:
        """
        Identify sensitive information in text using regex and optionally NLP.
        
        Args:
            text: The text to analyze
            use_nlp: Whether to use NLP recognition in addition to regex
            
        Returns:
            List of identified sensitive items (deduplicated)
        """
        logger.info("starting_recognition", text_length=len(text), use_nlp=use_nlp)
        items = []
        
        # Always use regex recognition
        regex_items = self._regex_recognition(text)
        items.extend(regex_items)
        logger.info("regex_recognition_complete", items_found=len(regex_items))
        
        # Optionally use NLP recognition
        if use_nlp:
            try:
                nlp_items = self._nlp_recognition(text)
                items.extend(nlp_items)
                logger.info("nlp_recognition_complete", items_found=len(nlp_items))
            except RecognitionError:
                # Re-raise custom recognition errors
                raise
            except Exception as e:
                # If NLP fails, log and continue with regex results only
                logger.warning(
                    "nlp_recognition_failed",
                    error=str(e),
                    fallback="regex_only"
                )
        
        # Deduplicate and return
        deduplicated_items = self._deduplicate(items)
        logger.info(
            "recognition_complete",
            total_items=len(items),
            deduplicated_items=len(deduplicated_items)
        )
        return deduplicated_items
