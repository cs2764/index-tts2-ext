"""
GitIgnore Manager for GitHub Preparation

This module provides functionality to update .gitignore files with proper exclusion patterns
for the IndexTTS2 project, ensuring user-generated content, temporary files, and large
model checkpoints are properly excluded from version control.
"""

import os
from pathlib import Path
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class GitIgnoreManager:
    """Manages .gitignore configuration for GitHub preparation."""
    
    def __init__(self, project_root: str = "."):
        """
        Initialize GitIgnoreManager.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root).resolve()
        self.gitignore_path = self.project_root / ".gitignore"
        
    def get_required_patterns(self) -> List[str]:
        """
        Get the list of required .gitignore patterns for IndexTTS2.
        
        Returns:
            List of gitignore patterns that should be included
        """
        patterns = [
            # User-generated content (Requirement 4.1)
            "/outputs/",
            "/prompts/", 
            "/logs/",
            "*.log",
            
            # Python cache files and virtual environments (Requirement 4.2)
            "__pycache__/",
            "*.py[cod]",
            "*.pyo",
            "*.pyd",
            ".Python",
            ".mypy_cache/",
            ".ruff_cache/",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".tox/",
            ".venv*/",
            "venv*/",
            "conda_env*/",
            ".env",
            ".env.*",
            
            # Large model checkpoints (Requirement 4.3)
            "/checkpoints/*.pth",
            "/checkpoints/*.pt", 
            "/checkpoints/*.bin",
            "/checkpoints/*.safetensors",
            "/checkpoints/qwen0.6bemo4-merge/",
            "/checkpoints/.cache/",
            "/cache/",
            
            # Temporary and debug files (Requirement 4.4)
            "*.tmp",
            "*.temp",
            "*_temp.*",
            "*_debug.*",
            "debug_*",
            "temp_*",
            "*.bak",
            "*.swp",
            "*.swo",
            "*~",
            
            # Development tools
            ".idea/",
            ".vscode/",
            "*.sublime-*",
            
            # Distribution/Packaging
            "/build/",
            "/dist/",
            "*.egg-info/",
            ".pypirc",
            
            # Operating System files
            "*.DS_Store",
            "Thumbs.db",
            "desktop.ini",
            ".Spotlight-V100",
            ".Trashes",
            "ehthumbs.db",
            
            # Audio processing temporary files
            "*.wav.tmp",
            "*.mp3.tmp",
            "test_*.wav",
            "debug_*.wav",
            "multiple_test_*",
            
            # UV package manager
            ".uv_cache/",
        ]
        
        return patterns
    
    def read_current_gitignore(self) -> Set[str]:
        """
        Read current .gitignore file and return set of patterns.
        
        Returns:
            Set of current gitignore patterns
        """
        current_patterns = set()
        
        if self.gitignore_path.exists():
            try:
                with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            current_patterns.add(line)
            except Exception as e:
                logger.error(f"Error reading .gitignore: {e}")
                
        return current_patterns
    
    def get_missing_patterns(self) -> List[str]:
        """
        Get patterns that are required but missing from current .gitignore.
        
        Returns:
            List of missing patterns that should be added
        """
        required_patterns = set(self.get_required_patterns())
        current_patterns = self.read_current_gitignore()
        
        missing_patterns = required_patterns - current_patterns
        return sorted(list(missing_patterns))
    
    def update_gitignore(self, dry_run: bool = False) -> bool:
        """
        Update .gitignore file with required patterns.
        
        Args:
            dry_run: If True, only show what would be changed without modifying files
            
        Returns:
            True if changes were made (or would be made in dry_run), False otherwise
        """
        missing_patterns = self.get_missing_patterns()
        
        if not missing_patterns:
            logger.info("✅ .gitignore is already up to date")
            return False
            
        if dry_run:
            logger.info(f"🔍 Dry run: Would add {len(missing_patterns)} patterns to .gitignore:")
            for pattern in missing_patterns:
                logger.info(f"  + {pattern}")
            return True
            
        try:
            # Read existing content
            existing_content = ""
            if self.gitignore_path.exists():
                with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # Prepare new content
            new_content = existing_content
            if not new_content.endswith('\n') and new_content:
                new_content += '\n'
                
            # Add header for new patterns
            new_content += '\n# GitHub Preparation - Additional Patterns\n'
            
            # Group patterns by category
            user_content = [p for p in missing_patterns if any(x in p for x in ['/outputs/', '/prompts/', '/logs/', '*.log'])]
            python_cache = [p for p in missing_patterns if any(x in p for x in ['__pycache__', '*.py', '.mypy_cache', '.pytest_cache', '.venv', 'venv', '.env'])]
            model_files = [p for p in missing_patterns if any(x in p for x in ['/checkpoints/', '/cache/'])]
            temp_files = [p for p in missing_patterns if any(x in p for x in ['*.tmp', '*.temp', '*_temp', '*_debug', 'debug_', 'temp_', '*.bak'])]
            audio_temp = [p for p in missing_patterns if any(x in p for x in ['*.wav.tmp', '*.mp3.tmp', 'test_*.wav', 'debug_*.wav', 'multiple_test_'])]
            other_patterns = [p for p in missing_patterns if p not in user_content + python_cache + model_files + temp_files + audio_temp]
            
            # Add patterns by category
            if user_content:
                new_content += '\n# User-generated content\n'
                for pattern in sorted(user_content):
                    new_content += f'{pattern}\n'
                    
            if python_cache:
                new_content += '\n# Python cache and environments\n'
                for pattern in sorted(python_cache):
                    new_content += f'{pattern}\n'
                    
            if model_files:
                new_content += '\n# Model checkpoints and cache\n'
                for pattern in sorted(model_files):
                    new_content += f'{pattern}\n'
                    
            if temp_files:
                new_content += '\n# Temporary and debug files\n'
                for pattern in sorted(temp_files):
                    new_content += f'{pattern}\n'
                    
            if audio_temp:
                new_content += '\n# Audio processing temporary files\n'
                for pattern in sorted(audio_temp):
                    new_content += f'{pattern}\n'
                    
            if other_patterns:
                new_content += '\n# Additional patterns\n'
                for pattern in sorted(other_patterns):
                    new_content += f'{pattern}\n'
            
            # Write updated content
            with open(self.gitignore_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info(f"✅ Updated .gitignore with {len(missing_patterns)} new patterns")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating .gitignore: {e}")
            return False
    
    def validate_gitignore(self) -> bool:
        """
        Validate that .gitignore contains all required patterns.
        
        Returns:
            True if all required patterns are present, False otherwise
        """
        missing_patterns = self.get_missing_patterns()
        
        if missing_patterns:
            logger.warning(f"⚠️  .gitignore is missing {len(missing_patterns)} required patterns:")
            for pattern in missing_patterns:
                logger.warning(f"  - {pattern}")
            return False
            
        logger.info("✅ .gitignore validation passed - all required patterns present")
        return True
    
    def get_status_report(self) -> dict:
        """
        Get a status report of .gitignore configuration.
        
        Returns:
            Dictionary containing status information
        """
        required_patterns = self.get_required_patterns()
        current_patterns = self.read_current_gitignore()
        missing_patterns = self.get_missing_patterns()
        
        return {
            'gitignore_exists': self.gitignore_path.exists(),
            'total_required_patterns': len(required_patterns),
            'current_patterns_count': len(current_patterns),
            'missing_patterns_count': len(missing_patterns),
            'missing_patterns': missing_patterns,
            'is_complete': len(missing_patterns) == 0
        }