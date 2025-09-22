"""
Example usage of DocumentationGenerator for IndexTTS2 GitHub preparation.

This script demonstrates how to use the DocumentationGenerator to create
comprehensive bilingual documentation for the IndexTTS2 project.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.documentation_generator import DocumentationGenerator


def main():
    """Main function to demonstrate documentation generation."""
    print("🚀 IndexTTS2 Documentation Generator Example")
    print("=" * 50)
    
    # Initialize the documentation generator
    generator = DocumentationGenerator(project_root)
    
    print("\n📋 Project Metadata:")
    metadata = generator.get_project_metadata()
    for key, value in metadata.items():
        if isinstance(value, list):
            print(f"  {key}: {', '.join(str(v) for v in value[:3])}...")
        else:
            print(f"  {key}: {value}")
    
    print("\n🔗 Navigation Links Preview:")
    nav_links = generator.generate_navigation_links()
    print(nav_links[:200] + "..." if len(nav_links) > 200 else nav_links)
    
    # Generate individual components
    print("\n📝 Generating Documentation Components...")
    
    # 1. Update README with bilingual content
    print("  1. Updating README.md...")
    generator.update_readme()
    
    # 2. Create system documentation
    print("  2. Creating system documentation...")
    generator.create_system_docs()
    
    # 3. Update version information
    print("  3. Updating version information...")
    generator.update_version_info()
    
    print("\n✅ Documentation generation completed!")
    
    # Show what was created
    print("\n📁 Generated Files:")
    
    readme_path = project_root / "README.md"
    if readme_path.exists():
        size = readme_path.stat().st_size
        print(f"  ✓ README.md ({size:,} bytes)")
    
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        for doc_file in docs_dir.glob("*.md"):
            size = doc_file.stat().st_size
            print(f"  ✓ docs/{doc_file.name} ({size:,} bytes)")
    
    print("\n🎯 Next Steps:")
    print("  1. Review the generated README.md file")
    print("  2. Check the docs/ directory for system documentation")
    print("  3. Customize content as needed for your specific use case")
    print("  4. Commit the changes to your repository")


def preview_readme_structure():
    """Preview the structure of the generated README."""
    print("\n📖 README Structure Preview:")
    print("=" * 30)
    
    generator = DocumentationGenerator(project_root)
    
    # Generate navigation
    nav = generator.generate_navigation_links()
    print("🔗 Navigation Section:")
    print(nav.split('\n')[0:5])
    
    # Generate English content preview
    metadata = generator.get_project_metadata()
    english_content = generator.generate_english_content(metadata)
    english_lines = english_content.split('\n')
    
    print("\n🇺🇸 English Section Headers:")
    for line in english_lines[:20]:
        if line.startswith('#'):
            print(f"  {line}")
    
    # Generate Chinese content preview
    chinese_content = generator.generate_chinese_content(metadata)
    chinese_lines = chinese_content.split('\n')
    
    print("\n🇨🇳 Chinese Section Headers:")
    for line in chinese_lines[:20]:
        if line.startswith('#'):
            print(f"  {line}")


def demonstrate_api_docs():
    """Demonstrate API documentation generation."""
    print("\n📚 API Documentation Preview:")
    print("=" * 35)
    
    generator = DocumentationGenerator(project_root)
    
    # Create temporary docs to show structure
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        generator_temp = DocumentationGenerator(temp_path)
        generator_temp._create_api_documentation(temp_path)
        
        api_file = temp_path / "API.md"
        if api_file.exists():
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Show first few sections
            lines = content.split('\n')
            for i, line in enumerate(lines[:30]):
                if line.startswith('#'):
                    print(f"  {line}")
                elif line.startswith('```'):
                    print(f"  {line}")
                elif 'IndexTTS2' in line and not line.startswith('#'):
                    print(f"  {line}")


if __name__ == "__main__":
    try:
        # Run main documentation generation
        main()
        
        # Show additional previews
        preview_readme_structure()
        demonstrate_api_docs()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Documentation generator example completed!")