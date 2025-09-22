#!/usr/bin/env python3
"""
测试完整的WebUI MP3生成流程
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def simulate_complete_webui_flow():
    """完全模拟webui.py中的MP3生成流程"""
    
    print("=== 完整WebUI MP3生成流程测试 ===")
    
    try:
        # Import required modules (as in webui.py)
        from indextts.infer_v2 import IndexTTS2
        from indextts.enhanced_webui import EnhancedWebUI
        
        print("✅ 模块导入成功")
        
        # Ensure outputs directory exists
        outputs_dir = "outputs"
        if not os.path.exists(outputs_dir):
            os.makedirs(outputs_dir)
        
        # Simulate user inputs (as received by webui.py)
        text = "这是一个完整的WebUI MP3生成流程测试。我们将验证从文本输入到MP3输出的整个过程。"
        voice_prompt = "examples/voice_01.wav"
        output_format = "MP3"  # User selection
        mp3_bitrate = 128      # User selection
        auto_save = False
        filename_preview = None
        
        print(f"用户输入参数:")
        print(f"  • 文本长度: {len(text)} 字符")
        print(f"  • 语音样本: {voice_prompt}")
        print(f"  • 输出格式: {output_format}")
        print(f"  • MP3比特率: {mp3_bitrate} kbps")
        print(f"  • 自动保存: {auto_save}")
        
        # Initialize TTS model (as in webui.py)
        print("\n初始化TTS模型...")
        tts = IndexTTS2()
        print("✅ TTS模型初始化完成")
        
        # Determine output format and path (exactly as in webui.py)
        format_ext = output_format.lower() if output_format else "wav"
        
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
        
        print(f"\n路径配置:")
        print(f"  • 最终输出路径: {output_path}")
        print(f"  • 临时WAV路径: {temp_output}")
        
        # Simulate progress callback
        last_progress = 0.0
        def _progress_cb(value, desc=None):
            nonlocal last_progress
            try:
                last_progress = float(value) if value is not None else last_progress
            except Exception:
                pass
            print(f"   进度: {last_progress*100:.1f}% - {desc or 'Processing'}")
        
        # Run TTS inference (exactly as in webui.py)
        print(f"\n🎵 开始TTS推理...")
        start_ts = time.time()
        
        # Hook progress callback into TTS engine
        tts.gr_progress = _progress_cb
        
        # Simulate the threading approach used in webui.py
        done_event = threading.Event()
        result_holder = {'path': None, 'err': None}
        
        def _run_infer():
            try:
                result_holder['path'] = tts.infer(
                    spk_audio_prompt=voice_prompt, 
                    text=text,
                    output_path=temp_output,
                    verbose=False
                )
            except Exception as e:
                result_holder['err'] = str(e)
            finally:
                done_event.set()
        
        worker = threading.Thread(target=_run_infer, daemon=True)
        worker.start()
        
        # Wait for completion
        while not done_event.is_set():
            time.sleep(0.1)
        
        if result_holder['err']:
            print(f"❌ 音频生成失败: {result_holder['err']}")
            return False
        
        output = result_holder['path']
        generation_time = time.time() - start_ts
        print(f"✅ 音频生成完成，耗时: {generation_time:.2f}秒")
        
        # Verify WAV output
        if not os.path.exists(output):
            print(f"❌ WAV文件未生成: {output}")
            return False
        
        wav_size = os.path.getsize(output)
        print(f"   • WAV文件大小: {wav_size} bytes")
        
        # Convert format if needed (exactly as in webui.py)
        if format_ext != "wav" and output:
            try:
                conversion_start_time = time.time()
                print(f"\n🔄 开始格式转换...")
                
                enhanced_webui_instance = EnhancedWebUI()
                format_converter = enhanced_webui_instance.get_format_converter()
                
                if format_ext == "mp3":
                    print(f"🔄 转换为 MP3 格式 (比特率: {mp3_bitrate} kbps)...")
                    final_output = format_converter.convert_to_format(
                        output, "mp3", 
                        bitrate=int(mp3_bitrate),
                        output_path=output_path
                    )
                else:
                    final_output = output
                
                # Remove temp WAV file if conversion was successful
                if final_output != output and os.path.exists(output):
                    os.remove(output)
                    print(f"   🧹 清理临时WAV文件: {output}")
                
                conversion_time = time.time() - conversion_start_time
                print(f"✅ 格式转换完成，耗时: {conversion_time:.2f}秒")
                
                output = final_output
                
            except Exception as e:
                print(f"❌ 格式转换失败: {e}")
                # Keep original WAV output
                return False
        
        # Final summary (as in webui.py)
        total_time = time.time() - start_ts
        print(f"\n" + "=" * 50)
        print(f"🎉 音频生成流程完成!")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        if output:
            print(f"📁 输出文件: {os.path.basename(output)}")
            print(f"📁 完整路径: {output}")
        print("=" * 50)
        
        # Verify final output
        success = True
        if os.path.exists(output):
            final_size = os.path.getsize(output)
            final_ext = os.path.splitext(output)[1].lower()
            output_dir = os.path.dirname(os.path.abspath(output))
            expected_dir = os.path.abspath(outputs_dir)
            
            print(f"\n📊 最终验证:")
            print(f"   • 文件存在: ✅")
            print(f"   • 文件格式: {final_ext}")
            print(f"   • 文件大小: {final_size} bytes")
            print(f"   • 输出目录: {output_dir}")
            print(f"   • 期望目录: {expected_dir}")
            
            if final_ext == f'.{format_ext}':
                print(f"   ✅ 格式正确")
            else:
                print(f"   ❌ 格式错误，期望: .{format_ext}")
                success = False
            
            if output_dir == expected_dir:
                print(f"   ✅ 保存位置正确")
            else:
                print(f"   ❌ 保存位置错误")
                success = False
            
            if format_ext == "mp3":
                compression_ratio = (wav_size - final_size) / wav_size * 100 if wav_size > 0 else 0
                print(f"   • 压缩率: {compression_ratio:.1f}%")
            
            # Clean up test file
            os.remove(output)
            print(f"   🧹 清理测试文件: {os.path.basename(output)}")
            
        else:
            print(f"\n❌ 最终输出文件不存在: {output}")
            success = False
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_formats():
    """测试不同格式的输出"""
    
    print("\n=== 测试不同格式输出 ===")
    
    formats_to_test = [
        ("wav", None),
        ("mp3", 64),
        ("mp3", 128),
        ("mp3", 192)
    ]
    
    results = {}
    
    for format_ext, bitrate in formats_to_test:
        format_name = format_ext.upper()
        if bitrate:
            format_name += f" ({bitrate}kbps)"
        
        print(f"\n--- 测试格式: {format_name} ---")
        
        try:
            from indextts.infer_v2 import IndexTTS2
            from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
            
            # Quick test
            tts = IndexTTS2()
            test_text = f"测试{format_name}格式输出。"
            
            # Generate paths
            timestamp = int(time.time())
            if format_ext == "wav":
                output_path = os.path.join("outputs", f"test_{format_ext}_{timestamp}.wav")
                temp_output = output_path
            else:
                output_path = os.path.join("outputs", f"test_{format_ext}_{bitrate}_{timestamp}.{format_ext}")
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                temp_output = os.path.join("outputs", f"{base_name}.wav")
            
            # Generate WAV
            wav_result = tts.infer(
                spk_audio_prompt="examples/voice_01.wav",
                text=test_text,
                output_path=temp_output,
                verbose=False
            )
            
            if format_ext == "wav":
                final_result = wav_result
                results[format_name] = "✅ 成功"
            else:
                # Convert format
                enhanced_webui_instance = EnhancedWebUI()
                format_converter = enhanced_webui_instance.get_format_converter()
                final_result = format_converter.convert_to_format(
                    wav_result, format_ext,
                    bitrate=bitrate if bitrate else 64,
                    output_path=output_path
                )
                
                if os.path.exists(final_result):
                    results[format_name] = "✅ 成功"
                    # Clean up WAV
                    if os.path.exists(wav_result):
                        os.remove(wav_result)
                else:
                    results[format_name] = "❌ 失败"
                    final_result = wav_result
            
            # Verify and clean up
            if os.path.exists(final_result):
                file_size = os.path.getsize(final_result)
                file_dir = os.path.dirname(os.path.abspath(final_result))
                expected_dir = os.path.abspath("outputs")
                
                print(f"   • 文件大小: {file_size} bytes")
                print(f"   • 保存位置: {'✅' if file_dir == expected_dir else '❌'}")
                
                os.remove(final_result)
            
        except Exception as e:
            results[format_name] = f"❌ 错误: {str(e)}"
            print(f"   • 错误: {e}")
    
    # Summary
    print(f"\n📊 格式测试结果:")
    for format_name, result in results.items():
        print(f"   • {format_name}: {result}")
    
    success_count = sum(1 for result in results.values() if result.startswith("✅"))
    total_count = len(results)
    
    return success_count == total_count

if __name__ == "__main__":
    print("开始完整WebUI MP3生成流程测试...\n")
    
    # Test complete WebUI flow
    webui_ok = simulate_complete_webui_flow()
    
    if webui_ok:
        print("\n✅ 完整WebUI流程测试通过!")
        
        # Test different formats
        formats_ok = test_different_formats()
        
        if formats_ok:
            print("\n🎉 所有测试通过! WebUI MP3生成功能完全正常!")
            sys.exit(0)
        else:
            print("\n⚠️  部分格式测试失败")
            sys.exit(1)
    else:
        print("\n❌ WebUI流程测试失败!")
        sys.exit(1)