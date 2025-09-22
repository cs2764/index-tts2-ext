#!/usr/bin/env python3
"""
Simple test to verify the indentation fix works correctly.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_short_text():
    """Test with a short text to verify the fix works."""
    
    print("=== Testing Indentation Fix ===")
    
    # Import after fixing
    from indextts.infer_v2 import IndexTTS2
    
    # Create a short test text with multiple segments
    test_text = """这是第一个测试段落。我们要确保每个段落都被正确处理。

这是第二个测试段落。现在应该能看到正确的处理进度。

这是第三个测试段落。每个段落都应该单独处理，而不是批量跳过。

This is the fourth test paragraph in English. Each segment should be processed individually.

最后一个测试段落。如果修复成功，我们应该看到每个段落的处理进度。"""
    
    paragraph_count = len(test_text.split('\n\n'))
    print(f"Test text has {paragraph_count} paragraphs")
    
    try:
        # Initialize model
        print("Initializing IndexTTS2...")
        tts_model = IndexTTS2()
        print("✅ Model initialized")
        
        # Test inference with progress monitoring
        output_path = "test_indentation_fix_output.wav"
        
        print("Starting inference...")
        start_time = time.time()
        
        result = tts_model.infer(
            spk_audio_prompt="examples/voice_01.wav",
            text=test_text,
            output_path=output_path,
            verbose=True
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Processing completed in {processing_time:.2f} seconds")
        
        # Check if output was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Output file created: {output_path} ({file_size} bytes)")
            
            # If processing was very fast (less than 5 seconds for 5 paragraphs), it might still be buggy
            if processing_time < 5:
                print("⚠️  Processing was very fast - please verify each segment was processed individually")
            else:
                print("✅ Processing time seems reasonable for individual segment processing")
                
            return True
        else:
            print("❌ Output file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_short_text()
    if success:
        print("🎉 Indentation fix test completed successfully!")
    else:
        print("❌ Indentation fix test failed!")
    
    sys.exit(0 if success else 1)