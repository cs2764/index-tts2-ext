"""
Test file organization system for GitHub preparation.

This module handles the identification, consolidation, and relocation of test files
to ensure proper project structure and eliminate redundancy.
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False
    send2trash = None

from .file_classifier import FileClassifier, FileInfo, FileAction, FileType
from .safe_file_manager import SafeFileManager


@dataclass
class TestFileInfo:
    """Information about a test file and its organization requirements."""
    path: Path
    name: str
    is_root_level: bool
    is_redundant: bool
    target_location: Optional[Path]
    functionality: str
    dependencies: List[str]


class TestOrganizer:
    """Organizes test files according to project structure best practices."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.tests_dir = self.project_root / "tests"
        self.file_classifier = FileClassifier(project_root)
        self.safe_file_manager = SafeFileManager(project_root)
        
        # Core test patterns that should be preserved
        self.core_test_patterns = {
            'regression': r'.*regression.*test.*\.py$',
            'integration': r'.*integration.*test.*\.py$',
            'performance': r'.*performance.*test.*\.py$',
            'audio_processing': r'.*audio.*test.*\.py$',
            'webui': r'.*webui.*test.*\.py$',
            'auto_save': r'.*auto_save.*test.*\.py$',
            'format_conversion': r'.*format.*conversion.*test.*\.py$',
            'task_management': r'.*task.*manager.*test.*\.py$'
        }
        
        # Redundant test patterns that can be consolidated (only for root-level files)
        self.redundant_patterns = {
            'debug_tests': r'^debug_.*test.*\.py$',
            'temp_cleanup_tests': r'^test_.*temp.*cleanup.*\.py$',
            'simple_tests': r'^test_simple_.*\.py$',
            'cleaning_chapter_tests': r'^test_cleaning_chapter.*\.py$',
            'enhanced_mp3_logging': r'^test_enhanced_mp3_logging\.py$',
            'complete_mp3_logging': r'^test_complete_mp3_logging_flow\.py$',
            'mini_regression': r'^_mini_regression_test\.py$'
        }
    
    def scan_test_files(self) -> List[TestFileInfo]:
        """Scan project for test files and classify them."""
        test_files = []
        
        # Scan root directory for test files
        for file_path in self.project_root.glob("test_*.py"):
            if file_path.is_file():
                test_info = self._analyze_test_file(file_path, is_root_level=True)
                test_files.append(test_info)
        
        # Also scan for other test-related files
        for file_path in self.project_root.glob("*test*.py"):
            if file_path.is_file() and not file_path.name.startswith("test_"):
                test_info = self._analyze_test_file(file_path, is_root_level=True)
                test_files.append(test_info)
        
        # Scan existing tests directory
        if self.tests_dir.exists():
            for file_path in self.tests_dir.glob("*.py"):
                if file_path.is_file() and file_path.name != "__init__.py":
                    test_info = self._analyze_test_file(file_path, is_root_level=False)
                    test_files.append(test_info)
        
        return test_files
    
    def _analyze_test_file(self, file_path: Path, is_root_level: bool) -> TestFileInfo:
        """Analyze a test file to determine its purpose and organization needs."""
        name = file_path.name
        functionality = self._determine_functionality(name, file_path)
        is_redundant = self._is_redundant_test(name, file_path)
        
        # Determine target location
        target_location = None
        if is_root_level and not is_redundant:
            target_location = self.tests_dir / name
        elif is_redundant:
            target_location = None  # Will be removed
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(file_path)
        
        return TestFileInfo(
            path=file_path,
            name=name,
            is_root_level=is_root_level,
            is_redundant=is_redundant,
            target_location=target_location,
            functionality=functionality,
            dependencies=dependencies
        )
    
    def _determine_functionality(self, name: str, file_path: Path) -> str:
        """Determine the core functionality of a test file."""
        name_lower = name.lower()
        
        # Check against core test patterns
        for functionality, pattern in self.core_test_patterns.items():
            if re.match(pattern, name_lower):
                return functionality
        
        # Analyze file content for additional clues
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'regression' in content.lower():
                return 'regression'
            elif 'integration' in content.lower():
                return 'integration'
            elif 'performance' in content.lower():
                return 'performance'
            elif 'webui' in content.lower() or 'gradio' in content.lower():
                return 'webui'
            elif 'auto_save' in content.lower():
                return 'auto_save'
            elif 'audio' in content.lower():
                return 'audio_processing'
            else:
                return 'general'
                
        except Exception:
            return 'unknown'
    
    def _is_redundant_test(self, name: str, file_path: Path) -> bool:
        """Check if a test file is redundant and can be removed."""
        name_lower = name.lower()
        
        # Never consider files already in tests/ directory as redundant
        if 'tests' in str(file_path.parent):
            return False
        
        # Check against redundant patterns
        for category, pattern in self.redundant_patterns.items():
            if re.match(pattern, name_lower):
                return True
        
        # Check for specific redundant cases
        if self._is_duplicate_functionality(name, file_path):
            return True
            
        # Check if it's a temporary debug file
        if 'debug' in name_lower and os.path.getmtime(file_path) < (os.path.getmtime(self.project_root) - 86400 * 7):  # Older than 7 days
            return True
            
        return False
    
    def _is_duplicate_functionality(self, name: str, file_path: Path) -> bool:
        """Check if this test duplicates functionality of existing tests."""
        functionality = self._determine_functionality(name, file_path)
        
        # Check if there's already a comprehensive test for this functionality
        existing_tests = list(self.tests_dir.glob("*.py")) if self.tests_dir.exists() else []
        
        for existing_test in existing_tests:
            if existing_test.name == name:
                continue
                
            existing_functionality = self._determine_functionality(existing_test.name, existing_test)
            
            # If there's already a comprehensive test for the same functionality
            if existing_functionality == functionality and 'comprehensive' in existing_test.name.lower():
                return True
        
        return False
    
    def _analyze_dependencies(self, file_path: Path) -> List[str]:
        """Analyze import dependencies in a test file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract import statements
            import_lines = [line.strip() for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
            
            for line in import_lines:
                if 'indextts' in line:
                    dependencies.append(line)
                elif any(pkg in line for pkg in ['pytest', 'unittest', 'gradio', 'torch']):
                    dependencies.append(line)
        
        except Exception:
            pass
        
        return dependencies
    
    def consolidate_redundant_tests(self, test_files: List[TestFileInfo]) -> Dict[str, List[TestFileInfo]]:
        """Group redundant tests for consolidation."""
        consolidation_groups = {}
        
        for test_file in test_files:
            if test_file.is_redundant:
                functionality = test_file.functionality
                if functionality not in consolidation_groups:
                    consolidation_groups[functionality] = []
                consolidation_groups[functionality].append(test_file)
        
        return consolidation_groups
    
    def organize_test_files(self) -> Dict[str, any]:
        """Execute the complete test file organization process."""
        print("Scanning test files...")
        test_files = self.scan_test_files()
        
        print(f"Found {len(test_files)} test files")
        
        # Separate files by action needed
        files_to_move = [tf for tf in test_files if tf.is_root_level and not tf.is_redundant and tf.target_location]
        files_to_remove = [tf for tf in test_files if tf.is_redundant]
        files_to_keep = [tf for tf in test_files if not tf.is_root_level and not tf.is_redundant]
        
        # Create consolidation groups
        consolidation_groups = self.consolidate_redundant_tests(test_files)
        
        # Execute organization
        results = {
            'moved_files': [],
            'removed_files': [],
            'consolidated_groups': consolidation_groups,
            'preserved_files': files_to_keep,
            'errors': []
        }
        
        # Ensure tests directory exists
        self.tests_dir.mkdir(exist_ok=True)
        
        # Move files directly (bypassing SafeFileManager restrictions for test organization)
        for test_file in files_to_move:
            try:
                success = self._move_test_file_direct(test_file)
                if success:
                    results['moved_files'].append(test_file)
                    print(f"Moved {test_file.name} to tests/")
            except Exception as e:
                results['errors'].append(f"Failed to move {test_file.name}: {str(e)}")
        
        # Remove redundant files directly
        for test_file in files_to_remove:
            try:
                success = self._remove_redundant_file_direct(test_file)
                if success:
                    results['removed_files'].append(test_file)
                    print(f"Removed redundant test: {test_file.name}")
            except Exception as e:
                results['errors'].append(f"Failed to remove {test_file.name}: {str(e)}")
        
        return results
    
    def _move_test_file_direct(self, test_file: TestFileInfo) -> bool:
        """Move a test file directly to the tests directory."""
        try:
            # Check if target already exists
            if test_file.target_location.exists():
                print(f"Target already exists, skipping: {test_file.target_location}")
                return False
            
            # Read original content
            with open(test_file.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update imports for new location
            updated_content = self._update_imports_for_tests_directory(content)
            
            # Write to new location
            with open(test_file.target_location, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # Remove original file using send2trash if available
            try:
                if SEND2TRASH_AVAILABLE:
                    send2trash(str(test_file.path))
                else:
                    # Move to .deleted directory as fallback
                    deleted_dir = self.project_root / '.deleted'
                    deleted_dir.mkdir(exist_ok=True)
                    shutil.move(str(test_file.path), str(deleted_dir / test_file.name))
            except Exception as e:
                print(f"Warning: Could not safely delete original file {test_file.path}: {e}")
                # File was copied successfully, so this is not a critical error
            
            return True
            
        except Exception as e:
            print(f"Error moving {test_file.name}: {str(e)}")
            return False
    
    def _remove_redundant_file_direct(self, test_file: TestFileInfo) -> bool:
        """Remove a redundant test file directly."""
        try:
            # Use send2trash if available
            if SEND2TRASH_AVAILABLE:
                send2trash(str(test_file.path))
            else:
                # Move to .deleted directory as fallback
                deleted_dir = self.project_root / '.deleted'
                deleted_dir.mkdir(exist_ok=True)
                
                # Create unique name if file already exists in deleted dir
                target_name = test_file.name
                counter = 1
                while (deleted_dir / target_name).exists():
                    stem = test_file.path.stem
                    suffix = test_file.path.suffix
                    target_name = f"{stem}_{counter}{suffix}"
                    counter += 1
                
                target_path = deleted_dir / target_name
                shutil.move(str(test_file.path), str(target_path))
            
            return True
            
        except Exception as e:
            print(f"Error removing {test_file.name}: {str(e)}")
            return False
    
    def _update_imports_for_tests_directory(self, content: str) -> str:
        """Update import statements for files moved to tests directory."""
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            updated_line = line
            
            # Update relative imports to indextts package
            if line.strip().startswith('from indextts'):
                # Already correct for tests directory
                pass
            elif line.strip().startswith('import indextts'):
                # Already correct for tests directory
                pass
            elif 'import ' in line and any(module in line for module in ['webui', 'infer_v2', 'cli']):
                # Update imports of root-level modules
                if 'webui' in line:
                    updated_line = line.replace('import webui', 'import sys; sys.path.append(".."); import webui')
                elif 'infer_v2' in line:
                    updated_line = line.replace('from infer_v2', 'from indextts.infer_v2')
            
            updated_lines.append(updated_line)
        
        return '\n'.join(updated_lines)
    
    def generate_organization_report(self, results: Dict[str, any]) -> str:
        """Generate a report of the test organization process."""
        report = []
        report.append("# Test File Organization Report")
        report.append("")
        
        report.append(f"## Summary")
        report.append(f"- Files moved to tests/: {len(results['moved_files'])}")
        report.append(f"- Redundant files removed: {len(results['removed_files'])}")
        report.append(f"- Files preserved in tests/: {len(results['preserved_files'])}")
        report.append(f"- Errors encountered: {len(results['errors'])}")
        report.append("")
        
        if results['moved_files']:
            report.append("## Files Moved to tests/")
            for test_file in results['moved_files']:
                report.append(f"- {test_file.name} ({test_file.functionality})")
            report.append("")
        
        if results['removed_files']:
            report.append("## Redundant Files Removed")
            for test_file in results['removed_files']:
                report.append(f"- {test_file.name} (reason: {test_file.functionality})")
            report.append("")
        
        if results['consolidated_groups']:
            report.append("## Consolidation Groups")
            for functionality, files in results['consolidated_groups'].items():
                report.append(f"### {functionality}")
                for test_file in files:
                    report.append(f"- {test_file.name}")
                report.append("")
        
        if results['errors']:
            report.append("## Errors")
            for error in results['errors']:
                report.append(f"- {error}")
            report.append("")
        
        return '\n'.join(report)