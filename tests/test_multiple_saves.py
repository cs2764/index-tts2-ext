#!/usr/bin/env python3
"""
Test script to verify auto-save functionality with multiple segments.
"""

import os
import sys
import torch
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '.')

from indextts.infer_v2 import IndexTTS2

def test_multiple_auto_saves():
    """Test auto-save functionality with multiple segments to trigger saves."""
    
    print("🔍 Testing auto-save with multiple segments...")
    print(f"Time: {datetime.now()}")
    
    # Initialize TTS
    try:
        tts = IndexTTS2(
            cfg_path="checkpoints/config.yaml", 
            model_dir="checkpoints", 
            use_cuda_kernel=False
        )
        print("✅ TTS initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize TTS: {e}")
        return
    
    # Test configuration with longer text to generate multiple segments
    test_text = """
    这是一个更长的测试文本，用于验证自动保存功能在多个段落中的工作情况。
    我们需要确保每隔几个段落就会触发一次自动保存。
    这样可以验证增量保存功能是否正常工作。
    同时也要测试最终的文件合并和清理功能。
    希望这个测试能够成功完成所有的自动保存操作。
    """
    
    voice_prompt = "examples/voice_01.wav"
    output_path = "test_multiple_saves.wav"
    
    print(f"📝 Test text length: {len(test_text)} characters")
    print(f"🎤 Voice prompt: {voice_prompt}")
    print(f"💾 Output path: {output_path}")
    
    # Configure auto-save with smaller interval to trigger more saves
    print("\n🔧 Configuring auto-save...")
    try:
        tts.set_auto_save_config(
            save_interval=2,  # Save every 2 segments
            enabled=True,
            output_path=output_path,
            voice_name="test_voice",
            source_filename="multiple_test"
        )
        print("✅ Auto-save configured")
        print(f"   - Interval: 2 segments")
        
    except Exception as e:
        print(f"❌ Failed to configure auto-save: {e}")
        return
    
    # Run inference with debug output
    print("\n🚀 Starting inference...")
    start_time = time.time()
    
    try:
        # Add progress callback for debugging
        def debug_progress(progress, desc):
            print(f"📊 Progress: {progress*100:.1f}% - {desc}")
        
        tts.gr_progress = debug_progress
        
        result_path = tts.infer(
            spk_audio_prompt=voice_prompt,
            text=test_text,
            output_path=output_path,
            verbose=False,  # Reduce verbosity for cleaner output
            max_text_tokens_per_segment=30  # Smaller segments to trigger more saves
        )
        
        end_time = time.time()
        print(f"\n✅ Inference completed in {end_time - start_time:.2f} seconds")
        print(f"📁 Result path: {result_path}")
        
        # Check if output file exists
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"📊 Output file size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print(f"❌ Output file not found: {result_path}")
        
        # Check save manager status
        if tts.save_manager:
            save_status = tts.save_manager.get_save_status()
            print(f"\n💾 Final save manager status:")
            print(f"   - Current step: {save_status.get('current_step', 'N/A')}")
            print(f"   - Last save step: {save_status.get('last_save_step', 'N/A')}")
            print(f"   - Buffer segments: {save_status.get('buffer_info', {}).get('segment_count', 'N/A')}")
            
            if tts.save_manager.last_save_info:
                print(f"   - Last save: {tts.save_manager.last_save_info}")
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Multiple saves test completed")

if __name__ == "__main__":
    test_multiple_auto_saves()