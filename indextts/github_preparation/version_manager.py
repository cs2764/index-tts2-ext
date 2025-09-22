"""
Version management system for GitHub preparation.

This module handles version increments, pyproject.toml updates, and changelog generation
for the IndexTTS2 project preparation workflow.
"""

import re
import toml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages version information and project metadata updates."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the version manager.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.changelog_path = self.project_root / "CHANGELOG.md"
        
    def get_current_version(self) -> str:
        """Get the current version from pyproject.toml.
        
        Returns:
            Current version string.
            
        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist.
            KeyError: If version field is missing.
        """
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
            
        with open(self.pyproject_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
            
        if 'project' not in config or 'version' not in config['project']:
            raise KeyError("Version field not found in pyproject.toml")
            
        return config['project']['version']
    
    def increment_version(self, version_type: str = "patch") -> str:
        """Increment version number with current date.
        
        Args:
            version_type: Type of version increment ('major', 'minor', 'patch').
                         For GitHub preparation, we use date-based versioning.
        
        Returns:
            New version string in format: major.minor.patch-YYYYMMDD
        """
        current_version = self.get_current_version()
        
        # Parse current version (remove any existing date suffix)
        version_match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-\d{8})?$', current_version)
        if not version_match:
            raise ValueError(f"Invalid version format: {current_version}")
            
        major, minor, patch = map(int, version_match.groups())
        
        # For GitHub preparation, we increment patch and add current date
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
            
        # Add current date suffix
        date_suffix = datetime.now().strftime("%Y%m%d")
        new_version = f"{major}.{minor}.{patch}-{date_suffix}"
        
        logger.info(f"Version incremented from {current_version} to {new_version}")
        return new_version
    
    def update_pyproject_toml(self, new_version: str = None, 
                             metadata_updates: Dict = None) -> None:
        """Update pyproject.toml with new version and metadata.
        
        Args:
            new_version: New version string. If None, auto-increment patch version.
            metadata_updates: Dictionary of metadata fields to update.
        """
        if new_version is None:
            new_version = self.increment_version()
            
        # Load current configuration
        with open(self.pyproject_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
            
        # Update version
        config['project']['version'] = new_version
        
        # Apply metadata updates
        if metadata_updates:
            for key, value in metadata_updates.items():
                if '.' in key:
                    # Handle nested keys like 'project.description'
                    keys = key.split('.')
                    current = config
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value
                else:
                    config['project'][key] = value
        
        # Ensure proper project metadata for GitHub
        self._ensure_github_metadata(config)
        
        # Write updated configuration
        with open(self.pyproject_path, 'w', encoding='utf-8') as f:
            toml.dump(config, f)
            
        logger.info(f"Updated pyproject.toml with version {new_version}")
    
    def _ensure_github_metadata(self, config: Dict) -> None:
        """Ensure proper metadata for GitHub release.
        
        Args:
            config: Configuration dictionary to update.
        """
        project = config.setdefault('project', {})
        
        # Ensure required fields exist
        if 'name' not in project:
            project['name'] = 'indextts'
            
        if 'description' not in project:
            project['description'] = (
                "IndexTTS2: A Breakthrough in Emotionally Expressive and "
                "Duration-Controlled Auto-Regressive Zero-Shot Text-to-Speech"
            )
            
        if 'authors' not in project:
            project['authors'] = [{"name": "Bilibili IndexTTS Team"}]
            
        # Ensure proper URLs
        urls = project.setdefault('urls', {})
        if 'Homepage' not in urls:
            urls['Homepage'] = "https://github.com/index-tts/index-tts"
        if 'Repository' not in urls:
            urls['Repository'] = "https://github.com/index-tts/index-tts.git"
            
        # Ensure proper classifiers
        if 'classifiers' not in project:
            project['classifiers'] = [
                "Development Status :: 5 - Production/Stable",
                "Intended Audience :: Science/Research",
                "Intended Audience :: Developers",
                "Topic :: Scientific/Engineering",
                "Topic :: Scientific/Engineering :: Artificial Intelligence",
                "Natural Language :: English",
                "Natural Language :: Chinese (Simplified)",
                "Programming Language :: Python :: 3",
                "Operating System :: OS Independent",
            ]
    
    def validate_version_consistency(self) -> List[str]:
        """Validate version consistency across project files.
        
        Returns:
            List of validation issues found.
        """
        issues = []
        current_version = self.get_current_version()
        
        # Check if version follows expected format
        if not re.match(r'^\d+\.\d+\.\d+(?:-\d{8})?$', current_version):
            issues.append(f"Invalid version format in pyproject.toml: {current_version}")
            
        # Check for version references in other files
        version_files = [
            self.project_root / "README.md",
            self.project_root / "indextts" / "__init__.py",
        ]
        
        for file_path in version_files:
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Look for version patterns that might be outdated
                    version_patterns = re.findall(r'version["\s]*[:=]["\s]*([0-9]+\.[0-9]+\.[0-9]+(?:-\d{8})?)', content, re.IGNORECASE)
                    for found_version in version_patterns:
                        if found_version != current_version:
                            issues.append(f"Version mismatch in {file_path}: found {found_version}, expected {current_version}")
                except Exception as e:
                    issues.append(f"Error reading {file_path}: {e}")
        
        return issues
    
    def generate_changelog_entry(self, version: str, changes: List[str] = None) -> str:
        """Generate changelog entry for the new version.
        
        Args:
            version: Version string for the changelog entry.
            changes: List of changes to include. If None, generates default GitHub prep entry.
            
        Returns:
            Formatted changelog entry.
        """
        if changes is None:
            changes = [
                "Prepared project for GitHub release",
                "Cleaned up development artifacts and temporary files",
                "Organized test files and project structure",
                "Updated documentation and metadata",
                "Configured proper .gitignore patterns",
            ]
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        entry = f"\n## [{version}] - {date_str}\n\n"
        entry += "### Changed\n"
        for change in changes:
            entry += f"- {change}\n"
        entry += "\n"
        
        return entry
    
    def update_changelog(self, version: str = None, changes: List[str] = None) -> None:
        """Update or create changelog with new version entry.
        
        Args:
            version: Version string. If None, uses current version from pyproject.toml.
            changes: List of changes to include.
        """
        if version is None:
            version = self.get_current_version()
            
        new_entry = self.generate_changelog_entry(version, changes)
        
        if self.changelog_path.exists():
            # Read existing changelog
            content = self.changelog_path.read_text(encoding='utf-8')
            
            # Insert new entry after the header
            lines = content.split('\n')
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('# ') or line.startswith('## '):
                    if 'changelog' in line.lower() or 'change log' in line.lower():
                        header_end = i + 1
                        break
                    elif line.startswith('## ['):
                        # Found first version entry, insert before it
                        header_end = i
                        break
            
            # Insert new entry
            lines.insert(header_end, new_entry.rstrip())
            updated_content = '\n'.join(lines)
        else:
            # Create new changelog
            updated_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n{new_entry}"
        
        self.changelog_path.write_text(updated_content, encoding='utf-8')
        logger.info(f"Updated changelog with version {version}")
    
    def get_project_metadata(self) -> Dict:
        """Get current project metadata from pyproject.toml.
        
        Returns:
            Dictionary containing project metadata.
        """
        with open(self.pyproject_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
            
        return config.get('project', {})