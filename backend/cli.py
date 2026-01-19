#!/usr/bin/env python3
"""
Command-Line Interface for Document Desensitization Platform

This CLI tool provides batch processing capabilities for desensitizing documents
without requiring the web interface.

Usage:
    python cli.py -f document.pdf                    # Process single file
    python cli.py -d ./documents                     # Process directory
    python cli.py -f document.pdf --output ./results # Custom output directory
    python cli.py -d ./docs --rules phone,id_card    # Specific rules only
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

from app.document_parser import DocumentParser, ParsedDocument
from app.recognition_engine import RecognitionEngine, SensitiveItem
from app.desensitization_processor import DesensitizationProcessor, DesensitizationRule
from app.file_exporter import FileExporter
from app.exceptions import DocumentParsingError, RecognitionError
from app.database import SessionLocal
from app.models import DesensitizationRule as DBDesensitizationRule


class CLIProcessor:
    """Processor for CLI-based document desensitization"""
    
    def __init__(self, output_dir: str = "./output", rules: Optional[List[str]] = None):
        """
        Initialize CLI processor.
        
        Args:
            output_dir: Directory for output files (default: ./output)
            rules: List of rule data types to apply (default: all enabled rules)
        """
        self.output_dir = Path(output_dir)
        self.rules = rules or []  # Empty list means use all enabled rules
        self.parser = DocumentParser()
        self.recognition_engine = RecognitionEngine()
        self.desensitization_processor = DesensitizationProcessor()
        self.file_exporter = FileExporter()
        self.logger = self._setup_logger()
        
        # Statistics
        self.total_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.errors: List[Dict] = []
    
    def _setup_logger(self) -> logging.Logger:
        """
        Setup structured logging for CLI operations.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('cli')
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler('desensitization.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def process_file(self, file_path: Path, base_dir: Optional[Path] = None) -> bool:
        """
        Process a single file and return success status.
        
        Args:
            file_path: Path to the file to process
            base_dir: Base directory for preserving relative structure (optional)
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Parse document
            file_type = file_path.suffix[1:].lower()
            parsed_doc = self.parser.parse(str(file_path), file_type)
            
            # Identify sensitive data
            # Try with NLP first, fall back to regex-only if NLP fails
            try:
                sensitive_items = self.recognition_engine.identify_sensitive_data(
                    parsed_doc.content,
                    use_nlp=True
                )
            except RecognitionError as e:
                self.logger.warning(f"NLP recognition failed, falling back to regex-only: {e.message}")
                sensitive_items = self.recognition_engine.identify_sensitive_data(
                    parsed_doc.content,
                    use_nlp=False
                )
            
            self.logger.info(f"Identified {len(sensitive_items)} sensitive items")
            
            # Load rules
            if not self.rules:
                # Use all enabled rules
                rules = self._load_default_rules()
            else:
                rules = self._load_selected_rules(self.rules)
            
            # Apply desensitization
            desensitized_content = self.desensitization_processor.process(
                parsed_doc.content,
                sensitive_items,
                rules
            )
            
            # Generate output path (preserving directory structure if base_dir provided)
            output_path = self._generate_output_path(file_path, base_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export file
            output_data = self.file_exporter.export(
                desensitized_content,
                file_type,
                file_type,  # Keep same format
                parsed_doc.metadata
            )
            
            with open(output_path, 'wb') as f:
                f.write(output_data)
            
            self.logger.info(f"Successfully processed: {file_path} -> {output_path}")
            self.successful_files += 1
            return True
            
        except DocumentParsingError as e:
            self.logger.error(f"Failed to parse {file_path}: {e.message}")
            self.errors.append({
                'file': str(file_path),
                'error': f"Parsing error: {e.message}"
            })
            self.failed_files += 1
            return False
        except RecognitionError as e:
            self.logger.error(f"Failed to recognize sensitive data in {file_path}: {e.message}")
            self.errors.append({
                'file': str(file_path),
                'error': f"Recognition error: {e.message}"
            })
            self.failed_files += 1
            return False
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {str(e)}")
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            self.failed_files += 1
            return False
    
    def process_directory(self, dir_path: Path, base_dir: Optional[Path] = None) -> None:
        """
        Recursively process all supported files in directory.
        
        Args:
            dir_path: Directory path to process
            base_dir: Base directory for preserving structure (used internally)
        """
        if base_dir is None:
            base_dir = dir_path
        
        supported_extensions = {'.pdf', '.docx', '.xlsx', '.txt', '.md'}
        
        for item in dir_path.iterdir():
            if item.is_file() and item.suffix.lower() in supported_extensions:
                self.total_files += 1
                self.process_file(item, base_dir)
            elif item.is_dir():
                # Recursively process subdirectories
                self.process_directory(item, base_dir)
    
    def _generate_output_path(self, input_path: Path, base_dir: Optional[Path] = None) -> Path:
        """
        Generate output path with _desensitized suffix.
        Preserves directory structure if base_dir is provided.
        
        Args:
            input_path: Input file path
            base_dir: Base directory for calculating relative path (optional)
            
        Returns:
            Output file path with _desensitized suffix
        """
        stem = input_path.stem
        suffix = input_path.suffix
        new_name = f"{stem}_desensitized{suffix}"
        
        # If base_dir is provided, preserve directory structure
        if base_dir is not None:
            # Calculate relative path from base_dir
            try:
                relative_path = input_path.relative_to(base_dir)
                # Preserve directory structure in output
                output_relative = relative_path.parent / new_name
                return self.output_dir / output_relative
            except ValueError:
                # If input_path is not relative to base_dir, just use filename
                pass
        
        # Default: place in output directory root
        return self.output_dir / new_name
    
    def _load_default_rules(self) -> List[DesensitizationRule]:
        """
        Load all enabled desensitization rules.
        
        Returns:
            List of all enabled desensitization rules
        """
        # Try to load from database first
        try:
            db = SessionLocal()
            db_rules = db.query(DBDesensitizationRule).filter(
                DBDesensitizationRule.enabled == True
            ).all()
            db.close()
            
            if db_rules:
                return [
                    DesensitizationRule(
                        id=str(rule.id),
                        name=rule.name,
                        data_type=rule.data_type,
                        strategy=rule.strategy,
                        enabled=rule.enabled
                    )
                    for rule in db_rules
                ]
        except Exception as e:
            self.logger.warning(f"Could not load rules from database: {e}")
        
        # Fallback to default rules
        return [
            DesensitizationRule(
                id="rule_name",
                name="姓名脱敏",
                data_type="name",
                strategy="mask",
                enabled=True
            ),
            DesensitizationRule(
                id="rule_phone",
                name="手机号脱敏",
                data_type="phone",
                strategy="mask",
                enabled=True
            ),
            DesensitizationRule(
                id="rule_id_card",
                name="身份证脱敏",
                data_type="id_card",
                strategy="mask",
                enabled=True
            ),
            DesensitizationRule(
                id="rule_address",
                name="地址脱敏",
                data_type="address",
                strategy="mask",
                enabled=True
            ),
            DesensitizationRule(
                id="rule_bank_card",
                name="银行卡脱敏",
                data_type="bank_card",
                strategy="mask",
                enabled=True
            ),
            DesensitizationRule(
                id="rule_email",
                name="邮箱脱敏",
                data_type="email",
                strategy="mask",
                enabled=True
            ),
        ]
    
    def _load_selected_rules(self, rule_names: List[str]) -> List[DesensitizationRule]:
        """
        Load specific rules by data type name.
        
        Args:
            rule_names: List of data type names (e.g., ['phone', 'id_card'])
            
        Returns:
            List of selected desensitization rules
        """
        all_rules = self._load_default_rules()
        return [r for r in all_rules if r.data_type in rule_names]
    
    def print_summary(self) -> None:
        """Print processing summary report"""
        print("\n" + "="*60)
        print("脱敏处理摘要 / Desensitization Summary")
        print("="*60)
        print(f"总文件数 / Total Files: {self.total_files}")
        print(f"成功处理 / Successful: {self.successful_files}")
        print(f"处理失败 / Failed: {self.failed_files}")
        
        if self.errors:
            print("\n失败详情 / Error Details:")
            for error in self.errors:
                print(f"  - {error['file']}: {error['error']}")
        
        print("="*60)


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='文档脱敏命令行工具 / Document Desensitization CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
  # 处理单个文件 / Process single file
  python cli.py -f document.pdf
  
  # 处理目录（递归）/ Process directory recursively
  python cli.py -d ./documents
  
  # 指定输出目录 / Specify output directory
  python cli.py -f document.pdf --output ./results
  
  # 指定脱敏规则 / Specify desensitization rules
  python cli.py -f document.pdf --rules phone,id_card,email
        """
    )
    
    # Required arguments (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-f', '--file',
        type=str,
        help='处理单个文件 / Process a single file'
    )
    group.add_argument(
        '-d', '--directory',
        type=str,
        help='处理目录（递归）/ Process directory recursively'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='输出目录（默认: ./output）/ Output directory (default: ./output)'
    )
    parser.add_argument(
        '--rules',
        type=str,
        help='指定脱敏规则，逗号分隔（默认: 全部）/ Specify rules, comma-separated (default: all)'
    )
    
    args = parser.parse_args()
    
    # Parse rules
    rules = args.rules.split(',') if args.rules else []
    
    # Initialize processor
    processor = CLIProcessor(output_dir=args.output, rules=rules)
    
    # Process files
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"错误: 文件不存在 / Error: File not found: {args.file}")
            sys.exit(1)
        
        processor.total_files = 1
        processor.process_file(file_path)
    
    elif args.directory:
        dir_path = Path(args.directory)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"错误: 目录不存在 / Error: Directory not found: {args.directory}")
            sys.exit(1)
        
        processor.process_directory(dir_path)
    
    # Print summary
    processor.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if processor.failed_files == 0 else 1)


if __name__ == '__main__':
    main()
