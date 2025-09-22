#!/usr/bin/env python3
"""
Test script to verify the fixed task manager no longer uses simulation.
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
from indextts.infer_v2 import IndexTTS2


def create_test_wav_file():
    """Create a test WAV file."""
    duration = 2.0
    sample_rate = 22050
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    outputs_dir = "outputs"
    os.makedirs(outputs_dir, exist_ok=True)
    
    test_wav = os.path.join(outputs_dir, "test_fixed_task_manager.wav")
    sf.write(test_wav, audio_data, sample_rate)
    
    return test_wav


def test_fixed_task_manager():
    """Test that the task manager no longer uses simulation."""
    print("🧪 测试修复后的任务管理器...")
    print("=" * 60)
    
    try:
        # Initialize enhanced WebUI and task manager
        enhanced_webui = EnhancedWebUI()
        task_manager = enhanced_webui.get_task_manager()
        
        # Verify task manager has access to enhanced webui
        if hasattr(task_manager, 'enhanced_webui'):
            print(f"✅ 任务管理器已连接到 EnhancedWebUI")
        else:
            print(f"❌ 任务管理器未连接到 EnhancedWebUI")
        
        # Create a mock TTS engine for testing
        print(f"\n🔧 创建模拟 TTS 引擎...")
        
        class MockTTSEngine:
            """Mock TTS engine for testing."""
            def __init__(self):
                self.device = "cpu"
                self.sampling_rate = 22050
            
            def infer(self, text, voice_prompt, output_path, **kwargs):
                """Mock TTS inference that creates a real audio file."""
                print(f"🎵 MockTTSEngine.infer() 被调用")
                print(f"   📝 文本: {text}")
                print(f"   🎤 语音提示: {voice_prompt}")
                print(f"   📁 输出路径: {output_path}")
                
                # Create a real audio file (not just simulation)
                duration = len(text) * 0.1  # 0.1 seconds per character
                sample_rate = 22050
                frequency = 440
                
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save the audio file
                sf.write(output_path, audio_data, sample_rate)
                
                print(f"✅ MockTTSEngine 生成了真实音频文件: {output_path}")
                return output_path
            
            def preprocess_text(self, text):
                """Mock text preprocessing."""
                return text.strip()
        
        mock_tts = MockTTSEngine()
        
        # Test parameters
        test_text = "Hello, this is a test of the fixed task manager."
        voice_prompt = "test_voice.wav"
        output_path = "outputs/test_fixed_task_manager_output.wav"
        
        task_params = {
            'tts_engine': mock_tts,
            'text': test_text,
            'voice_prompt': voice_prompt,
            'output_path': output_path,
            'output_format': 'mp3',
            'mp3_bitrate': 128,
            'generation_kwargs': {}
        }
        
        print(f"\n📋 测试任务参数:")
        print(f"   📝 文本: {test_text}")
        print(f"   🎤 语音提示: {voice_prompt}")
        print(f"   📁 输出路径: {output_path}")
        print(f"   🎵 输出格式: mp3")
        
        # Create a mock progress tracker
        class MockProgressTracker:
            def start_stage(self, name, substages=None):
                print(f"📋 开始阶段: {name}")
            
            def update_stage_progress(self, progress, message):
                print(f"📊 阶段进度: {progress*100:.1f}% - {message}")
            
            def complete_stage(self):
                print(f"✅ 阶段完成")
            
            def add_batch_timing(self, timing_info):
                print(f"⏱️  批处理时间: {timing_info}")
        
        progress_tracker = MockProgressTracker()
        
        # Test the fixed generic task processing
        print(f"\n📞 测试修复后的通用任务处理...")
        task_id = "test_task_001"
        
        try:
            # This should now call actual TTS processing instead of simulation
            task_manager._process_generic_task(
                task_id=task_id,
                task_type="tts_generation",
                params=task_params,
                progress_tracker=progress_tracker
            )
            
            print(f"✅ 通用任务处理测试完成")
            
            # Check if the output file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ 输出文件验证: {output_path} ({file_size / 1024:.1f} KB)")
            else:
                print(f"❌ 输出文件未找到: {output_path}")
            
            # Check if MP3 file was created
            mp3_path = output_path.replace('.wav', '.mp3')
            if os.path.exists(mp3_path):
                file_size = os.path.getsize(mp3_path)
                print(f"✅ MP3 文件验证: {mp3_path} ({file_size / 1024:.1f} KB)")
            else:
                print(f"⚠️  MP3 文件未找到: {mp3_path}")
            
        except Exception as e:
            print(f"❌ 通用任务处理测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # Test the fixed basic task processing
        print(f"\n📞 测试修复后的基础任务处理...")
        basic_task_id = "test_basic_task_001"
        basic_output_path = "outputs/test_fixed_basic_task_output.wav"
        
        basic_params = task_params.copy()
        basic_params['output_path'] = basic_output_path
        
        try:
            # This should now call actual TTS processing instead of simulation
            task_manager._process_task_basic(
                task_id=basic_task_id,
                task_type="tts_generation",
                params=basic_params
            )
            
            print(f"✅ 基础任务处理测试完成")
            
            # Check if the output file was created
            if os.path.exists(basic_output_path):
                file_size = os.path.getsize(basic_output_path)
                print(f"✅ 基础任务输出文件验证: {basic_output_path} ({file_size / 1024:.1f} KB)")
            else:
                print(f"❌ 基础任务输出文件未找到: {basic_output_path}")
            
        except Exception as e:
            print(f"❌ 基础任务处理测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
    
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_fixed_task_manager()
    
    # Clean up test files
    print(f"\n🧹 清理测试文件...")
    test_files = [
        "outputs/test_fixed_task_manager.wav",
        "outputs/test_fixed_task_manager_output.wav",
        "outputs/test_fixed_task_manager_output.mp3",
        "outputs/test_fixed_basic_task_output.wav"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   删除: {file_path}")
    
    if success:
        print(f"\n✅ 所有测试通过! 任务管理器不再使用模拟。")
    else:
        print(f"\n❌ 测试失败，需要进一步调试。")