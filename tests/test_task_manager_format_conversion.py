#!/usr/bin/env python3
"""
Test script to verify task manager format conversion works.
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indextts.enhanced_webui import EnhancedWebUI
from indextts.task_management.task_manager import TaskManager


def create_test_wav_file():
    """Create a test WAV file for conversion."""
    duration = 3.0
    sample_rate = 22050
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    outputs_dir = "outputs"
    os.makedirs(outputs_dir, exist_ok=True)
    
    test_wav = os.path.join(outputs_dir, "test_task_manager_mp3.wav")
    sf.write(test_wav, audio_data, sample_rate)
    
    return test_wav


def test_task_manager_format_conversion():
    """Test the task manager format conversion."""
    print("🧪 测试任务管理器格式转换...")
    print("=" * 60)
    
    # Create test WAV file
    test_wav = create_test_wav_file()
    print(f"📁 创建测试 WAV 文件: {test_wav}")
    
    try:
        # Initialize enhanced WebUI
        enhanced_webui = EnhancedWebUI()
        task_manager = enhanced_webui.get_task_manager()
        
        # Verify task manager has access to enhanced webui
        if hasattr(task_manager, 'enhanced_webui'):
            print(f"✅ 任务管理器已连接到 EnhancedWebUI")
        else:
            print(f"❌ 任务管理器未连接到 EnhancedWebUI")
        
        # Test format conversion parameters
        generation_params = {
            'output_format': 'mp3',
            'mp3_bitrate': 128
        }
        
        print(f"\n🔄 测试任务管理器格式转换...")
        print(f"   📁 输入文件: {test_wav}")
        print(f"   🎵 目标格式: {generation_params['output_format']}")
        print(f"   🎚️ 比特率: {generation_params['mp3_bitrate']} kbps")
        
        # Create a mock progress tracker
        class MockProgressTracker:
            def start_stage(self, name, substages):
                print(f"📋 开始阶段: {name}")
            
            def update_stage_progress(self, progress, message):
                print(f"📊 进度更新: {progress*100:.1f}% - {message}")
            
            def complete_stage(self):
                print(f"✅ 阶段完成")
        
        progress_tracker = MockProgressTracker()
        
        # Simulate the format conversion part of task processing
        print(f"\n📞 调用任务管理器格式转换逻辑...")
        
        # This is the code from task_manager.py
        output_format = generation_params.get('output_format', 'wav').lower()
        result_path = test_wav
        
        if output_format != 'wav' and result_path:
            progress_tracker.start_stage("Format Conversion", ["Converting to target format"])
            progress_tracker.update_stage_progress(0.5, "Converting audio format")
            
            print(f"🔍 DEBUG: TaskManager 正在执行格式转换 - task_manager.py")
            print(f"   📁 输入文件: {result_path}")
            print(f"   🎵 目标格式: {output_format}")
            
            try:
                # Get format converter from enhanced webui
                if hasattr(task_manager, 'enhanced_webui') and task_manager.enhanced_webui:
                    format_converter = task_manager.enhanced_webui.get_format_converter()
                    
                    if output_format == "mp3":
                        bitrate = generation_params.get('mp3_bitrate', 128)
                        print(f"   🎚️ MP3 比特率: {bitrate} kbps")
                        
                        # Create output path
                        output_path = result_path.replace('.wav', '.mp3')
                        
                        # This should trigger our enhanced logging
                        converted_path = format_converter.convert_to_format(
                            result_path, "mp3", 
                            bitrate=bitrate,
                            output_path=output_path
                        )
                        
                        # Update result path to the converted file
                        result_path = converted_path
                        print(f"✅ TaskManager 格式转换完成: {result_path}")
                
                else:
                    print("⚠️  无法获取格式转换器，跳过转换")
                    
            except Exception as e:
                print(f"❌ TaskManager 格式转换失败: {e}")
                import traceback
                traceback.print_exc()
            
            progress_tracker.update_stage_progress(1.0, "Format conversion complete")
            progress_tracker.complete_stage()
        
        return result_path
    
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_task_manager_format_conversion()
    
    # Clean up
    print(f"\n🧹 清理测试文件...")
    test_files = [
        "outputs/test_task_manager_mp3.wav",
        "outputs/test_task_manager_mp3.mp3"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   删除: {file_path}")
    
    print(f"\n✅ 测试完成!")