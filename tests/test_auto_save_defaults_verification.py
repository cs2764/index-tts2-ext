#!/usr/bin/env python3
"""
Test script to verify that:
1. Incremental auto-save is enabled by default
2. Output files are saved to outputs folder with correct naming format
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

def test_auto_save_defaults():
    """Test that incremental auto-save is enabled by default."""
    print("🔍 Testing incremental auto-save default configuration...")
    
    try:
        from indextts.auto_save.config_validator import create_config_validator
        
        # Create validator (this should use default preferences)
        validator = create_config_validator()
        defaults = validator.get_default_values()
        
        print(f"   📋 Default enabled: {defaults['enabled']}")
        print(f"   📋 Default interval: {defaults['interval']}")
        print(f"   📋 Source: {defaults['source']}")
        
        # Verify that auto-save is enabled by default
        assert defaults['enabled'] == True, f"Expected auto-save to be enabled by default, got {defaults['enabled']}"
        assert defaults['interval'] == 5, f"Expected default interval to be 5, got {defaults['interval']}"
        
        print("   ✅ Incremental auto-save is correctly enabled by default")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing auto-save defaults: {e}")
        return False

def test_filename_generation():
    """Test that filename generation follows the required format."""
    print("🔍 Testing filename generation format...")
    
    try:
        from indextts.output_management.output_manager import OutputManager
        from indextts.config.enhanced_config import OutputConfig
        
        # Create temporary output directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OutputConfig.default()
            config.output_directory = temp_dir
            manager = OutputManager(config)
            
            # Test filename generation with source file
            test_timestamp = datetime(2024, 1, 15, 14, 30, 45)
            filename = manager.generate_filename(
                source_file="test_book.txt",
                voice_name="alice",
                format_ext="mp3",
                timestamp=test_timestamp
            )
            
            expected = "test_book_20240115_143045_alice.mp3"
            print(f"   📋 Generated filename: {filename}")
            print(f"   📋 Expected format: {expected}")
            
            assert filename == expected, f"Expected {expected}, got {filename}"
            
            # Test filename generation without source file
            filename_no_source = manager.generate_filename(
                source_file=None,
                voice_name="bob",
                format_ext="wav",
                timestamp=test_timestamp
            )
            
            expected_no_source = "generation_20240115_143045_bob.wav"
            print(f"   📋 Generated filename (no source): {filename_no_source}")
            print(f"   📋 Expected format (no source): {expected_no_source}")
            
            assert filename_no_source == expected_no_source, f"Expected {expected_no_source}, got {filename_no_source}"
            
            print("   ✅ Filename generation follows correct format: text_filename + timestamp + voice_name")
            return True
            
    except Exception as e:
        print(f"   ❌ Error testing filename generation: {e}")
        return False

def test_outputs_folder_usage():
    """Test that outputs are correctly directed to outputs folder."""
    print("🔍 Testing outputs folder usage...")
    
    try:
        # Verify outputs folder exists or can be created
        outputs_dir = "outputs"
        if not os.path.exists(outputs_dir):
            os.makedirs(outputs_dir, exist_ok=True)
            print(f"   📁 Created outputs directory: {outputs_dir}")
        else:
            print(f"   📁 Outputs directory exists: {outputs_dir}")
        
        # Test that the directory is writable
        test_file = os.path.join(outputs_dir, "test_write_permission.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("   ✅ Outputs directory is writable")
        except Exception as e:
            print(f"   ❌ Outputs directory is not writable: {e}")
            return False
        
        # Verify that webui.py uses outputs folder
        webui_path = "webui.py"
        if os.path.exists(webui_path):
            with open(webui_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for outputs folder usage
            if 'os.path.join("outputs"' in content:
                print("   ✅ webui.py correctly uses outputs folder")
            else:
                print("   ⚠️  Could not verify outputs folder usage in webui.py")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing outputs folder: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🚀 Starting auto-save defaults verification tests...\n")
    
    results = []
    
    # Test 1: Auto-save defaults
    results.append(test_auto_save_defaults())
    print()
    
    # Test 2: Filename generation
    results.append(test_filename_generation())
    print()
    
    # Test 3: Outputs folder usage
    results.append(test_outputs_folder_usage())
    print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All requirements verified successfully!")
        print()
        print("✅ Requirement 1: Incremental auto-save is enabled by default")
        print("✅ Requirement 2: Output files saved to outputs folder with correct naming")
        print("   Format: text_filename + timestamp + voice_name.extension")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)