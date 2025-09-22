#!/usr/bin/env python3
"""
Conservative test file organizer that only handles root-level test files.

This version is more careful about what it considers redundant and only
operates on files in the project root, never touching the tests/ directory.
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


@dataclass
class TestFileInfo:
    """Information about a test file and its organization requirements."""
    path: Path
    name: str
    is_root_level: bool
    is_redundant: bool
    target_location: Optional[Path]
    functionality: str


class ConservativeTestOrganizer:
    """Conservative test file organizer that only handles root-level files."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.tests_dir = self.project_root / "tests"
        
        # Only truly redundant patterns for root-level files
        self.redundant_patterns = {
            'debug_test_files': r'^debug_.*test.*\.py$',
            'temp_cleanup_specific': r'^test_simple_temp_cleanup\.py$',
            'cleaning_chapter_specific': r'^test_cleaning_chapter_issue\.py$',
            'enhanced_mp3_logging_specific': r'^test_enhanced_mp3_logging\.py$',
            'complete_mp3_logging_specific': r'^test_complete_mp3_logging_flow\.py$',
            'mini_regression_specific': r'^_mini_regression_test\.py$'
        }
        
        # Core functionality patterns that should be preserved
        self.preserve_patterns = {
            'webui_tests': r'.*webui.*\.py$',
            'auto_save_tests': r'.*auto_save.*\.py$',
            'format_conversion': r'.*format.*conversion.*\.py$',
            'task_manager': r'.*task.*manager.*\.py$',
            'mp3_conversion': r'.*mp3_conversion.*\.py$',
            'indentation_fix': r'.*indentation_fix.*\.py$',
            'long_text_processing': r'.*long_text_processing.*\.py$',
            'multiple_saves': r'.*multiple_saves.*\.py$',
            'outputs_folder': r'.*outputs_folder.*\.py$',
            'encoding_comprehensive': r'.*encoding_comprehensive.*\.py$'
        }
    
    def scan_root_test_files(self) -> List[TestFileInfo]:
        """Scan only root-level test files."""
        test_files = []
        
        # Only scan root directory for test files
        for file_path in self.project_root.glob("test_*.py"):
            if file_path.is_file():
                test_info = self._analyze_test_file(file_path)
                test_files.append(test_info)
        
        # Also check for other test patterns in root
        for file_path in self.project_root.glob("*test*.py"):
            if file_path.is_file() and not file_path.name.startswith("test_"):
                test_info = self._analyze_test_file(file_path)
                test_files.append(test_info)
        
        return test_files
    
    def _analyze_test_file(self, file_path: Path) -> TestFileInfo:
        """Analyze a root-level test file."""
        name = file_path.name
        functionality = self._determine_functionality(name)
        is_redundant = self._is_redundant_test(name)
        
        # Determine target location for non-redundant files
        target_location = None
        if not is_redundant:
            target_location = self.tests_dir / name
        
        return TestFileInfo(
            path=file_path,
            name=name,
            is_root_level=True,
            is_redundant=is_redundant,
            target_location=target_location,
            functionality=functionality
        )
    
    def _determine_functionality(self, name: str) -> str:
        """Determine the functionality of a test file."""
        name_lower = name.lower()
        
        # Check against preserve patterns first
        for functionality, pattern in self.preserve_patterns.items():
            if re.match(pattern, name_lower):
                return functionality
        
        # Default categorization
        if 'webui' in name_lower:
            return 'webui'
        elif 'auto_save' in name_lower:
            return 'auto_save'
        elif 'mp3' in name_lower:
            return 'audio_processing'
        elif 'task' in name_lower:
            return 'task_management'
        else:
            return 'general'
    
    def _is_redundant_test(self, name: str) -> bool:
        """Check if a root-level test file is truly redundant."""
        name_lower = name.lower()
        
        # Check against specific redundant patterns
        for category, pattern in self.redundant_patterns.items():
            if re.match(pattern, name_lower):
                return True
        
        return False
    
    def organize_root_test_files(self) -> Dict[str, any]:
        """Organize only root-level test files."""
        print("Scanning root-level test files...")
        test_files = self.scan_root_test_files()
        
        print(f"Found {len(test_files)} root-level test files")
        
        # Separate files by action
        files_to_move = [tf for tf in test_files if not tf.is_redundant and tf.target_location]
        files_to_remove = [tf for tf in test_files if tf.is_redundant]
        
        results = {
            'moved_files': [],
            'removed_files': [],
            'errors': []
        }
        
        # Ensure tests directory exists
        self.tests_dir.mkdir(exist_ok=True)
        
        # Move files to tests directory
        for test_file in files_to_move:
            try:
                success = self._move_test_file(test_file)
                if success:
                    results['moved_files'].append(test_file)
                    print(f"Moved {test_file.name} to tests/")
            except Exception as e:
                results['errors'].append(f"Failed to move {test_file.name}: {str(e)}")
        
        # Remove truly redundant files
        for test_file in files_to_remove:
            try:
                success = self._remove_redundant_file(test_file)
                if success:
                    results['removed_files'].append(test_file)
                    print(f"Removed redundant test: {test_file.name}")
            except Exception as e:
                results['errors'].append(f"Failed to remove {test_file.name}: {str(e)}")
        
        return results
    
    def _move_test_file(self, test_file: TestFileInfo) -> bool:
        """Move a test file to the tests directory."""
        try:
            # Check if target already exists
            if test_file.target_location.exists():
                print(f"Target already exists, skipping: {test_file.target_location}")
                return False
            
            # Read original content
            with open(test_file.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update imports for tests directory
            updated_content = self._update_imports_for_tests_directory(content)
            
            # Write to new location
            with open(test_file.target_location, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # Remove original file safely
            if SEND2TRASH_AVAILABLE:
                send2trash(str(test_file.path))
            else:
                # Move to .deleted directory as fallback
                deleted_dir = self.project_root / '.deleted'
                deleted_dir.mkdir(exist_ok=True)
                shutil.move(str(test_file.path), str(deleted_dir / test_file.name))
            
            return True
            
        except Exception as e:
            print(f"Error moving {test_file.name}: {str(e)}")
            return False
    
    def _remove_redundant_file(self, test_file: TestFileInfo) -> bool:
        """Remove a truly redundant test file."""
        try:
            if SEND2TRASH_AVAILABLE:
                send2trash(str(test_file.path))
            else:
                # Move to .deleted directory as fallback
                deleted_dir = self.project_root / '.deleted'
                deleted_dir.mkdir(exist_ok=True)
                
                # Create unique name if needed
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
            
            # Update relative imports to work from tests directory
            if line.strip().startswith('from indextts'):
                # Already correct for tests directory
                pass
            elif line.strip().startswith('import indextts'):
                # Already correct for tests directory
                pass
            elif 'import webui' in line and not line.strip().startswith('#'):
                # Update webui import to work from tests directory
                updated_line = line.replace('import webui', 'import sys; sys.path.append(".."); import webui')
            elif 'from webui' in line and not line.strip().startswith('#'):
                # Update webui import to work from tests directory
                updated_line = line.replace('from webui', 'import sys; sys.path.append(".."); from webui')
            
            updated_lines.append(updated_line)
        
        return '\n'.join(updated_lines)
    
    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate organization report."""
        report = []
        report.append("# Conservative Test File Organization Report")
        report.append("")
        
        report.append(f"## Summary")
        report.append(f"- Files moved to tests/: {len(results['moved_files'])}")
        report.append(f"- Redundant files removed: {len(results['removed_files'])}")
        report.append(f"- Errors: {len(results['errors'])}")
        report.append("")
        
        if results['moved_files']:
            report.append("## Files Moved to tests/")
            for test_file in results['moved_files']:
                report.append(f"- {test_file.name} ({test_file.functionality})")
            report.append("")
        
        if results['removed_files']:
            report.append("## Redundant Files Removed")
            for test_file in results['removed_files']:
                report.append(f"- {test_file.name}")
            report.append("")
        
        if results['errors']:
            report.append("## Errors")
            for error in results['errors']:
                report.append(f"- {error}")
            report.append("")
        
        return '\n'.join(report)


def main():
    """Execute conservative test organization."""
    print("Conservative Test File Organization")
    print("=" * 40)
    
    organizer = ConservativeTestOrganizer(".")
    results = organizer.organize_root_test_files()
    
    # Generate report
    report = organizer.generate_report(results)
    print("\n" + report)
    
    # Save report
    with open("conservative_test_organization_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to: conservative_test_organization_report.md")
    
    return 0 if len(results['errors']) == 0 else 1


if __name__ == "__main__":
    exit(main())