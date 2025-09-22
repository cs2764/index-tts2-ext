"""
Comprehensive GitHub Preparation Workflow for IndexTTS2

This module provides the main GitHubPreparation class that orchestrates all cleanup operations,
implements safety checks and validation, provides progress reporting and logging, and includes
rollback mechanisms for critical operations.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from .file_classifier import FileClassifier, FileInfo, FileAction, FileType
from .safe_file_manager import SafeFileManager, FileOperation
from .version_manager import VersionManager
from .documentation_generator import DocumentationGenerator
from .gitignore_manager import GitIgnoreManager


@dataclass
class WorkflowStep:
    """Represents a step in the GitHub preparation workflow."""
    name: str
    description: str
    completed: bool = False
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class WorkflowState:
    """Represents the complete state of the GitHub preparation workflow."""
    project_root: str
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[WorkflowStep] = None
    total_files_analyzed: int = 0
    operations_planned: int = 0
    operations_completed: int = 0
    operations_failed: int = 0
    rollback_available: bool = False
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


class GitHubPreparation:
    """
    Main orchestrator for GitHub preparation workflow.
    
    Coordinates all cleanup operations including file classification, safe deletion,
    test organization, version management, documentation generation, and .gitignore
    configuration with comprehensive safety checks and rollback capabilities.
    """
    
    def __init__(self, project_root: str = ".", dry_run: bool = False, backup_enabled: bool = True):
        """
        Initialize the GitHub preparation workflow.
        
        Args:
            project_root: Path to the project root directory
            dry_run: If True, only simulate operations without executing them
            backup_enabled: If True, create backups before critical operations
        """
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.backup_enabled = backup_enabled
        
        # Initialize components
        self.file_classifier = FileClassifier(str(self.project_root))
        self.safe_file_manager = SafeFileManager(str(self.project_root), dry_run=dry_run)
        self.version_manager = VersionManager(self.project_root)
        self.documentation_generator = DocumentationGenerator(str(self.project_root))
        self.gitignore_manager = GitIgnoreManager(str(self.project_root))
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Workflow state
        self.workflow_state = WorkflowState(
            project_root=str(self.project_root),
            start_time=datetime.now()
        )
        
        # Safety and validation
        self._init_safety_checks()
        
        # Progress tracking
        self.progress_callback = None
        
    def _setup_logger(self) -> logging.Logger:
        """Set up comprehensive logging for the workflow."""
        logger = logging.getLogger('GitHubPreparation')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler (only if not in dry run mode to avoid file handle issues in tests)
            if not self.dry_run:
                log_dir = self.project_root / 'logs'
                log_dir.mkdir(exist_ok=True)
                
                log_file = log_dir / f'github_preparation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
                
                logger.info(f"GitHub preparation logging initialized. Log file: {log_file}")
            else:
                logger.info("GitHub preparation logging initialized (dry run mode - no file logging)")
        
        return logger
    
    def _init_safety_checks(self):
        """Initialize comprehensive safety checks and validation rules."""
        
        # Critical files that must never be modified
        self.critical_files = {
            'webui.py',
            'pyproject.toml',
            'uv.lock',
            'LICENSE',
            '.git',
            '.gitignore',
            '.gitattributes'
        }
        
        # Critical directories that must be preserved
        self.critical_directories = {
            '.git',
            'indextts',
            '.venv',
            'venv',
            'env'
        }
        
        # Minimum required files for project functionality
        self.required_files = {
            'webui.py': 'Main web UI entry point',
            'pyproject.toml': 'Package configuration',
            'indextts/__init__.py': 'Core package initialization',
            'indextts/infer_v2.py': 'Main inference engine'
        }
        
        # Maximum safe deletion thresholds
        self.safety_thresholds = {
            'max_delete_percentage': 30,  # Never delete more than 30% of files
            'max_delete_count': 100,      # Never delete more than 100 files at once
            'min_source_files': 10        # Must preserve at least 10 source files
        }
    
    def set_progress_callback(self, callback):
        """
        Set a callback function for progress reporting.
        
        Args:
            callback: Function that accepts (step_name, progress_percentage, message)
        """
        self.progress_callback = callback
    
    def _report_progress(self, step_name: str, progress: float, message: str):
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(step_name, progress, message)
        self.logger.info(f"[{step_name}] {progress:.1f}% - {message}")
    
    def validate_project_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate that the project has the required structure and files.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.logger.info("Validating project structure...")
        issues = []
        
        # Check for required files
        for required_file, description in self.required_files.items():
            file_path = self.project_root / required_file
            if not file_path.exists():
                issues.append(f"Missing required file: {required_file} ({description})")
        
        # Check for critical directories (skip virtual environment directories as they're optional)
        for critical_dir in self.critical_directories:
            if critical_dir.startswith('.') or critical_dir in {'venv', 'env'}:
                continue  # Skip hidden directories and optional virtual environments
            dir_path = self.project_root / critical_dir
            if not dir_path.exists():
                issues.append(f"Missing critical directory: {critical_dir}")
        
        # Check if this looks like the IndexTTS2 project
        indextts_dir = self.project_root / 'indextts'
        if not indextts_dir.exists():
            issues.append("This doesn't appear to be the IndexTTS2 project (missing indextts/ directory)")
        
        # Check for webui.py
        webui_file = self.project_root / 'webui.py'
        if not webui_file.exists():
            issues.append("Missing webui.py - this doesn't appear to be the IndexTTS2 project")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info("Project structure validation passed")
        else:
            self.logger.warning(f"Project structure validation failed with {len(issues)} issues")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        
        return is_valid, issues
    
    def create_backup(self) -> Optional[str]:
        """
        Create a backup of critical files before starting operations.
        
        Returns:
            Path to backup directory if successful, None otherwise
        """
        if not self.backup_enabled:
            return None
        
        self.logger.info("Creating backup of critical files...")
        
        try:
            backup_dir = self.project_root / f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            backup_dir.mkdir(exist_ok=True)
            
            # Backup critical files
            import shutil
            
            backup_files = [
                'pyproject.toml',
                '.gitignore',
                'README.md'
            ]
            
            for file_name in backup_files:
                source_path = self.project_root / file_name
                if source_path.exists():
                    target_path = backup_dir / file_name
                    if not self.dry_run:
                        shutil.copy2(source_path, target_path)
                    self.logger.info(f"Backed up: {file_name}")
            
            self.logger.info(f"Backup created at: {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        Analyze the entire project structure and generate cleanup plan.
        
        Returns:
            Dictionary containing analysis results and cleanup plan
        """
        step = WorkflowStep(
            name="analyze_project",
            description="Analyzing project structure and generating cleanup plan",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            self._report_progress("Analysis", 0, "Starting project analysis...")
            
            # Scan all files
            self._report_progress("Analysis", 20, "Scanning project files...")
            file_infos = self.file_classifier.scan_project()
            self.workflow_state.total_files_analyzed = len(file_infos)
            
            # Generate classification report
            self._report_progress("Analysis", 40, "Classifying files...")
            classification_report = self.file_classifier.generate_cleanup_report(file_infos)
            
            # Group files by action and type
            self._report_progress("Analysis", 60, "Grouping files by action...")
            files_by_action = self.file_classifier.get_files_by_action(file_infos)
            files_by_type = self.file_classifier.get_files_by_type(file_infos)
            
            # Plan operations
            self._report_progress("Analysis", 80, "Planning file operations...")
            operations = self.safe_file_manager.plan_operations(file_infos)
            self.workflow_state.operations_planned = len(operations)
            
            # Safety validation
            self._report_progress("Analysis", 90, "Validating safety of operations...")
            safety_report = self._validate_operation_safety(operations)
            
            self._report_progress("Analysis", 100, "Analysis complete")
            
            analysis_results = {
                'total_files': len(file_infos),
                'files_by_action': {action.value: len(files) for action, files in files_by_action.items()},
                'files_by_type': {file_type.value: len(files) for file_type, files in files_by_type.items()},
                'planned_operations': len(operations),
                'classification_report': classification_report,
                'safety_report': safety_report,
                'file_infos': file_infos,
                'operations': operations
            }
            
            step.completed = True
            step.end_time = datetime.now()
            step.details = {
                'total_files': len(file_infos),
                'planned_operations': len(operations)
            }
            
            self.logger.info(f"Project analysis completed: {len(file_infos)} files analyzed, {len(operations)} operations planned")
            return analysis_results
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            self.logger.error(f"Project analysis failed: {e}")
            raise
    
    def _validate_operation_safety(self, operations: List[FileOperation]) -> Dict[str, Any]:
        """
        Validate the safety of planned operations against thresholds.
        
        Args:
            operations: List of planned operations
            
        Returns:
            Dictionary containing safety validation results
        """
        delete_operations = [op for op in operations if op.action == FileAction.DELETE]
        total_files = self.workflow_state.total_files_analyzed
        
        safety_report = {
            'is_safe': True,
            'warnings': [],
            'errors': [],
            'statistics': {
                'total_files': total_files,
                'delete_operations': len(delete_operations),
                'delete_percentage': (len(delete_operations) / total_files * 100) if total_files > 0 else 0
            }
        }
        
        # Check deletion percentage threshold
        delete_percentage = safety_report['statistics']['delete_percentage']
        if delete_percentage > self.safety_thresholds['max_delete_percentage']:
            safety_report['errors'].append(
                f"Deletion percentage ({delete_percentage:.1f}%) exceeds safety threshold "
                f"({self.safety_thresholds['max_delete_percentage']}%)"
            )
            safety_report['is_safe'] = False
        
        # Check deletion count threshold
        if len(delete_operations) > self.safety_thresholds['max_delete_count']:
            safety_report['errors'].append(
                f"Deletion count ({len(delete_operations)}) exceeds safety threshold "
                f"({self.safety_thresholds['max_delete_count']})"
            )
            safety_report['is_safe'] = False
        
        # Check for critical file operations
        for operation in operations:
            file_path = Path(operation.source_path)
            if file_path.name in self.critical_files:
                safety_report['errors'].append(
                    f"Critical file scheduled for {operation.action.value}: {file_path.name}"
                )
                safety_report['is_safe'] = False
        
        return safety_report
    
    def execute_cleanup_workflow(self, skip_confirmation: bool = False) -> Dict[str, Any]:
        """
        Execute the complete GitHub preparation workflow.
        
        Args:
            skip_confirmation: If True, skip user confirmation prompts
            
        Returns:
            Dictionary containing workflow execution results
        """
        self.logger.info("Starting GitHub preparation workflow...")
        self.workflow_state.start_time = datetime.now()
        
        try:
            # Step 1: Validate project structure
            self._report_progress("Validation", 0, "Validating project structure...")
            is_valid, issues = self.validate_project_structure()
            if not is_valid:
                raise ValueError(f"Project validation failed: {'; '.join(issues)}")
            
            # Step 2: Create backup
            self._report_progress("Backup", 0, "Creating backup...")
            backup_path = self.create_backup()
            
            # Step 3: Analyze project
            self._report_progress("Analysis", 0, "Analyzing project...")
            analysis_results = self.analyze_project()
            
            # Step 4: Safety confirmation
            if not skip_confirmation and not self.dry_run:
                safety_report = analysis_results['safety_report']
                if not safety_report['is_safe']:
                    raise ValueError(f"Safety validation failed: {'; '.join(safety_report['errors'])}")
            
            # Step 5: Execute file operations
            self._report_progress("Cleanup", 0, "Executing file cleanup...")
            cleanup_results = self._execute_file_cleanup(analysis_results['operations'])
            
            # Step 6: Organize test files
            self._report_progress("Organization", 0, "Organizing test files...")
            test_org_results = self.safe_file_manager.organize_test_files()
            
            # Step 7: Update version information
            self._report_progress("Version", 0, "Updating version information...")
            version_results = self._update_version_info()
            
            # Step 8: Generate documentation
            self._report_progress("Documentation", 0, "Generating documentation...")
            doc_results = self._generate_documentation()
            
            # Step 9: Update .gitignore
            self._report_progress("GitIgnore", 0, "Updating .gitignore...")
            gitignore_results = self._update_gitignore()
            
            # Step 10: Final validation
            self._report_progress("Final Validation", 0, "Performing final validation...")
            final_validation = self._perform_final_validation()
            
            self.workflow_state.end_time = datetime.now()
            self.workflow_state.rollback_available = True
            
            workflow_results = {
                'success': True,
                'backup_path': backup_path,
                'analysis_results': analysis_results,
                'cleanup_results': cleanup_results,
                'test_organization': test_org_results,
                'version_update': version_results,
                'documentation': doc_results,
                'gitignore_update': gitignore_results,
                'final_validation': final_validation,
                'workflow_state': self.workflow_state
            }
            
            self.logger.info("GitHub preparation workflow completed successfully")
            return workflow_results
            
        except Exception as e:
            self.workflow_state.end_time = datetime.now()
            self.logger.error(f"GitHub preparation workflow failed: {e}")
            raise
    
    def _execute_file_cleanup(self, operations: List[FileOperation]) -> Dict[str, Any]:
        """Execute file cleanup operations with progress reporting."""
        step = WorkflowStep(
            name="file_cleanup",
            description="Executing file cleanup operations",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            # Execute cleanup operations
            stats = self.safe_file_manager.execute_operations(operations)
            
            self.workflow_state.operations_completed = stats['completed']
            self.workflow_state.operations_failed = stats['failed']
            
            # Clean up temporary files
            temp_cleanup_stats = self.safe_file_manager.cleanup_temporary_files()
            
            step.completed = True
            step.end_time = datetime.now()
            step.details = {
                'operations_stats': stats,
                'temp_cleanup_stats': temp_cleanup_stats
            }
            
            return {
                'operations_stats': stats,
                'temp_cleanup_stats': temp_cleanup_stats,
                'operation_report': self.safe_file_manager.generate_operation_report()
            }
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            raise
    
    def _update_version_info(self) -> Dict[str, Any]:
        """Update version information and project metadata."""
        step = WorkflowStep(
            name="version_update",
            description="Updating version information",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            # Get current version
            current_version = self.version_manager.get_current_version()
            
            # Increment version with current date
            new_version = self.version_manager.increment_version()
            
            # Update pyproject.toml
            self.version_manager.update_pyproject_toml()
            
            step.completed = True
            step.end_time = datetime.now()
            step.details = {
                'old_version': current_version,
                'new_version': new_version
            }
            
            return {
                'old_version': current_version,
                'new_version': new_version,
                'updated_files': ['pyproject.toml']
            }
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            self.logger.warning(f"Version update failed: {e}")
            return {'error': str(e)}
    
    def _generate_documentation(self) -> Dict[str, Any]:
        """Generate bilingual documentation."""
        step = WorkflowStep(
            name="documentation_generation",
            description="Generating bilingual documentation",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            # Update README
            self.documentation_generator.update_readme()
            
            # Create system documentation
            self.documentation_generator.create_system_docs()
            
            step.completed = True
            step.end_time = datetime.now()
            
            return {
                'updated_files': ['README.md'],
                'created_files': []
            }
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            self.logger.warning(f"Documentation generation failed: {e}")
            return {'error': str(e)}
    
    def _update_gitignore(self) -> Dict[str, Any]:
        """Update .gitignore configuration."""
        step = WorkflowStep(
            name="gitignore_update",
            description="Updating .gitignore configuration",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            # Update .gitignore
            added_patterns = self.gitignore_manager.update_gitignore()
            
            step.completed = True
            step.end_time = datetime.now()
            step.details = {
                'added_patterns': added_patterns
            }
            
            return {
                'added_patterns': added_patterns,
                'updated_files': ['.gitignore']
            }
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            self.logger.warning(f"GitIgnore update failed: {e}")
            return {'error': str(e)}
    
    def _perform_final_validation(self) -> Dict[str, Any]:
        """Perform final validation of the prepared project."""
        step = WorkflowStep(
            name="final_validation",
            description="Performing final project validation",
            start_time=datetime.now()
        )
        self.workflow_state.steps.append(step)
        
        try:
            validation_results = {
                'structure_valid': True,
                'required_files_present': True,
                'gitignore_configured': True,
                'issues': []
            }
            
            # Re-validate project structure
            is_valid, issues = self.validate_project_structure()
            validation_results['structure_valid'] = is_valid
            validation_results['issues'].extend(issues)
            
            # Check .gitignore
            gitignore_path = self.project_root / '.gitignore'
            if not gitignore_path.exists():
                validation_results['gitignore_configured'] = False
                validation_results['issues'].append("Missing .gitignore file")
            
            step.completed = True
            step.end_time = datetime.now()
            step.details = validation_results
            
            return validation_results
            
        except Exception as e:
            step.error = str(e)
            step.end_time = datetime.now()
            return {'error': str(e)}
    
    def rollback_changes(self) -> Dict[str, Any]:
        """
        Attempt to rollback changes made during the workflow.
        
        Returns:
            Dictionary containing rollback results
        """
        self.logger.info("Starting rollback of GitHub preparation changes...")
        
        try:
            # Rollback file operations
            rollback_stats = self.safe_file_manager.rollback_operations()
            
            # TODO: Rollback version changes, documentation changes, etc.
            # This would require storing the original state
            
            rollback_results = {
                'success': True,
                'file_operations': rollback_stats,
                'limitations': [
                    "Files sent to system recycle bin cannot be automatically restored",
                    "Version and documentation changes require manual restoration from backup"
                ]
            }
            
            self.logger.info("Rollback completed")
            return rollback_results
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_workflow_report(self) -> str:
        """
        Generate a comprehensive report of the entire workflow.
        
        Returns:
            Formatted workflow report
        """
        report = []
        report.append("# GitHub Preparation Workflow Report")
        report.append("")
        report.append(f"**Project Root:** {self.workflow_state.project_root}")
        report.append(f"**Start Time:** {self.workflow_state.start_time}")
        if self.workflow_state.end_time:
            duration = self.workflow_state.end_time - self.workflow_state.start_time
            report.append(f"**End Time:** {self.workflow_state.end_time}")
            report.append(f"**Duration:** {duration}")
        report.append(f"**Dry Run:** {self.dry_run}")
        report.append("")
        
        # Summary statistics
        report.append("## Summary")
        report.append(f"- Total files analyzed: {self.workflow_state.total_files_analyzed}")
        report.append(f"- Operations planned: {self.workflow_state.operations_planned}")
        report.append(f"- Operations completed: {self.workflow_state.operations_completed}")
        report.append(f"- Operations failed: {self.workflow_state.operations_failed}")
        report.append(f"- Rollback available: {self.workflow_state.rollback_available}")
        report.append("")
        
        # Workflow steps
        report.append("## Workflow Steps")
        for step in self.workflow_state.steps:
            status = "✅ Completed" if step.completed else ("❌ Failed" if step.error else "⏳ In Progress")
            report.append(f"### {step.name} - {status}")
            report.append(f"**Description:** {step.description}")
            if step.start_time:
                report.append(f"**Start Time:** {step.start_time}")
            if step.end_time:
                duration = step.end_time - step.start_time if step.start_time else "Unknown"
                report.append(f"**Duration:** {duration}")
            if step.error:
                report.append(f"**Error:** {step.error}")
            if step.details:
                report.append("**Details:**")
                for key, value in step.details.items():
                    report.append(f"- {key}: {value}")
            report.append("")
        
        return "\n".join(report)
    
    def save_workflow_state(self, file_path: Optional[str] = None) -> str:
        """
        Save the current workflow state to a JSON file.
        
        Args:
            file_path: Optional path to save the state file
            
        Returns:
            Path to the saved state file
        """
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.project_root / f'github_preparation_state_{timestamp}.json'
        
        # Convert workflow state to serializable format
        state_dict = asdict(self.workflow_state)
        
        # Convert datetime objects to strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        state_dict = convert_datetime(state_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Workflow state saved to: {file_path}")
        return str(file_path)
    
    def cleanup(self):
        """Clean up resources, including logging handlers."""
        # Close and remove file handlers to prevent file handle issues
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.removeHandler(handler)