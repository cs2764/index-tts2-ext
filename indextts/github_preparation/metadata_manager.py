"""
Project metadata management for GitHub preparation.

This module handles validation and updates to pyproject.toml to ensure proper
project description, URLs, entry points, and UV-compatible build system configuration.
"""

import os
import re
import toml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectMetadata:
    """Data model for project metadata."""
    name: str
    version: str
    description: str
    authors: List[Dict[str, str]]
    license: str
    license_files: List[str]
    readme: str
    classifiers: List[str]
    requires_python: str
    dependencies: List[str]
    optional_dependencies: Dict[str, List[str]]
    urls: Dict[str, str]
    scripts: Dict[str, str]


class MetadataManager:
    """Manages project metadata validation and updates for pyproject.toml."""
    
    def __init__(self, project_root: str = "."):
        """Initialize metadata manager.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.current_metadata = None
        
    def load_current_metadata(self) -> ProjectMetadata:
        """Load current metadata from pyproject.toml.
        
        Returns:
            ProjectMetadata object with current configuration
            
        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist
            ValueError: If pyproject.toml is malformed
        """
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
            
        try:
            with open(self.pyproject_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
                
            project_data = data.get('project', {})
            
            self.current_metadata = ProjectMetadata(
                name=project_data.get('name', ''),
                version=project_data.get('version', ''),
                description=project_data.get('description', ''),
                authors=project_data.get('authors', []),
                license=project_data.get('license', ''),
                license_files=project_data.get('license-files', []),
                readme=project_data.get('readme', ''),
                classifiers=project_data.get('classifiers', []),
                requires_python=project_data.get('requires-python', ''),
                dependencies=project_data.get('dependencies', []),
                optional_dependencies=project_data.get('optional-dependencies', {}),
                urls=project_data.get('urls', {}),
                scripts=project_data.get('scripts', {})
            )
            
            return self.current_metadata
            
        except Exception as e:
            raise ValueError(f"Failed to parse pyproject.toml: {e}")
    
    def validate_metadata(self) -> List[str]:
        """Validate current metadata against requirements.
        
        Returns:
            List of validation issues found
        """
        issues = []
        
        if not self.current_metadata:
            self.load_current_metadata()
            
        metadata = self.current_metadata
        
        # Validate basic project information
        if not metadata.name:
            issues.append("Project name is missing")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', metadata.name):
            issues.append("Project name contains invalid characters")
            
        if not metadata.version:
            issues.append("Project version is missing")
        elif not re.match(r'^\d+\.\d+\.\d+', metadata.version):
            issues.append("Project version format is invalid (should be semantic versioning)")
            
        if not metadata.description:
            issues.append("Project description is missing")
        elif len(metadata.description) < 50:
            issues.append("Project description is too short (should be at least 50 characters)")
            
        # Validate authors
        if not metadata.authors:
            issues.append("Authors list is empty")
        else:
            for i, author in enumerate(metadata.authors):
                if not isinstance(author, dict) or 'name' not in author:
                    issues.append(f"Author {i+1} is missing name field")
                    
        # Validate URLs
        required_urls = ['Homepage', 'Repository']
        for url_type in required_urls:
            if url_type not in metadata.urls:
                issues.append(f"Missing {url_type} URL")
            elif not metadata.urls[url_type].startswith(('http://', 'https://')):
                issues.append(f"{url_type} URL is not a valid HTTP(S) URL")
                
        # Validate entry points
        if not metadata.scripts:
            issues.append("No CLI entry points defined")
        elif 'indextts' not in metadata.scripts:
            issues.append("Missing main 'indextts' CLI entry point")
            
        # Validate Python version requirement
        if not metadata.requires_python:
            issues.append("Python version requirement is missing")
        elif not re.match(r'>=\d+\.\d+', metadata.requires_python):
            issues.append("Python version requirement format is invalid")
            
        # Validate dependencies
        if not metadata.dependencies:
            issues.append("Dependencies list is empty")
        else:
            # Check for core dependencies
            core_deps = ['torch', 'torchaudio', 'transformers', 'librosa']
            missing_core = []
            dep_names = [dep.split('==')[0].split('>=')[0].split('~=')[0] for dep in metadata.dependencies]
            
            for core_dep in core_deps:
                if core_dep not in dep_names:
                    missing_core.append(core_dep)
                    
            if missing_core:
                issues.append(f"Missing core dependencies: {', '.join(missing_core)}")
                
            # Check for gradio in webui optional dependencies
            webui_deps = metadata.optional_dependencies.get('webui', [])
            webui_dep_names = [dep.split('==')[0].split('>=')[0].split('~=')[0] for dep in webui_deps]
            if 'gradio' not in webui_dep_names:
                issues.append("Missing gradio in webui optional dependencies")
                
        return issues
    
    def update_project_description(self) -> None:
        """Update project description to reflect IndexTTS2 capabilities."""
        enhanced_description = (
            "IndexTTS2: A breakthrough text-to-speech system combining emotionally expressive "
            "speech synthesis with precise duration control in an autoregressive zero-shot "
            "architecture. Features include zero-shot voice cloning, independent emotion control "
            "through multiple modalities, multilingual support (Chinese/English), and high-quality "
            "22kHz audio generation with BigVGAN vocoder."
        )
        
        if self.current_metadata:
            self.current_metadata.description = enhanced_description
    
    def update_project_urls(self) -> None:
        """Update project URLs with proper GitHub repository links."""
        # Note: Using placeholder URLs as per instructions to avoid real company details
        updated_urls = {
            'Homepage': 'https://github.com/cs2764/index-tts2-ext',
            'Repository': 'https://github.com/cs2764/index-tts2-ext.git',
            'Documentation': 'https://github.com/cs2764/index-tts2-ext/blob/main/README.md',
            'Issues': 'https://github.com/cs2764/index-tts2-ext/issues',
            'Changelog': 'https://github.com/cs2764/index-tts2-ext/releases'
        }
        
        if self.current_metadata:
            self.current_metadata.urls.update(updated_urls)
    
    def update_entry_points(self) -> None:
        """Update entry points configuration for CLI and web UI."""
        updated_scripts = {
            'indextts': 'indextts.cli:main',
            'indextts-webui': 'webui:main'
        }
        
        if self.current_metadata:
            self.current_metadata.scripts.update(updated_scripts)
    
    def update_dependencies(self) -> None:
        """Update dependency specifications to reflect current technology stack."""
        # Ensure core dependencies are properly specified
        core_updates = {
            'torch': '2.8.*',
            'torchaudio': '2.8.*',
            'transformers': '4.52.1',
            'gradio': None,  # Move to optional dependencies
            'librosa': '0.10.2.post1',
            'safetensors': '0.5.2',
            'accelerate': '1.8.1',
            'omegaconf': '>=2.3.0',
            'sentencepiece': '>=0.2.1'
        }
        
        if not self.current_metadata:
            return
            
        # Update main dependencies
        updated_deps = []
        for dep in self.current_metadata.dependencies:
            dep_name = dep.split('==')[0].split('>=')[0].split('~=')[0]
            if dep_name in core_updates:
                if core_updates[dep_name] is not None:
                    updated_deps.append(f"{dep_name}=={core_updates[dep_name]}")
                # Skip if None (move to optional)
            else:
                updated_deps.append(dep)
                
        self.current_metadata.dependencies = updated_deps
        
        # Ensure gradio is in webui optional dependencies
        if 'webui' not in self.current_metadata.optional_dependencies:
            self.current_metadata.optional_dependencies['webui'] = []
            
        webui_deps = self.current_metadata.optional_dependencies['webui']
        if not any('gradio' in dep for dep in webui_deps):
            webui_deps.append('gradio==5.44.1')
    
    def ensure_uv_compatibility(self) -> Dict[str, Any]:
        """Ensure UV-compatible build system configuration.
        
        Returns:
            Updated build system configuration
        """
        uv_build_config = {
            'build-system': {
                'requires': ['hatchling >= 1.27.0'],
                'build-backend': 'hatchling.build'
            },
            'tool': {
                'uv': {
                    'no-build-isolation-package': ['deepspeed']
                },
                'uv.sources': {
                    'torch': [
                        {
                            'index': 'pytorch-cuda',
                            'marker': "sys_platform == 'linux' or sys_platform == 'win32'"
                        }
                    ],
                    'torchaudio': [
                        {
                            'index': 'pytorch-cuda', 
                            'marker': "sys_platform == 'linux' or sys_platform == 'win32'"
                        }
                    ],
                    'torchvision': [
                        {
                            'index': 'pytorch-cuda',
                            'marker': "sys_platform == 'linux' or sys_platform == 'win32'"
                        }
                    ]
                },
                'uv.index': [
                    {
                        'name': 'pytorch-cuda',
                        'url': 'https://download.pytorch.org/whl/cu128',
                        'explicit': True
                    }
                ]
            }
        }
        
        return uv_build_config
    
    def update_classifiers(self) -> None:
        """Update project classifiers to reflect current status and capabilities."""
        updated_classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Science/Research",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "Topic :: Scientific/Engineering",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Multimedia :: Sound/Audio :: Speech",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Natural Language :: English", 
            "Natural Language :: Chinese (Simplified)",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Operating System :: OS Independent",
            "License :: Other/Proprietary License"
        ]
        
        if self.current_metadata:
            self.current_metadata.classifiers = updated_classifiers
    
    def generate_updated_pyproject(self) -> Dict[str, Any]:
        """Generate complete updated pyproject.toml configuration.
        
        Returns:
            Dictionary containing updated pyproject.toml structure
        """
        if not self.current_metadata:
            self.load_current_metadata()
            
        # Apply all updates
        self.update_project_description()
        self.update_project_urls()
        self.update_entry_points()
        self.update_dependencies()
        self.update_classifiers()
        
        # Build complete configuration
        config = {
            'project': {
                'name': self.current_metadata.name,
                'version': self.current_metadata.version,
                'description': self.current_metadata.description,
                'authors': self.current_metadata.authors,
                'license': self.current_metadata.license,
                'license-files': self.current_metadata.license_files,
                'readme': self.current_metadata.readme,
                'classifiers': self.current_metadata.classifiers,
                'requires-python': self.current_metadata.requires_python,
                'dependencies': self.current_metadata.dependencies,
                'optional-dependencies': self.current_metadata.optional_dependencies,
                'urls': self.current_metadata.urls,
                'scripts': self.current_metadata.scripts
            }
        }
        
        # Add UV-compatible build system
        uv_config = self.ensure_uv_compatibility()
        config.update(uv_config)
        
        # Add dependency groups for development
        config['dependency-groups'] = {
            'dev': [
                'pytest>=8.4.2',
                'pytest-cov>=4.0.0',
                'black>=23.0.0',
                'flake8>=6.0.0',
                'mypy>=1.0.0'
            ]
        }
        
        return config
    
    def write_updated_pyproject(self, backup: bool = True) -> None:
        """Write updated pyproject.toml file.
        
        Args:
            backup: Whether to create backup of original file
            
        Raises:
            IOError: If file operations fail
        """
        if backup and self.pyproject_path.exists():
            backup_path = self.pyproject_path.with_suffix('.toml.backup')
            backup_path.write_text(self.pyproject_path.read_text(encoding='utf-8'), encoding='utf-8')
            
        try:
            updated_config = self.generate_updated_pyproject()
            
            with open(self.pyproject_path, 'w', encoding='utf-8') as f:
                toml.dump(updated_config, f)
                
        except Exception as e:
            raise IOError(f"Failed to write updated pyproject.toml: {e}")
    
    def validate_and_update(self) -> Dict[str, Any]:
        """Perform complete validation and update workflow.
        
        Returns:
            Dictionary with validation results and update status
        """
        results = {
            'validation_issues': [],
            'updates_applied': [],
            'success': False
        }
        
        try:
            # Load and validate current metadata
            self.load_current_metadata()
            issues = self.validate_metadata()
            results['validation_issues'] = issues
            
            # Apply updates
            original_desc = self.current_metadata.description
            self.update_project_description()
            if self.current_metadata.description != original_desc:
                results['updates_applied'].append('Updated project description')
                
            original_urls = dict(self.current_metadata.urls)
            self.update_project_urls()
            if self.current_metadata.urls != original_urls:
                results['updates_applied'].append('Updated project URLs')
                
            original_scripts = dict(self.current_metadata.scripts)
            self.update_entry_points()
            if self.current_metadata.scripts != original_scripts:
                results['updates_applied'].append('Updated entry points')
                
            original_deps = list(self.current_metadata.dependencies)
            self.update_dependencies()
            if self.current_metadata.dependencies != original_deps:
                results['updates_applied'].append('Updated dependencies')
                
            original_classifiers = list(self.current_metadata.classifiers)
            self.update_classifiers()
            if self.current_metadata.classifiers != original_classifiers:
                results['updates_applied'].append('Updated classifiers')
                
            # Write updated configuration
            self.write_updated_pyproject()
            results['updates_applied'].append('Updated pyproject.toml file')
            
            results['success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            
        return results