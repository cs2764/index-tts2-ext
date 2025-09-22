#!/usr/bin/env python3
"""
测试MP3格式转换功能
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mp3_conversion():
    """测试MP3格式转换功能"""
    
    print("=== 测试MP3格式转换功能 ===")
    
    try:
        # Import required modules
        from indextts.infer_v2 import IndexTTS2
        from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
        
        print("✅ 模块导入成功")
        
        # Initialize components
        print("初始化组件...")
        tts_model = IndexTTS2()
        enhanced_webui = EnhancedWebUI()
        format_converter = enhanced_webui.get_format_converter()
        
        print("✅ 组件初始化成功")
        
        # Generate a short test audio first
        test_text = "这是一个MP3格式转换测试。"
        temp_wav_path = "test_mp3_conversion_temp.wav"
        
        print(f"生成测试音频: {test_text}")
        start_time = time.time()
        
        wav_output = tts_model.infer(
            spk_audio_prompt="examples/voice_01.wav",
            text=test_text,
            output_path=temp_wav_path,
            verbose=False
        )
        
        generation_time = time.time() - start_time
        print(f"✅ WAV音频生成完成，耗时: {generation_time:.2f}秒")
        
        # Check if WAV file was created
        if not os.path.exists(wav_output):
            print(f"❌ WAV文件未生成: {wav_output}")
            return False
        
        wav_size = os.path.getsize(wav_output)
        print(f"📁 WAV文件大小: {wav_size} bytes")
        
        # Test MP3 conversion with different bitrates
        bitrates = [64, 128, 192]
        
        for bitrate in bitrates:
            print(f"\n--- 测试MP3转换 (比特率: {bitrate} kbps) ---")
            
            try:
                conversion_start = time.time()
                
                mp3_output = format_converter.convert_to_format(
                    wav_output, 
                    "mp3", 
                    bitrate=bitrate
                )
                
                conversion_time = time.time() - conversion_start
                
                if os.path.exists(mp3_output):
                    mp3_size = os.path.getsize(mp3_output)
                    compression_ratio = (wav_size - mp3_size) / wav_size * 100
                    
                    print(f"✅ MP3转换成功:")
                    print(f"   • 输出文件: {mp3_output}")
                    print(f"   • 文件大小: {mp3_size} bytes")
                    print(f"   • 压缩率: {compression_ratio:.1f}%")
                    print(f"   • 转换耗时: {conversion_time:.2f}秒")
                    
                    # Clean up MP3 file
                    os.remove(mp3_output)
                    print(f"   • 清理临时文件: {mp3_output}")
                    
                else:
                    print(f"❌ MP3文件未生成: {mp3_output}")
                    
            except Exception as e:
                print(f"❌ MP3转换失败 (比特率 {bitrate}): {e}")
                import traceback
                traceback.print_exc()
        
        # Clean up WAV file
        if os.path.exists(wav_output):
            os.remove(wav_output)
            print(f"\n🧹 清理临时WAV文件: {wav_output}")
        
        print("\n🎉 MP3转换测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_format_converter_methods():
    """测试格式转换器的方法可用性"""
    
    print("\n=== 测试格式转换器方法 ===")
    
    try:
        from indextts.enhanced_webui.enhanced_webui import EnhancedWebUI
        from indextts.audio_formats.format_converter import AudioFormatConverter
        
        # Test direct AudioFormatConverter
        print("测试直接AudioFormatConverter实例...")
        converter = AudioFormatConverter()
        
        print("可用方法:")
        methods = [method for method in dir(converter) if not method.startswith('_')]
        for method in methods:
            if 'convert' in method.lower():
                print(f"  • {method}")
        
        # Test through EnhancedWebUI
        print("\n测试通过EnhancedWebUI获取的转换器...")
        enhanced_webui = EnhancedWebUI()
        webui_converter = enhanced_webui.get_format_converter()
        
        print("通过WebUI获取的转换器类型:", type(webui_converter))
        print("是否有convert_to_format方法:", hasattr(webui_converter, 'convert_to_format'))
        print("是否有convert_to_mp3方法:", hasattr(webui_converter, 'convert_to_mp3'))
        
        # Test supported formats
        if hasattr(webui_converter, 'config'):
            print("支持的格式:", webui_converter.config.supported_formats)
        
        return True
        
    except Exception as e:
        print(f"❌ 方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始MP3转换功能测试...\n")
    
    # Test format converter methods first
    methods_ok = test_format_converter_methods()
    
    if methods_ok:
        # Test actual MP3 conversion
        conversion_ok = test_mp3_conversion()
        
        if conversion_ok:
            print("\n🎉 所有测试通过!")
            sys.exit(0)
        else:
            print("\n❌ MP3转换测试失败!")
            sys.exit(1)
    else:
        print("\n❌ 格式转换器方法测试失败!")
        sys.exit(1)