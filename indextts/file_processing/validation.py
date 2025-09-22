"""
Comprehensive file validation and error reporting for file processing.
"""

import os
import zipfile
import mimetypes
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import chardet


class ValidationErrorType(Enum):
    """Types of validation errors."""
    FILE_NOT_FOUND = "file_not_found"
    FILE_NOT_READABLE = "file_not_readable"
    FILE_EMPTY = "file_empty"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    CORRUPTED_FILE = "corrupted_file"
    INVALID_ENCODING = "invalid_encoding"
    INVALID_EPUB = "invalid_epub"
    PERMISSION_DENIED = "permission_denied"
    INVALID_CONTENT = "invalid_content"


@dataclass
class ValidationError:
    """Represents a validation error with detailed information."""
    error_type: ValidationErrorType
    message: str
    details: Dict[str, Any]
    suggestions: List[str]
    severity: str = "error"  # "error", "warning", "info"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation error to dictionary."""
        return {
            'error_type': self.error_type.value,
            'message': self.message,
            'details': self.details,
            'suggestions': self.suggestions,
            'severity': self.severity
        }


@dataclass
class ValidationResult:
    """Result of file validation with errors and warnings."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    file_info: Dict[str, Any]
    
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return len(self.warnings) > 0
    
    def get_error_messages(self) -> List[str]:
        """Get list of error messages."""
        return [error.message for error in self.errors]
    
    def get_warning_messages(self) -> List[str]:
        """Get list of warning messages."""
        return [warning.message for warning in self.warnings]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'file_info': self.file_info
        }


class FileValidator:
    """Comprehensive file validator with detailed error reporting."""
    
    def __init__(self, max_file_size: int = 50 * 1024 * 1024, 
                 supported_formats: List[str] = None):
        """
        Initialize file validator.
        
        Args:
            max_file_size: Maximum allowed file size in bytes
            supported_formats: List of supported file extensions
        """
        self.max_file_size = max_file_size
        self.supported_formats = supported_formats or ['txt', 'epub']
        self.encoding_detector = chardet.UniversalDetector()
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Perform comprehensive file validation.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        errors = []
        warnings = []
        file_info = {}
        
        try:
            # Basic file existence and accessibility checks
            basic_validation = self._validate_basic_file_properties(file_path)
            errors.extend(basic_validation['errors'])
            warnings.extend(basic_validation['warnings'])
            file_info.update(basic_validation['file_info'])
            
            # If basic validation failed, don't continue
            if basic_validation['errors']:
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    file_info=file_info
                )
            
            # Format-specific validation
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            if file_ext == 'txt':
                format_validation = self._validate_txt_file(file_path)
            elif file_ext == 'epub':
                format_validation = self._validate_epub_file(file_path)
            else:
                format_validation = {
                    'errors': [ValidationError(
                        error_type=ValidationErrorType.UNSUPPORTED_FORMAT,
                        message=f"Unsupported file format: {file_ext}",
                        details={'format': file_ext, 'supported_formats': self.supported_formats},
                        suggestions=[
                            f"Please use one of the supported formats: {', '.join(self.supported_formats)}",
                            "Convert your file to TXT or EPUB format"
                        ]
                    )],
                    'warnings': [],
                    'file_info': {}
                }
            
            errors.extend(format_validation['errors'])
            warnings.extend(format_validation['warnings'])
            file_info.update(format_validation['file_info'])
            
            # Content validation
            if not errors:  # Only validate content if no format errors
                content_validation = self._validate_file_content(file_path, file_ext)
                errors.extend(content_validation['errors'])
                warnings.extend(content_validation['warnings'])
                file_info.update(content_validation['file_info'])
            
        except Exception as e:
            errors.append(ValidationError(
                error_type=ValidationErrorType.CORRUPTED_FILE,
                message=f"Unexpected error during validation: {str(e)}",
                details={'exception': str(e), 'exception_type': type(e).__name__},
                suggestions=[
                    "Check if the file is corrupted or in use by another application",
                    "Try uploading the file again",
                    "Verify file integrity"
                ]
            ))
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            file_info=file_info
        )
    
    def _validate_basic_file_properties(self, file_path: str) -> Dict[str, Any]:
        """Validate basic file properties like existence, size, permissions."""
        errors = []
        warnings = []
        file_info = {}
        
        # Check file existence
        if not os.path.exists(file_path):
            errors.append(ValidationError(
                error_type=ValidationErrorType.FILE_NOT_FOUND,
                message=f"File not found: {file_path}",
                details={'file_path': file_path},
                suggestions=[
                    "Check if the file path is correct",
                    "Ensure the file exists and hasn't been moved or deleted",
                    "Try uploading the file again"
                ]
            ))
            return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
        
        # Check if it's actually a file
        if not os.path.isfile(file_path):
            errors.append(ValidationError(
                error_type=ValidationErrorType.FILE_NOT_READABLE,
                message=f"Path is not a file: {file_path}",
                details={'file_path': file_path, 'is_directory': os.path.isdir(file_path)},
                suggestions=[
                    "Ensure you're selecting a file, not a directory",
                    "Check the file path"
                ]
            ))
            return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
        
        # Get file stats
        try:
            stat = os.stat(file_path)
            file_info.update({
                'file_size': stat.st_size,
                'modified_time': stat.st_mtime,
                'permissions': oct(stat.st_mode)[-3:]
            })
        except OSError as e:
            errors.append(ValidationError(
                error_type=ValidationErrorType.PERMISSION_DENIED,
                message=f"Cannot access file: {str(e)}",
                details={'file_path': file_path, 'os_error': str(e)},
                suggestions=[
                    "Check file permissions",
                    "Ensure the file is not locked by another application",
                    "Try running with appropriate permissions"
                ]
            ))
            return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
        
        # Check file size
        file_size = stat.st_size
        if file_size == 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.FILE_EMPTY,
                message="File is empty",
                details={'file_path': file_path, 'file_size': file_size},
                suggestions=[
                    "Ensure the file contains text content",
                    "Check if the file was properly saved",
                    "Try uploading a different file"
                ]
            ))
        elif file_size > self.max_file_size:
            errors.append(ValidationError(
                error_type=ValidationErrorType.FILE_TOO_LARGE,
                message=f"File size {file_size:,} bytes exceeds maximum allowed size {self.max_file_size:,} bytes",
                details={
                    'file_size': file_size,
                    'max_size': self.max_file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'max_size_mb': round(self.max_file_size / (1024 * 1024), 2)
                },
                suggestions=[
                    f"Reduce file size to under {self.max_file_size // (1024 * 1024)}MB",
                    "Split large files into smaller chunks",
                    "Remove unnecessary content from the file"
                ]
            ))
        
        # Check file format
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        file_info.update({
            'filename': filename,
            'file_extension': file_ext,
            'mime_type': mimetypes.guess_type(file_path)[0]
        })
        
        if file_ext not in self.supported_formats:
            errors.append(ValidationError(
                error_type=ValidationErrorType.UNSUPPORTED_FORMAT,
                message=f"Unsupported file format: {file_ext}",
                details={
                    'format': file_ext,
                    'supported_formats': self.supported_formats,
                    'filename': filename
                },
                suggestions=[
                    f"Use one of the supported formats: {', '.join(self.supported_formats)}",
                    "Convert your file to TXT or EPUB format",
                    "Check the file extension"
                ]
            ))
        
        # File size warnings
        if file_size > self.max_file_size * 0.8:  # Warn at 80% of max size
            warnings.append(ValidationError(
                error_type=ValidationErrorType.FILE_TOO_LARGE,
                message=f"File is large ({file_size:,} bytes). Processing may take longer.",
                details={
                    'file_size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                },
                suggestions=[
                    "Consider splitting large files for faster processing",
                    "Processing may take several minutes"
                ],
                severity="warning"
            ))
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _validate_txt_file(self, file_path: str) -> Dict[str, Any]:
        """Validate TXT file specific properties."""
        errors = []
        warnings = []
        file_info = {}
        
        try:
            # Detect encoding
            encoding_result = self._detect_encoding_with_confidence(file_path)
            file_info.update(encoding_result['file_info'])
            
            if encoding_result['errors']:
                errors.extend(encoding_result['errors'])
                return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
            
            if encoding_result['warnings']:
                warnings.extend(encoding_result['warnings'])
            
            # Try to read the file with detected encoding
            encoding = encoding_result['file_info']['detected_encoding']
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(1024)  # Read first 1KB for validation
                
                file_info['content_preview'] = content[:200] + "..." if len(content) > 200 else content
                file_info['has_content'] = len(content.strip()) > 0
                
                if not content.strip():
                    errors.append(ValidationError(
                        error_type=ValidationErrorType.INVALID_CONTENT,
                        message="File appears to be empty or contains only whitespace",
                        details={'encoding': encoding},
                        suggestions=[
                            "Ensure the file contains readable text",
                            "Check if the correct encoding was detected",
                            "Try saving the file with UTF-8 encoding"
                        ]
                    ))
                
            except UnicodeDecodeError as e:
                # Try fallback encodings before marking as error
                fallback_encodings = ['gbk', 'gb2312', 'latin1']
                content_read = False
                
                for fallback_encoding in fallback_encodings:
                    try:
                        with open(file_path, 'r', encoding=fallback_encoding) as f:
                            content = f.read(1024)
                        file_info['detected_encoding'] = fallback_encoding
                        file_info['encoding_fallback_used'] = True
                        content_read = True
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not content_read:
                    errors.append(ValidationError(
                        error_type=ValidationErrorType.INVALID_ENCODING,
                        message=f"Cannot decode file with any supported encoding",
                        details={'attempted_encodings': [encoding] + fallback_encodings, 'decode_error': str(e)},
                        suggestions=[
                            "Try saving the file with UTF-8 encoding",
                            "Check if the file encoding is correct",
                            "Use a text editor to convert the file encoding"
                        ]
                    ))
                else:
                    warnings.append(ValidationError(
                        error_type=ValidationErrorType.INVALID_ENCODING,
                        message=f"Used fallback encoding {file_info['detected_encoding']} instead of detected {encoding}",
                        details={'detected_encoding': encoding, 'fallback_encoding': file_info['detected_encoding']},
                        suggestions=[
                            "File content may not display exactly as intended",
                            "Consider saving the file with UTF-8 encoding for best compatibility"
                        ],
                        severity="warning"
                    ))
            
        except Exception as e:
            errors.append(ValidationError(
                error_type=ValidationErrorType.CORRUPTED_FILE,
                message=f"Error validating TXT file: {str(e)}",
                details={'exception': str(e)},
                suggestions=[
                    "Check if the file is corrupted",
                    "Try opening the file in a text editor",
                    "Re-save the file and try again"
                ]
            ))
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _validate_epub_file(self, file_path: str) -> Dict[str, Any]:
        """Validate EPUB file specific properties."""
        errors = []
        warnings = []
        file_info = {}
        
        try:
            # Check if it's a valid ZIP file (EPUB is a ZIP archive)
            try:
                with zipfile.ZipFile(file_path, 'r') as epub_zip:
                    file_list = epub_zip.namelist()
                    file_info['epub_files'] = len(file_list)
                    
                    # Check for required EPUB files
                    required_files = ['META-INF/container.xml']
                    missing_files = [f for f in required_files if f not in file_list]
                    
                    if missing_files:
                        errors.append(ValidationError(
                            error_type=ValidationErrorType.INVALID_EPUB,
                            message=f"Invalid EPUB: missing required files: {', '.join(missing_files)}",
                            details={'missing_files': missing_files, 'total_files': len(file_list)},
                            suggestions=[
                                "Ensure the file is a valid EPUB format",
                                "Try re-exporting the EPUB from your source",
                                "Use an EPUB validator tool to check the file"
                            ]
                        ))
                    
                    # Check for content files
                    content_files = [f for f in file_list if f.endswith(('.html', '.xhtml', '.htm'))]
                    file_info['content_files'] = len(content_files)
                    
                    if not content_files:
                        warnings.append(ValidationError(
                            error_type=ValidationErrorType.INVALID_CONTENT,
                            message="EPUB contains no HTML content files",
                            details={'total_files': len(file_list)},
                            suggestions=[
                                "Check if the EPUB contains readable content",
                                "Verify the EPUB was created correctly"
                            ],
                            severity="warning"
                        ))
                    
                    # Try to validate with ebooklib if available
                    try:
                        import ebooklib
                        from ebooklib import epub
                        
                        book = epub.read_epub(file_path)
                        
                        # Get basic metadata
                        title = book.get_metadata('DC', 'title')
                        author = book.get_metadata('DC', 'creator')
                        
                        file_info.update({
                            'epub_title': title[0][0] if title else "Unknown",
                            'epub_author': author[0][0] if author else "Unknown",
                            'epub_items': len(list(book.get_items()))
                        })
                        
                        # Check for text content
                        text_items = [item for item in book.get_items() 
                                    if item.get_type() == ebooklib.ITEM_DOCUMENT]
                        
                        if not text_items:
                            warnings.append(ValidationError(
                                error_type=ValidationErrorType.INVALID_CONTENT,
                                message="EPUB contains no readable text content",
                                details={'total_items': len(list(book.get_items()))},
                                suggestions=[
                                    "Ensure the EPUB contains text content",
                                    "Check if the EPUB was created correctly"
                                ],
                                severity="warning"
                            ))
                        
                    except ImportError:
                        warnings.append(ValidationError(
                            error_type=ValidationErrorType.INVALID_EPUB,
                            message="Cannot fully validate EPUB: ebooklib not available",
                            details={'validation_level': 'basic'},
                            suggestions=[
                                "Install ebooklib for full EPUB validation",
                                "Basic ZIP validation passed"
                            ],
                            severity="warning"
                        ))
                    except Exception as e:
                        # Don't fail validation for ebooklib issues if basic ZIP structure is valid
                        warnings.append(ValidationError(
                            error_type=ValidationErrorType.INVALID_EPUB,
                            message=f"EPUB detailed validation failed: {str(e)}",
                            details={'validation_error': str(e), 'basic_zip_valid': True},
                            suggestions=[
                                "EPUB may still be processable despite validation warnings",
                                "Try re-creating the EPUB file if processing fails",
                                "Use an EPUB validator tool for detailed analysis"
                            ],
                            severity="warning"
                        ))
            
            except zipfile.BadZipFile:
                errors.append(ValidationError(
                    error_type=ValidationErrorType.CORRUPTED_FILE,
                    message="File is not a valid ZIP archive (EPUB files must be ZIP format)",
                    details={'file_type': 'invalid_zip'},
                    suggestions=[
                        "Ensure the file is a valid EPUB format",
                        "Check if the file was corrupted during transfer",
                        "Try re-downloading or re-creating the EPUB file"
                    ]
                ))
            
        except Exception as e:
            errors.append(ValidationError(
                error_type=ValidationErrorType.CORRUPTED_FILE,
                message=f"Error validating EPUB file: {str(e)}",
                details={'exception': str(e)},
                suggestions=[
                    "Check if the file is corrupted",
                    "Ensure the file is a valid EPUB format",
                    "Try uploading the file again"
                ]
            ))
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _validate_file_content(self, file_path: str, file_ext: str) -> Dict[str, Any]:
        """Validate file content for readability and structure."""
        errors = []
        warnings = []
        file_info = {}
        
        try:
            if file_ext == 'txt':
                content_validation = self._validate_txt_content(file_path)
            elif file_ext == 'epub':
                content_validation = self._validate_epub_content(file_path)
            else:
                return {'errors': [], 'warnings': [], 'file_info': {}}
            
            errors.extend(content_validation['errors'])
            warnings.extend(content_validation['warnings'])
            file_info.update(content_validation['file_info'])
            
        except Exception as e:
            warnings.append(ValidationError(
                error_type=ValidationErrorType.INVALID_CONTENT,
                message=f"Could not validate file content: {str(e)}",
                details={'exception': str(e)},
                suggestions=[
                    "File may still be processable",
                    "Check file content manually if needed"
                ],
                severity="warning"
            ))
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _validate_txt_content(self, file_path: str) -> Dict[str, Any]:
        """Validate TXT file content structure and readability."""
        errors = []
        warnings = []
        file_info = {}
        
        # This is already handled in _validate_txt_file
        # Additional content-specific validation can be added here
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _validate_epub_content(self, file_path: str) -> Dict[str, Any]:
        """Validate EPUB content structure and readability."""
        errors = []
        warnings = []
        file_info = {}
        
        # This is already handled in _validate_epub_file
        # Additional content-specific validation can be added here
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}
    
    def _detect_encoding_with_confidence(self, file_path: str) -> Dict[str, Any]:
        """Detect file encoding with confidence scoring and validation."""
        errors = []
        warnings = []
        file_info = {}
        
        self.encoding_detector.reset()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks for better detection
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.encoding_detector.feed(chunk)
                    if self.encoding_detector.done:
                        break
            
            self.encoding_detector.close()
            result = self.encoding_detector.result
            
            if result and result['confidence'] >= 0.8:
                detected_encoding = result['encoding'].lower()
                
                # Map common encoding variations
                encoding_map = {
                    'gb2312': 'gb2312',
                    'gbk': 'gbk',
                    'utf-8': 'utf-8',
                    'utf8': 'utf-8',
                    'ascii': 'utf-8',
                    'windows-1252': 'utf-8',
                }
                
                final_encoding = encoding_map.get(detected_encoding, detected_encoding)
                
                file_info.update({
                    'detected_encoding': final_encoding,
                    'encoding_confidence': result['confidence'],
                    'raw_encoding': result['encoding']
                })
                
                if result['confidence'] < 0.9:
                    warnings.append(ValidationError(
                        error_type=ValidationErrorType.INVALID_ENCODING,
                        message=f"Encoding detection confidence is low ({result['confidence']:.2f})",
                        details={
                            'detected_encoding': final_encoding,
                            'confidence': result['confidence']
                        },
                        suggestions=[
                            "File may not display correctly",
                            "Consider saving the file with UTF-8 encoding",
                            "Check the file content after processing"
                        ],
                        severity="warning"
                    ))
                
            else:
                # Low confidence or no detection
                file_info.update({
                    'detected_encoding': 'utf-8',
                    'encoding_confidence': result['confidence'] if result else 0.0,
                    'fallback_used': True
                })
                
                warnings.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_ENCODING,
                    message="Could not reliably detect file encoding, using UTF-8 fallback",
                    details={
                        'confidence': result['confidence'] if result else 0.0,
                        'fallback_encoding': 'utf-8'
                    },
                    suggestions=[
                        "File may not display correctly",
                        "Try saving the file with UTF-8 encoding",
                        "Check the file content after processing"
                    ],
                    severity="warning"
                ))
                
        except Exception as e:
            # Don't fail validation for encoding detection errors, use fallback
            warnings.append(ValidationError(
                error_type=ValidationErrorType.INVALID_ENCODING,
                message=f"Encoding detection failed, using UTF-8 fallback: {str(e)}",
                details={'exception': str(e)},
                suggestions=[
                    "File may not display correctly if encoding is wrong",
                    "Try saving the file with UTF-8 encoding",
                    "Check the file content after processing"
                ],
                severity="warning"
            ))
            
            # Fallback to UTF-8
            file_info.update({
                'detected_encoding': 'utf-8',
                'encoding_confidence': 0.0,
                'fallback_used': True,
                'detection_error': str(e)
            })
        
        return {'errors': errors, 'warnings': warnings, 'file_info': file_info}


def validate_file_upload(file_path: str, max_file_size: int = None, 
                        supported_formats: List[str] = None) -> ValidationResult:
    """
    Convenience function for validating uploaded files.
    
    Args:
        file_path: Path to the file to validate
        max_file_size: Maximum allowed file size in bytes
        supported_formats: List of supported file extensions
        
    Returns:
        ValidationResult with detailed validation information
    """
    validator = FileValidator(
        max_file_size=max_file_size or 50 * 1024 * 1024,
        supported_formats=supported_formats or ['txt', 'epub']
    )
    
    return validator.validate_file(file_path)


def format_validation_errors_for_ui(validation_result: ValidationResult) -> Dict[str, Any]:
    """
    Format validation errors for display in the user interface.
    
    Args:
        validation_result: Result from file validation
        
    Returns:
        Dictionary with formatted error information for UI display
    """
    if validation_result.is_valid:
        return {
            'status': 'success',
            'message': 'File validation passed successfully',
            'file_info': validation_result.file_info
        }
    
    # Format errors for display
    error_messages = []
    for error in validation_result.errors:
        error_msg = f"❌ {error.message}"
        if error.suggestions:
            error_msg += f"\n   💡 {error.suggestions[0]}"
        error_messages.append(error_msg)
    
    # Format warnings for display
    warning_messages = []
    for warning in validation_result.warnings:
        warning_msg = f"⚠️ {warning.message}"
        if warning.suggestions:
            warning_msg += f"\n   💡 {warning.suggestions[0]}"
        warning_messages.append(warning_msg)
    
    return {
        'status': 'error',
        'message': f"File validation failed with {len(validation_result.errors)} error(s)",
        'errors': error_messages,
        'warnings': warning_messages,
        'file_info': validation_result.file_info,
        'detailed_errors': [error.to_dict() for error in validation_result.errors],
        'detailed_warnings': [warning.to_dict() for warning in validation_result.warnings]
    }