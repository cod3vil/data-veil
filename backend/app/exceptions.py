"""
Custom Exception Classes for Data Desensitization Platform

This module defines custom exception classes for different error scenarios
in the desensitization platform, providing structured error handling with
error codes and detailed information.
"""

from typing import Dict, Optional, Any


class DesensitizationError(Exception):
    """
    Base exception for all desensitization platform errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code for categorization
        details: Additional context information about the error
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "DESENSITIZATION_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base desensitization error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context information
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format for API responses.
        
        Returns:
            Dictionary containing error information
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class FileUploadError(DesensitizationError):
    """
    Exception raised during file upload operations.
    
    Common scenarios:
    - Unsupported file format
    - File size exceeds limit
    - File corruption
    - Network interruption during upload
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "FILE_UPLOAD_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize file upload error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for upload errors
            details: Additional context (e.g., file size, format)
        """
        super().__init__(message, error_code, details)


class DocumentParsingError(DesensitizationError):
    """
    Exception raised during document parsing operations.
    
    Common scenarios:
    - Corrupted document structure
    - Unsupported encoding
    - Password-protected documents
    - Empty documents
    - Invalid file format
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "DOCUMENT_PARSING_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize document parsing error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for parsing errors
            details: Additional context (e.g., file type, parsing stage)
        """
        super().__init__(message, error_code, details)


class RecognitionError(DesensitizationError):
    """
    Exception raised during sensitive data recognition operations.
    
    Common scenarios:
    - NLP model loading failure
    - Insufficient memory for large documents
    - Invalid regex patterns
    - Recognition timeout
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "RECOGNITION_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize recognition error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for recognition errors
            details: Additional context (e.g., recognition method, text length)
        """
        super().__init__(message, error_code, details)


class DesensitizationProcessingError(DesensitizationError):
    """
    Exception raised during desensitization processing operations.
    
    Common scenarios:
    - Invalid rule configuration
    - Processing timeout for large documents
    - Strategy application failure
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "PROCESSING_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize desensitization processing error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for processing errors
            details: Additional context (e.g., rule info, item count)
        """
        super().__init__(message, error_code, details)


class ExportError(DesensitizationError):
    """
    Exception raised during file export operations.
    
    Common scenarios:
    - Insufficient disk space
    - File write permission errors
    - Format conversion failures
    - Invalid output format
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "EXPORT_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize export error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for export errors
            details: Additional context (e.g., output format, file size)
        """
        super().__init__(message, error_code, details)
