"""
Test suite for DocumentationGenerator class.

Tests bilingual documentation generation, template creation, and navigation links.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from indextts.github_preparation.documentation_generator import DocumentationGenerator


class TestDocumentationGenerator(unittest.TestCase):
    """Test cases for DocumentationGenerator class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = DocumentationGenerator(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test DocumentationGenerator initialization."""
        self.assertEqual(self.generator.project_root, Path(self.temp_dir))
        self.assertTrue(str(self.generator.config_path).endswith("config.yaml"))
        self.assertTrue(str(self.generator.pyproject_path).endswith("pyproject.toml"))
    
    def test_get_project_metadata_defaults(self):
        """Test project metadata extraction with defaults."""
        metadata = self.generator.get_project_metadata()
        
        self.assertEqual(metadata['name'], 'IndexTTS2')
        self.assertEqual(metadata['author'], 'IndexTeam')
        self.assertIn('torch', str(metadata['main_dependencies']))
        self.assertIn('gradio', str(metadata['main_dependencies']))
    
    def test_generate_navigation_links(self):
        """Test navigation links generation."""
        nav_links = self.generator.generate_navigation_links()
        
        self.assertIn('Language / 语言', nav_links)
        self.assertIn('[English Documentation]', nav_links)
        self.assertIn('[中文文档]', nav_links)
        self.assertIn('#english-documentation', nav_links)
        self.assertIn('#中文文档', nav_links)
    
    def test_generate_english_content(self):
        """Test English documentation content generation."""
        metadata = {
            'name': 'IndexTTS2',
            'description': 'Test Description',
            'python_requires': '>=3.10'
        }
        
        content = self.generator.generate_english_content(metadata)
        
        # Check key sections
        self.assertIn('# English Documentation', content)
        self.assertIn('Zero-shot Voice Cloning', content)
        self.assertIn('Emotional Expression Control', content)
        self.assertIn('Duration Control', content)
        self.assertIn('Installation', content)
        self.assertIn('uv sync --all-extras', content)
        self.assertIn('Quick Start', content)
        self.assertIn('Performance Optimization', content)
        
        # Check UV package manager instructions
        self.assertIn('pip install -U uv', content)
        self.assertIn('uv run webui.py', content)
        self.assertIn('uv tool install', content)
    
    def test_generate_chinese_content(self):
        """Test Chinese documentation content generation."""
        metadata = {
            'name': 'IndexTTS2',
            'description': 'Test Description',
            'python_requires': '>=3.10'
        }
        
        content = self.generator.generate_chinese_content(metadata)
        
        # Check key sections in Chinese
        self.assertIn('# 中文文档', content)
        self.assertIn('零样本语音克隆', content)
        self.assertIn('情感表达控制', content)
        self.assertIn('时长控制', content)
        self.assertIn('安装指南', content)
        self.assertIn('uv sync --all-extras', content)
        self.assertIn('快速开始', content)
        self.assertIn('性能优化', content)
        
        # Check UV package manager instructions in Chinese
        self.assertIn('pip install -U uv', content)
        self.assertIn('uv run webui.py', content)
    
    def test_update_readme(self):
        """Test README.md file generation."""
        self.generator.update_readme()
        
        readme_path = Path(self.temp_dir) / "README.md"
        self.assertTrue(readme_path.exists())
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check bilingual structure
        self.assertIn('Language / 语言', content)
        self.assertIn('# English Documentation', content)
        self.assertIn('# 中文文档', content)
        
        # Check navigation links
        self.assertIn('[English Documentation]', content)
        self.assertIn('[中文文档]', content)
        
        # Check IndexTTS2 features
        self.assertIn('Zero-shot Voice Cloning', content)
        self.assertIn('零样本语音克隆', content)
        
        # Check UV installation instructions
        self.assertIn('uv sync --all-extras', content)
    
    def test_create_system_docs(self):
        """Test system documentation creation."""
        self.generator.create_system_docs()
        
        docs_dir = Path(self.temp_dir) / "docs"
        self.assertTrue(docs_dir.exists())
        
        # Check API documentation
        api_doc = docs_dir / "API.md"
        self.assertTrue(api_doc.exists())
        
        with open(api_doc, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        self.assertIn('IndexTTS2 API Documentation', api_content)
        self.assertIn('IndexTTS2', api_content)
        self.assertIn('infer(text, prompt_audio', api_content)
        self.assertIn('Available Emotions', api_content)
        
        # Check deployment guide
        deployment_doc = docs_dir / "DEPLOYMENT.md"
        self.assertTrue(deployment_doc.exists())
        
        with open(deployment_doc, 'r', encoding='utf-8') as f:
            deployment_content = f.read()
        
        self.assertIn('Deployment Guide', deployment_content)
        self.assertIn('Docker Deployment', deployment_content)
        self.assertIn('webui.py', deployment_content)
        
        # Check troubleshooting guide
        troubleshooting_doc = docs_dir / "TROUBLESHOOTING.md"
        self.assertTrue(troubleshooting_doc.exists())
        
        with open(troubleshooting_doc, 'r', encoding='utf-8') as f:
            troubleshooting_content = f.read()
        
        self.assertIn('Troubleshooting Guide', troubleshooting_content)
        self.assertIn('Common Issues', troubleshooting_content)
        self.assertIn('uv add torch', troubleshooting_content)
    
    def test_generate_all_documentation(self):
        """Test complete documentation generation workflow."""
        self.generator.generate_all_documentation()
        
        # Check README exists
        readme_path = Path(self.temp_dir) / "README.md"
        self.assertTrue(readme_path.exists())
        
        # Check docs directory exists
        docs_dir = Path(self.temp_dir) / "docs"
        self.assertTrue(docs_dir.exists())
        
        # Check all documentation files exist
        expected_files = ["API.md", "DEPLOYMENT.md", "TROUBLESHOOTING.md"]
        for filename in expected_files:
            file_path = docs_dir / filename
            self.assertTrue(file_path.exists(), f"{filename} should exist")
    
    def test_bilingual_content_structure(self):
        """Test that bilingual content follows proper structure."""
        self.generator.update_readme()
        
        readme_path = Path(self.temp_dir) / "README.md"
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check order: Navigation -> English -> Chinese
        nav_pos = content.find('Language / 语言')
        english_pos = content.find('# English Documentation')
        chinese_pos = content.find('# 中文文档')
        
        self.assertLess(nav_pos, english_pos, "Navigation should come before English")
        self.assertLess(english_pos, chinese_pos, "English should come before Chinese")
    
    def test_uv_package_manager_instructions(self):
        """Test that UV package manager is properly documented."""
        metadata = self.generator.get_project_metadata()
        english_content = self.generator.generate_english_content(metadata)
        chinese_content = self.generator.generate_chinese_content(metadata)
        
        # Check UV instructions in English
        self.assertIn('pip install -U uv', english_content)
        self.assertIn('uv sync --all-extras', english_content)
        self.assertIn('uv run webui.py', english_content)
        self.assertIn('uv tool install', english_content)
        
        # Check UV instructions in Chinese
        self.assertIn('pip install -U uv', chinese_content)
        self.assertIn('uv sync --all-extras', chinese_content)
        self.assertIn('uv run webui.py', chinese_content)
        self.assertIn('uv tool install', chinese_content)
    
    def test_indextts2_capabilities_documented(self):
        """Test that IndexTTS2 capabilities are properly documented."""
        metadata = self.generator.get_project_metadata()
        english_content = self.generator.generate_english_content(metadata)
        chinese_content = self.generator.generate_chinese_content(metadata)
        
        # Key capabilities that should be documented
        capabilities = [
            ('Zero-shot Voice Cloning', '零样本语音克隆'),
            ('Emotional Expression Control', '情感表达控制'),
            ('Duration Control', '时长控制'),
            ('Multilingual Support', '多语言支持'),
            ('BigVGAN', 'BigVGAN')
        ]
        
        for english_term, chinese_term in capabilities:
            self.assertIn(english_term, english_content)
            self.assertIn(chinese_term, chinese_content)


if __name__ == '__main__':
    unittest.main()