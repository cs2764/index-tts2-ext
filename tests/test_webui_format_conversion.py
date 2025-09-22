#!/usr/bin/env python3
"""
测试WebUI中的完整格式转换流程
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def simulate_webui_generation_with_mp3():
    """模拟WebUI中的完整音频生成和MP3转换流程"""
    
    print("=== 模拟WebUI完整流程测试 ===")
    
    try:
        # Import required modules
        from indextts.infer_v2 import IndexTTS2
        from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
        
        print("✅ 模块导入成功")
        
        # Initialize components (similar to webui.py)
        print("初始化组件...")
        tts_model = IndexTTS2()
        enhanced_webui = EnhancedWebUI()
        
        print("✅ 组件初始化成功")
        
        # Simulate user input
        test_text = "这是一个完整的WebUI格式转换测试。我们将生成WAV音频，然后转换为MP3格式。"
        voice_prompt = "examples/voice_01.wav"
        output_format = "mp3"  # User selected MP3
        mp3_bitrate = 128      # User selected 128 kbps
        
        print(f"用户输入:")
        print(f"  • 文本: {test_text}")
        print(f"  • 语音样本: {voice_prompt}")
        print(f"  • 输出格式: {output_format.upper()}")
        print(f"  • MP3比特率: {mp3_bitrate} kbps")
        
        # Step 1: Generate WAV audio (as done in webui.py)
        print(f"\n🎵 步骤1: 生成WAV音频...")
        temp_output = f"test_webui_temp_{int(time.time())}.wav"
        
        start_time = time.time()
        wav_output = tts_model.infer(
            spk_audio_prompt=voice_prompt,
            text=test_text,
            output_path=temp_output,
            verbose=False
        )
        generation_time = time.time() - start_time
        
        print(f"✅ WAV音频生成完成:")
        print(f"   • 输出文件: {wav_output}")
        print(f"   • 生成耗时: {generation_time:.2f}秒")
        
        if not os.path.exists(wav_output):
            print(f"❌ WAV文件未生成: {wav_output}")
            return False
        
        wav_size = os.path.getsize(wav_output)
        print(f"   • 文件大小: {wav_size} bytes")
        
        # Step 2: Convert format if needed (as done in webui.py)
        format_ext = output_format.lower()
        if format_ext != "wav":
            print(f"\n🔄 步骤2: 转换为 {format_ext.upper()} 格式...")
            
            try:
                conversion_start_time = time.time()
                
                # Get format converter (as done in webui.py)
                format_converter = enhanced_webui.get_format_converter()
                
                if format_ext == "mp3":
                    print(f"🔄 转换为 MP3 格式 (比特率: {mp3_bitrate} kbps)...")
                    final_output = format_converter.convert_to_format(
                        wav_output, 
                        "mp3", 
                        bitrate=int(mp3_bitrate)
                    )
                else:
                    final_output = wav_output
                
                conversion_time = time.time() - conversion_start_time
                
                if final_output != wav_output and os.path.exists(final_output):
                    mp3_size = os.path.getsize(final_output)
                    compression_ratio = (wav_size - mp3_size) / wav_size * 100
                    
                    print(f"✅ 格式转换完成:")
                    print(f"   • 输出文件: {final_output}")
                    print(f"   • 文件大小: {mp3_size} bytes")
                    print(f"   • 压缩率: {compression_ratio:.1f}%")
                    print(f"   • 转换耗时: {conversion_time:.2f}秒")
                    
                    # Remove temp WAV file if conversion was successful (as done in webui.py)
                    if os.path.exists(wav_output):
                        os.remove(wav_output)
                        print(f"   • 清理临时WAV文件: {wav_output}")
                    
                    output = final_output
                else:
                    print(f"❌ 格式转换失败，保留原始WAV文件")
                    output = wav_output
                
            except Exception as e:
                print(f"❌ 格式转换失败: {e}")
                print("保留原始WAV输出")
                output = wav_output
        else:
            output = wav_output
        
        # Step 3: Final summary (as done in webui.py)
        total_time = time.time() - start_time
        print(f"\n" + "=" * 50)
        print(f"🎉 音频生成流程完成!")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        if output:
            print(f"📁 最终输出文件: {os.path.basename(output)}")
            print(f"📁 完整路径: {output}")
        print("=" * 50)
        
        # Verify final output
        if os.path.exists(output):
            final_size = os.path.getsize(output)
            final_ext = os.path.splitext(output)[1].lower()
            
            print(f"\n✅ 最终验证:")
            print(f"   • 文件存在: ✓")
            print(f"   • 文件格式: {final_ext}")
            print(f"   • 文件大小: {final_size} bytes")
            print(f"   • 格式正确: {'✓' if final_ext == f'.{format_ext}' else '✗'}")
            
            # Clean up
            os.remove(output)
            print(f"   • 清理测试文件: {output}")
            
            return final_ext == f'.{format_ext}'
        else:
            print(f"\n❌ 最终输出文件不存在: {output}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_formats():
    """测试多种格式转换"""
    
    print("\n=== 测试多种格式转换 ===")
    
    formats_to_test = [
        ("wav", None),
        ("mp3", 64),
        ("mp3", 128),
        ("mp3", 192)
    ]
    
    results = {}
    
    for format_ext, bitrate in formats_to_test:
        format_name = f"{format_ext.upper()}"
        if bitrate:
            format_name += f" ({bitrate}kbps)"
        
        print(f"\n--- 测试格式: {format_name} ---")
        
        try:
            # Import required modules
            from indextts.infer_v2 import IndexTTS2
            from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
            
            # Initialize components
            tts_model = IndexTTS2()
            enhanced_webui = EnhancedWebUI()
            
            # Generate short test audio
            test_text = f"测试{format_name}格式。"
            temp_wav = f"test_format_{format_ext}_{bitrate or 'default'}_{int(time.time())}.wav"
            
            wav_output = tts_model.infer(
                spk_audio_prompt="examples/voice_01.wav",
                text=test_text,
                output_path=temp_wav,
                verbose=False
            )
            
            if format_ext == "wav":
                # No conversion needed
                final_output = wav_output
                results[format_name] = "✅ 成功"
            else:
                # Convert format
                format_converter = enhanced_webui.get_format_converter()
                final_output = format_converter.convert_to_format(
                    wav_output,
                    format_ext,
                    bitrate=bitrate if bitrate else 64
                )
                
                if os.path.exists(final_output):
                    results[format_name] = "✅ 成功"
                    # Clean up WAV if conversion successful
                    if os.path.exists(wav_output):
                        os.remove(wav_output)
                else:
                    results[format_name] = "❌ 失败"
                    final_output = wav_output
            
            # Clean up final output
            if os.path.exists(final_output):
                final_size = os.path.getsize(final_output)
                print(f"   • 文件大小: {final_size} bytes")
                os.remove(final_output)
            
        except Exception as e:
            results[format_name] = f"❌ 错误: {str(e)}"
            print(f"   • 错误: {e}")
    
    # Summary
    print(f"\n📊 格式转换测试结果:")
    for format_name, result in results.items():
        print(f"   • {format_name}: {result}")
    
    success_count = sum(1 for result in results.values() if result.startswith("✅"))
    total_count = len(results)
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count == total_count

if __name__ == "__main__":
    print("开始WebUI格式转换流程测试...\n")
    
    # Test complete WebUI flow
    webui_ok = simulate_webui_generation_with_mp3()
    
    if webui_ok:
        print("\n✅ WebUI流程测试通过!")
        
        # Test multiple formats
        formats_ok = test_multiple_formats()
        
        if formats_ok:
            print("\n🎉 所有格式转换测试通过!")
            sys.exit(0)
        else:
            print("\n⚠️  部分格式转换测试失败")
            sys.exit(1)
    else:
        print("\n❌ WebUI流程测试失败!")
        sys.exit(1)