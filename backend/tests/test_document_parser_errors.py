"""
Unit tests for Document Parser error handling

Tests error conditions and edge cases for document parsing.
"""

import pytest
import tempfile
import os
from pathlib import Path

from app.document_parser import DocumentParser, ParsedDocument, DocumentParsingError

# Import document creation libraries
import fitz  # PyMuPDF
from docx import Document
from openpyxl import Workbook


class TestDocumentParserErrors:
    """Test error handling in DocumentParser"""
    
    def test_unsupported_format(self):
        """Test that unsupported file formats are rejected"""
        parser = DocumentParser()
        
        with pytest.raises(DocumentParsingError) as exc_info:
            parser.parse("test.xyz", "xyz")
        
        assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"
        assert "unsupported" in exc_info.value.message.lower()
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist"""
        parser = DocumentParser()
        
        with pytest.raises(DocumentParsingError):
            parser.parse("/nonexistent/file.txt", "txt")
    
    def test_parse_empty_pdf(self):
        """Test parsing an empty PDF document"""
        parser = DocumentParser()
        
        # Create a PDF with a blank page (can't save with zero pages)
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
            try:
                doc = fitz.open()
                # Add a blank page (PyMuPDF doesn't allow saving with zero pages)
                doc.new_page()
                doc.save(tmp_path)
                doc.close()
                
                # Should raise error for empty document (no text content)
                with pytest.raises(DocumentParsingError) as exc_info:
                    parser.parse(tmp_path, 'pdf')
                
                assert exc_info.value.error_code == "NO_CONTENT"
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_parse_pdf_with_no_text(self):
        """Test parsing a PDF with pages but no text content"""
        parser = DocumentParser()
        
        # Create a PDF with a blank page
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
            try:
                doc = fitz.open()
                doc.new_page()  # Add blank page
                doc.save(tmp_path)
                doc.close()
                
                # Should raise error for no content
                with pytest.raises(DocumentParsingError) as exc_info:
                    parser.parse(tmp_path, 'pdf')
                
                assert exc_info.value.error_code == "NO_CONTENT"
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_parse_corrupted_pdf(self):
        """Test parsing a corrupted PDF file"""
        parser = DocumentParser()
        
        # Create a file with invalid PDF content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write("This is not a valid PDF file")
        
        try:
            with pytest.raises(DocumentParsingError) as exc_info:
                parser.parse(tmp_path, 'pdf')
            
            assert exc_info.value.error_code in ["CORRUPTED_FILE", "PARSING_FAILED"]
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_parse_empty_docx(self):
        """Test parsing a DOCX with no content"""
        parser = DocumentParser()
        
        # Create a DOCX with no paragraphs
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.docx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
            try:
                doc = Document()
                # Don't add any content - python-docx creates a default empty paragraph
                doc.save(tmp_path)
                
                # Should raise error for no content
                # Note: python-docx creates documents with empty paragraphs by default
                # So we expect PARSING_FAILED or NO_CONTENT depending on implementation
                with pytest.raises(DocumentParsingError) as exc_info:
                    parser.parse(tmp_path, 'docx')
                
                # Accept either error code since empty DOCX has empty paragraphs
                assert exc_info.value.error_code in ["NO_CONTENT", "PARSING_FAILED"]
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_parse_corrupted_docx(self):
        """Test parsing a corrupted DOCX file"""
        parser = DocumentParser()
        
        # Create a file with invalid DOCX content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write("This is not a valid DOCX file")
        
        try:
            with pytest.raises(DocumentParsingError) as exc_info:
                parser.parse(tmp_path, 'docx')
            
            assert exc_info.value.error_code in ["CORRUPTED_FILE", "PARSING_FAILED"]
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_parse_empty_xlsx(self):
        """Test parsing an XLSX with no content"""
        parser = DocumentParser()
        
        # Create an XLSX with empty sheet
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
            try:
                wb = Workbook()
                ws = wb.active
                # Don't add any content
                wb.save(tmp_path)
                wb.close()
                
                # Should raise error for no content
                # Note: openpyxl creates sheets with dimensions but no actual content
                with pytest.raises(DocumentParsingError) as exc_info:
                    parser.parse(tmp_path, 'xlsx')
                
                # Accept either error code
                assert exc_info.value.error_code in ["NO_CONTENT", "PARSING_FAILED"]
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_parse_corrupted_xlsx(self):
        """Test parsing a corrupted XLSX file"""
        parser = DocumentParser()
        
        # Create a file with invalid XLSX content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write("This is not a valid XLSX file")
        
        try:
            with pytest.raises(DocumentParsingError) as exc_info:
                parser.parse(tmp_path, 'xlsx')
            
            assert exc_info.value.error_code in ["CORRUPTED_FILE", "PARSING_FAILED"]
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_parse_empty_txt(self):
        """Test parsing an empty TXT file"""
        parser = DocumentParser()
        
        # Create an empty TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
            tmp_path = tmp_file.name
            # Don't write anything
        
        try:
            with pytest.raises(DocumentParsingError) as exc_info:
                parser.parse(tmp_path, 'txt')
            
            assert exc_info.value.error_code == "EMPTY_DOCUMENT"
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_parse_txt_with_only_whitespace(self):
        """Test parsing a TXT file with only whitespace"""
        parser = DocumentParser()
        
        # Create a TXT file with only whitespace
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write("   \n\n\t\t   \n")
        
        try:
            with pytest.raises(DocumentParsingError) as exc_info:
                parser.parse(tmp_path, 'txt')
            
            assert exc_info.value.error_code == "NO_CONTENT"
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_parse_txt_with_various_encodings(self):
        """Test parsing TXT files with different encodings"""
        parser = DocumentParser()
        
        # Test UTF-8 (most common)
        test_content_utf8 = "测试内容 Test Content"
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(test_content_utf8.encode('utf-8'))
        
        try:
            result = parser.parse(tmp_path, 'txt')
            assert isinstance(result, ParsedDocument)
            assert test_content_utf8 == result.content
            assert result.metadata['encoding'] == 'utf-8'
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Test ASCII (subset of UTF-8)
        test_content_ascii = "Test Content Only"
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(test_content_ascii.encode('ascii'))
        
        try:
            result = parser.parse(tmp_path, 'txt')
            assert isinstance(result, ParsedDocument)
            assert test_content_ascii == result.content
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_error_details_preserved(self):
        """Test that error details are preserved in exceptions"""
        parser = DocumentParser()
        
        with pytest.raises(DocumentParsingError) as exc_info:
            parser.parse("nonexistent.txt", "txt")
        
        # Check that exception has proper structure
        assert hasattr(exc_info.value, 'message')
        assert hasattr(exc_info.value, 'error_code')
        assert hasattr(exc_info.value, 'details')
