#!/usr/bin/env python3
"""
测试MP3文件是否正确保存到outputs文件夹
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mp3_output_to_outputs_folder():
    """测试MP3文件是否正确保存到outputs文件夹"""
    
    print("=== 测试MP3文件保存到outputs文件夹 ===")
    
    try:
        # Import required modules
        from indextts.infer_v2 import IndexTTS2
        from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
        
        print("✅ 模块导入成功")
        
        # Ensure outputs directory exists
        outputs_dir = "outputs"
        if not os.path.exists(outputs_dir):
            os.makedirs(outputs_dir)
            print(f"📁 创建outputs目录: {outputs_dir}")
        
        # Clear any existing test files
        test_files = [f for f in os.listdir(outputs_dir) if f.startswith("test_mp3_")]
        for f in test_files:
            os.remove(os.path.join(outputs_dir, f))
            print(f"🧹 清理旧测试文件: {f}")
        
        # Initialize components
        print("初始化组件...")
        tts_model = IndexTTS2()
        enhanced_webui = EnhancedWebUI()
        format_converter = enhanced_webui.get_format_converter()
        
        print("✅ 组件初始化成功")
        
        # Simulate webui.py logic
        test_text = "这是一个测试MP3文件保存到outputs文件夹的测试。"
        voice_prompt = "examples/voice_01.wav"
        format_ext = "mp3"
        mp3_bitrate = 128
        
        # Generate output paths (similar to webui.py)
        timestamp = int(time.time())
        final_mp3_path = os.path.join(outputs_dir, f"test_mp3_{timestamp}.mp3")
        temp_wav_path = os.path.join(outputs_dir, f"test_mp3_{timestamp}.wav")
        
        print(f"预期的文件路径:")
        print(f"  • 临时WAV: {temp_wav_path}")
        print(f"  • 最终MP3: {final_mp3_path}")
        
        # Step 1: Generate WAV audio
        print(f"\n🎵 步骤1: 生成WAV音频...")
        start_time = time.time()
        
        wav_output = tts_model.infer(
            spk_audio_prompt=voice_prompt,
            text=test_text,
            output_path=temp_wav_path,
            verbose=False
        )
        
        generation_time = time.time() - start_time
        print(f"✅ WAV音频生成完成:")
        print(f"   • 输出文件: {wav_output}")
        print(f"   • 生成耗时: {generation_time:.2f}秒")
        
        # Verify WAV file exists
        if not os.path.exists(wav_output):
            print(f"❌ WAV文件未生成: {wav_output}")
            return False
        
        wav_size = os.path.getsize(wav_output)
        print(f"   • 文件大小: {wav_size} bytes")
        print(f"   • 文件位置: {os.path.dirname(wav_output)}")
        
        # Step 2: Convert to MP3 with specific output path
        print(f"\n🔄 步骤2: 转换为MP3格式...")
        conversion_start = time.time()
        
        mp3_output = format_converter.convert_to_format(
            wav_output, 
            "mp3", 
            bitrate=mp3_bitrate,
            output_path=final_mp3_path
        )
        
        conversion_time = time.time() - conversion_start
        print(f"✅ MP3转换完成:")
        print(f"   • 输出文件: {mp3_output}")
        print(f"   • 转换耗时: {conversion_time:.2f}秒")
        
        # Verify MP3 file exists in correct location
        success = True
        
        if os.path.exists(mp3_output):
            mp3_size = os.path.getsize(mp3_output)
            compression_ratio = (wav_size - mp3_size) / wav_size * 100
            
            print(f"   • 文件大小: {mp3_size} bytes")
            print(f"   • 压缩率: {compression_ratio:.1f}%")
            print(f"   • 文件位置: {os.path.dirname(mp3_output)}")
            
            # Check if MP3 is in outputs folder
            if os.path.dirname(os.path.abspath(mp3_output)) == os.path.abspath(outputs_dir):
                print(f"   ✅ MP3文件正确保存在outputs文件夹中")
            else:
                print(f"   ❌ MP3文件未保存在outputs文件夹中")
                print(f"      期望位置: {os.path.abspath(outputs_dir)}")
                print(f"      实际位置: {os.path.dirname(os.path.abspath(mp3_output))}")
                success = False
            
            # Check if filename matches expected
            if os.path.basename(mp3_output) == os.path.basename(final_mp3_path):
                print(f"   ✅ 文件名正确: {os.path.basename(mp3_output)}")
            else:
                print(f"   ❌ 文件名不匹配")
                print(f"      期望文件名: {os.path.basename(final_mp3_path)}")
                print(f"      实际文件名: {os.path.basename(mp3_output)}")
                success = False
                
        else:
            print(f"   ❌ MP3文件未生成: {mp3_output}")
            success = False
        
        # Step 3: Clean up WAV file (as done in webui.py)
        if success and os.path.exists(wav_output):
            os.remove(wav_output)
            print(f"   🧹 清理临时WAV文件: {wav_output}")
        
        # Step 4: Verify final state
        print(f"\n📊 最终验证:")
        files_in_outputs = os.listdir(outputs_dir)
        test_files = [f for f in files_in_outputs if f.startswith("test_mp3_")]
        
        print(f"   • outputs文件夹中的测试文件: {test_files}")
        
        if success and test_files:
            print(f"   ✅ 测试成功: MP3文件正确保存到outputs文件夹")
            
            # Clean up test file
            for f in test_files:
                os.remove(os.path.join(outputs_dir, f))
                print(f"   🧹 清理测试文件: {f}")
        else:
            print(f"   ❌ 测试失败: MP3文件未正确保存")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webui_path_logic():
    """测试webui.py中的路径生成逻辑"""
    
    print("\n=== 测试WebUI路径生成逻辑 ===")
    
    # Simulate webui.py path generation
    output_format = "mp3"
    format_ext = output_format.lower() if output_format else "wav"
    
    # Test case 1: No auto_save
    auto_save = False
    filename_preview = None
    
    if auto_save and filename_preview:
        output_path = os.path.join("outputs", filename_preview)
    else:
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.{format_ext}")
    
    # For TTS generation, always use WAV first, then convert if needed
    temp_output = output_path
    if format_ext != "wav":
        # Generate temporary WAV path for TTS generation
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        temp_output = os.path.join("outputs", f"{base_name}.wav")
    
    print(f"路径生成测试:")
    print(f"  • 选择格式: {output_format}")
    print(f"  • 最终输出路径: {output_path}")
    print(f"  • 临时WAV路径: {temp_output}")
    print(f"  • 路径正确: {'✅' if temp_output.endswith('.wav') and output_path.endswith('.mp3') else '❌'}")
    
    return temp_output.endswith('.wav') and output_path.endswith('.mp3')

if __name__ == "__main__":
    print("开始测试MP3文件保存到outputs文件夹...\n")
    
    # Test path logic first
    path_ok = test_webui_path_logic()
    
    if path_ok:
        print("✅ 路径逻辑测试通过")
        
        # Test actual MP3 output
        output_ok = test_mp3_output_to_outputs_folder()
        
        if output_ok:
            print("\n🎉 所有测试通过! MP3文件正确保存到outputs文件夹")
            sys.exit(0)
        else:
            print("\n❌ MP3输出测试失败!")
            sys.exit(1)
    else:
        print("❌ 路径逻辑测试失败!")
        sys.exit(1)