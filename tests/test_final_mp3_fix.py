#!/usr/bin/env python3
"""
最终MP3修复验证测试
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_final_mp3_fix():
    """测试最终的MP3修复是否工作"""
    
    print("=== 最终MP3修复验证测试 ===")
    
    try:
        # Import exactly as in webui.py
        from indextts.infer_v2 import IndexTTS2
        from indextts.enhanced_webui import EnhancedWebUI
        
        print("✅ 模块导入成功")
        
        # Initialize exactly as in webui.py
        tts = IndexTTS2()
        enhanced_webui = EnhancedWebUI()
        
        print("✅ 组件初始化成功")
        
        # Test parameters
        text = "这是最终的MP3修复验证测试。"
        voice_prompt = "examples/voice_01.wav"
        output_format = "mp3"
        mp3_bitrate = 128
        
        # Generate paths exactly as in webui.py
        format_ext = output_format.lower()
        output_path = os.path.join("outputs", f"final_test_{int(time.time())}.{format_ext}")
        
        # For TTS generation, always use WAV first, then convert if needed
        temp_output = output_path
        if format_ext != "wav":
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            temp_output = os.path.join("outputs", f"{base_name}.wav")
        
        print(f"路径配置:")
        print(f"  • 最终MP3路径: {output_path}")
        print(f"  • 临时WAV路径: {temp_output}")
        
        # Step 1: Generate WAV
        print(f"\n🎵 步骤1: 生成WAV音频...")
        start_time = time.time()
        
        wav_result = tts.infer(
            spk_audio_prompt=voice_prompt,
            text=text,
            output_path=temp_output,
            verbose=False
        )
        
        generation_time = time.time() - start_time
        print(f"✅ WAV生成完成: {wav_result}")
        print(f"   • 耗时: {generation_time:.2f}秒")
        
        if not os.path.exists(wav_result):
            print(f"❌ WAV文件未生成")
            return False
        
        wav_size = os.path.getsize(wav_result)
        print(f"   • 文件大小: {wav_size} bytes")
        
        # Step 2: Convert to MP3 exactly as in webui.py
        if format_ext != "wav":
            print(f"\n🔄 步骤2: 转换为MP3...")
            
            try:
                conversion_start = time.time()
                
                format_converter = enhanced_webui.get_format_converter()
                
                if format_ext == "mp3":
                    print(f"🔄 转换为 MP3 格式 (比特率: {mp3_bitrate} kbps)...")
                    final_output = format_converter.convert_to_format(
                        wav_result, "mp3", 
                        bitrate=int(mp3_bitrate),
                        output_path=output_path
                    )
                
                conversion_time = time.time() - conversion_start
                print(f"✅ MP3转换完成: {final_output}")
                print(f"   • 耗时: {conversion_time:.2f}秒")
                
                # Remove temp WAV file if conversion was successful (as in webui.py)
                if final_output != wav_result and os.path.exists(wav_result):
                    os.remove(wav_result)
                    print(f"   🧹 清理临时WAV文件")
                
                output = final_output
                
            except Exception as e:
                print(f"❌ 格式转换失败: {e}")
                output = wav_result
                return False
        else:
            output = wav_result
        
        # Step 3: Verify final result
        print(f"\n📊 最终验证:")
        
        if os.path.exists(output):
            final_size = os.path.getsize(output)
            final_ext = os.path.splitext(output)[1].lower()
            output_dir = os.path.dirname(os.path.abspath(output))
            expected_dir = os.path.abspath("outputs")
            
            print(f"   • 文件存在: ✅")
            print(f"   • 文件路径: {output}")
            print(f"   • 文件格式: {final_ext}")
            print(f"   • 文件大小: {final_size} bytes")
            print(f"   • 输出目录: {output_dir}")
            print(f"   • 期望目录: {expected_dir}")
            
            success = True
            
            # Check format
            if final_ext == f'.{format_ext}':
                print(f"   ✅ 格式正确")
            else:
                print(f"   ❌ 格式错误，期望: .{format_ext}")
                success = False
            
            # Check location
            if output_dir == expected_dir:
                print(f"   ✅ 保存位置正确")
            else:
                print(f"   ❌ 保存位置错误")
                success = False
            
            # Check compression for MP3
            if format_ext == "mp3" and wav_size > 0:
                compression_ratio = (wav_size - final_size) / wav_size * 100
                print(f"   • 压缩率: {compression_ratio:.1f}%")
                if compression_ratio > 30:  # Reasonable compression
                    print(f"   ✅ 压缩效果良好")
                else:
                    print(f"   ⚠️  压缩效果一般")
            
            # Clean up
            os.remove(output)
            print(f"   🧹 清理测试文件")
            
            return success
            
        else:
            print(f"   ❌ 最终输出文件不存在: {output}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始最终MP3修复验证测试...\n")
    
    success = test_final_mp3_fix()
    
    if success:
        print("\n🎉 最终MP3修复验证成功!")
        print("✅ MP3文件现在可以正确保存到outputs文件夹")
        print("✅ 格式转换功能完全正常")
        print("✅ WebUI中选择MP3格式将正常工作")
        sys.exit(0)
    else:
        print("\n❌ 最终MP3修复验证失败!")
        sys.exit(1)