import json
import os
import sys
import threading
import time

import warnings

import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

# Import enhanced WebUI components
from indextts.enhanced_webui import EnhancedWebUI, WebUIComponents
from indextts.enhanced_webui.ui_theme_manager import get_theme_manager
from indextts.enhanced_webui.enhanced_ui_components import EnhancedUIComponents
from indextts.enhanced_webui.ui_theme import create_status_message, create_chapter_preview
from indextts.file_processing import FilePreviewGenerator

import argparse

def format_time(seconds):
    """
    将秒数格式化为"X小时Y分钟Z秒"的格式
    
    Args:
        seconds (float): 秒数
        
    Returns:
        str: 格式化的时间字符串
    """
    if seconds < 0:
        return "0秒"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or not parts:  # 如果没有小时和分钟，至少显示秒
        parts.append(f"{secs}秒")
    
    return "".join(parts)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IndexTTS WebUI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose mode")
    parser.add_argument("--port", type=int, default=7863, help="Port to run the web UI on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the web UI on")
    parser.add_argument("--model_dir", type=str, default="./checkpoints", help="Model checkpoints directory")
    parser.add_argument("--fp16", action="store_true", default=True, help="Use FP16 for inference if available")
    parser.add_argument("--deepspeed", action="store_true", default=False, help="Use DeepSpeed to accelerate if available")
    parser.add_argument("--cuda_kernel", action="store_true", default=False, help="Use CUDA kernel for inference if available")
    parser.add_argument("--gui_seg_tokens", type=int, default=120, help="GUI: Max tokens per generation segment")
    return parser.parse_args()

# Only parse args if running as main module
if __name__ == "__main__":
    cmd_args = parse_args()
else:
    # Default args for testing
    class DefaultArgs:
        verbose = False
        port = 7863
        host = "0.0.0.0"
        model_dir = "./checkpoints"
        fp16 = True
        deepspeed = False
        cuda_kernel = True
        gui_seg_tokens = 120
    cmd_args = DefaultArgs()

if not os.path.exists(cmd_args.model_dir):
    print(f"Model directory {cmd_args.model_dir} does not exist. Please download the model first.")
    sys.exit(1)

for file in [
    "bpe.model",
    "gpt.pth",
    "config.yaml",
    "s2mel.pth",
    "wav2vec2bert_stats.pt"
]:
    file_path = os.path.join(cmd_args.model_dir, file)
    if not os.path.exists(file_path):
        print(f"Required file {file_path} does not exist. Please download it.")
        sys.exit(1)

import gradio as gr
from indextts.infer_v2 import IndexTTS2
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto(language="Auto")
MODE = 'local'
tts = IndexTTS2(model_dir=cmd_args.model_dir,
                cfg_path=os.path.join(cmd_args.model_dir, "config.yaml"),
                use_fp16=cmd_args.fp16,
                use_deepspeed=cmd_args.deepspeed,
                use_cuda_kernel=cmd_args.cuda_kernel,
                )
# 支持的语言列表
LANGUAGES = {
    "中文": "zh_CN",
    "English": "en_US"
}
EMO_CHOICES = [i18n("与音色参考音频相同"),
                i18n("使用情感参考音频"),
                i18n("使用情感向量控制"),
                i18n("使用情感描述文本控制")]
EMO_CHOICES_BASE = EMO_CHOICES[:3]  # 基础选项
EMO_CHOICES_EXPERIMENTAL = EMO_CHOICES  # 全部选项（包括文本描述）

os.makedirs("outputs",exist_ok=True)
os.makedirs("prompts",exist_ok=True)

# Initialize enhanced WebUI
enhanced_webui = EnhancedWebUI()
# Pass the TTS engine to enable background integration inside components
webui_components = EnhancedUIComponents(enhanced_webui, tts)
file_preview_generator = FilePreviewGenerator()

MAX_LENGTH_TO_USE_SPEED = 70
with open("examples/cases.jsonl", "r", encoding="utf-8") as f:
    example_cases = []
    for line in f:
        line = line.strip()
        if not line:
            continue
        example = json.loads(line)
        if example.get("emo_audio",None):
            emo_audio_path = os.path.join("examples",example["emo_audio"])
        else:
            emo_audio_path = None
        example_cases.append([os.path.join("examples", example.get("prompt_audio", "sample_prompt.wav")),
                              EMO_CHOICES[example.get("emo_mode",0)],
                              example.get("text"),
                             emo_audio_path,
                             example.get("emo_weight",1.0),
                             example.get("emo_text",""),
                             example.get("emo_vec_1",0),
                             example.get("emo_vec_2",0),
                             example.get("emo_vec_3",0),
                             example.get("emo_vec_4",0),
                             example.get("emo_vec_5",0),
                             example.get("emo_vec_6",0),
                             example.get("emo_vec_7",0),
                             example.get("emo_vec_8",0),
                             example.get("emo_text") is not None]
                             )

def normalize_emo_vec(emo_vec):
    # emotion factors for better user experience
    k_vec = [0.75,0.70,0.80,0.80,0.75,0.75,0.55,0.45]
    tmp = np.array(k_vec) * np.array(emo_vec)
    if np.sum(tmp) > 0.8:
        tmp = tmp * 0.8/ np.sum(tmp)
    return tmp.tolist()

def process_uploaded_file(file_path, use_native_chapters, file_cleaning_enabled, chapter_recognition_enabled):
    """Process uploaded file with new toggle system."""
    if not file_path:
        error_html = create_status_message("No file uploaded", "error")
        return "", gr.update(value=error_html, visible=True), gr.update(visible=False)
    
    try:
        # Get file processor
        file_processor = enhanced_webui.get_file_processor()
        
        # Process the file with new toggle system
        processed_file = file_processor.process_file(
            file_path,
            use_native_chapters=use_native_chapters,
            enable_text_processing=file_cleaning_enabled,
            enable_chapter_recognition=chapter_recognition_enabled,
            text_processing_options={
                'merge_empty_lines': True,
                'remove_extra_spaces': True,
                'smart_sentence_break': True,
                'clean_special_chars': True
            }
        )
        
        # Update status
        message = f"""<strong>✅ File processed successfully</strong><br>
            <small>File: {processed_file.filename}<br>
            Encoding: {processed_file.original_encoding}<br>
            Content length: {len(processed_file.content)} characters<br>
            Chapters detected: {len(processed_file.chapters) if processed_file.chapters else 0}</small>"""
        status_html = create_status_message(message, "success")
        
        return processed_file.content, gr.update(value=status_html, visible=True), gr.update(visible=False)
        
    except Exception as e:
        message = f"<strong>❌ Error processing file</strong><br><small>{str(e)}</small>"
        error_html = create_status_message(message, "error")
        return "", gr.update(value=error_html, visible=True), gr.update(visible=False)

def on_file_upload(file_path):
    """Handle file upload event with preview generation."""
    if not file_path:
        return (
            gr.update(visible=False),  # file_status
            gr.update(visible=False),  # use_native_chapters
            gr.update(visible=False)   # file_preview
        )
    
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Generate preview based on file type
        if file_ext == '.epub':
            preview = file_preview_generator.generate_epub_preview(file_path)
            preview_html = file_preview_generator.format_preview_display(preview)
            
            status_html = create_status_message("✅ EPUB文件已上传并生成预览", "success")
            
            return (
                gr.update(value=status_html, visible=True),  # file_status
                gr.update(visible=True),   # use_native_chapters (show for EPUB)
                gr.update(value=preview_html, visible=True)  # file_preview
            )
            
        elif file_ext == '.txt':
            # Use the new preview method that supports cleaning
            preview = file_preview_generator.generate_text_preview(file_path)
            preview_html = file_preview_generator.format_preview_display(preview)
            
            status_html = create_status_message("✅ TXT文件已上传并生成预览", "success")
            
            return (
                gr.update(value=status_html, visible=True),  # file_status
                gr.update(visible=False),  # use_native_chapters (hide for TXT)
                gr.update(value=preview_html, visible=True)  # file_preview
            )
            
        else:
            # Unsupported file type
            error_html = create_status_message(f"❌ 不支持的文件类型: {file_ext}", "error")
            
            return (
                gr.update(value=error_html, visible=True),  # file_status
                gr.update(visible=False),  # use_native_chapters
                gr.update(visible=False)   # file_preview
            )
            
    except Exception as e:
        error_html = create_status_message(f"❌ 文件处理错误: {str(e)}", "error")
        
        return (
            gr.update(value=error_html, visible=True),  # file_status
            gr.update(visible=False),  # use_native_chapters
            gr.update(visible=False)   # file_preview
        )

def on_file_cleaning_change(file_cleaning_enabled, file_path):
    """Handle file cleaning toggle change and regenerate preview with cleaning results."""
    if not file_path:
        return gr.update(visible=False)
    
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.txt':
            # Generate preview with cleaning if enabled
            if file_cleaning_enabled:
                preview = file_preview_generator.generate_text_preview_with_cleaning(file_path, enable_cleaning=True)
            else:
                preview = file_preview_generator.generate_text_preview(file_path)
            
            preview_html = file_preview_generator.format_preview_display(preview)
            return gr.update(value=preview_html, visible=True)
        
        elif file_ext == '.epub':
            # EPUB files don't support text cleaning in preview
            preview = file_preview_generator.generate_epub_preview(file_path)
            preview_html = file_preview_generator.format_preview_display(preview)
            return gr.update(value=preview_html, visible=True)
        
        else:
            return gr.update(visible=False)
            
    except Exception as e:
        error_html = create_status_message(f"❌ 预览生成错误: {str(e)}", "error")
        return gr.update(value=error_html, visible=True)



def on_chapter_recognition_change(enabled, file_path):
    """Handle chapter recognition toggle change and generate preview."""
    if not enabled or not file_path:
        return gr.update(visible=False)
    
    try:
        # Import SmartChapterParser
        from indextts.chapter_parsing import SmartChapterParser
        
        # Read file content
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.txt':
            # Detect encoding and read text file
            preview = file_preview_generator.generate_text_preview(file_path)
            text_content = preview.preview_text
            
            # For full chapter detection, read entire file
            with open(file_path, 'r', encoding=preview.encoding, errors='replace') as f:
                full_text = f.read()
        
        elif file_ext == '.epub':
            # Extract EPUB content
            try:
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                
                book = epub.read_epub(file_path)
                text_content = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        text = soup.get_text()
                        if text.strip():
                            text_content.append(text.strip())
                
                full_text = '\n'.join(text_content)
                
            except ImportError:
                error_html = create_status_message("需要安装 ebooklib 和 beautifulsoup4 来处理 EPUB 文件", "error")
                return gr.update(value=error_html, visible=True)
        else:
            return gr.update(visible=False)
        
        # Parse chapters using SmartChapterParser
        parser = SmartChapterParser()
        chapters = parser.parse(full_text)
        
        # Generate enhanced chapter preview HTML with detailed info
        if chapters:
            import html
            
            # Create detailed chapter preview with count and titles using better colors
            chapter_info_html = f"""
            <div style='background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 15px; border-radius: 8px 8px 0 0; margin-bottom: 0;'>
                <h4 style='margin: 0 0 8px 0; color: white; font-size: 16px;'>📚 章节识别结果</h4>
                <p style='margin: 0; font-weight: bold; font-size: 14px;'>共识别到 {len(chapters)} 个章节</p>
            </div>
            <div style='max-height: 350px; overflow-y: auto; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px; padding: 0; background: #f8f9fa;'>
            """
            
            for i, chapter in enumerate(chapters[:10], 1):  # Show first 10 chapters
                title = chapter.title if hasattr(chapter, 'title') else str(chapter)
                # Escape HTML and truncate long titles
                title = html.escape(title)
                if len(title) > 60:
                    title = title[:57] + "..."
                
                confidence = getattr(chapter, 'confidence_score', 0.8)
                
                # Better confidence color scheme
                if confidence > 0.8:
                    confidence_color = "#28a745"
                    confidence_text = "高"
                elif confidence > 0.6:
                    confidence_color = "#ffc107"
                    confidence_text = "中"
                else:
                    confidence_color = "#dc3545"
                    confidence_text = "低"
                
                chapter_info_html += f"""
                <div style='margin: 8px; padding: 12px; background: white; border-radius: 6px; border-left: 4px solid {confidence_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                    <div style='color: #212529; font-weight: bold; margin-bottom: 4px;'>第 {i} 章: {title}</div>
                    <div style='font-size: 12px; color: #6c757d;'>
                        置信度: <span style='color: {confidence_color}; font-weight: bold;'>{confidence:.2f} ({confidence_text})</span>
                    </div>
                </div>
                """
            
            if len(chapters) > 10:
                chapter_info_html += f"""
                <div style='text-align: center; padding: 15px; color: #6c757d; font-style: italic; background: #e9ecef; margin: 8px; border-radius: 6px;'>
                    ... 还有 {len(chapters) - 10} 个章节
                </div>
                """
            
            chapter_info_html += "</div>"
            
            return gr.update(value=chapter_info_html, visible=True)
        else:
            no_chapters_html = create_status_message(
                "<strong>⚠️ 未检测到章节</strong><br><small>可能需要调整章节识别设置或文件不包含明显的章节结构</small>", 
                "warning"
            )
            return gr.update(value=no_chapters_html, visible=True)
            
    except Exception as e:
        error_html = create_status_message(
            f"<strong>❌ 章节检测错误</strong><br><small>{str(e)}</small>",
            "error"
        )
        return gr.update(value=error_html, visible=True)

def on_format_change(format_selection):
    """Handle audio format selection change."""
    if format_selection == "MP3":
        return gr.update(visible=True)  # Show MP3 bitrate slider
    else:
        return gr.update(visible=False)  # Hide MP3 bitrate slider

def on_segmentation_change(enabled):
    """Handle segmentation checkbox change."""
    return gr.update(visible=enabled)  # Show/hide chapters per file slider

def update_segmentation_availability(file_path, chapter_recognition_enabled):
    """Update segmentation availability based on file type and chapter recognition settings."""
    if not file_path:
        return gr.update(visible=False, interactive=False)
    
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
    
    # Check if segmentation is available
    is_available = webui_components.is_segmentation_available(file_ext, chapter_recognition_enabled)
    
    if is_available:
        return gr.update(visible=True, interactive=True)
    else:
        return gr.update(visible=True, interactive=False, value=False)

def update_filename_preview(voice_selection, output_format, file_upload_path=None):
    """Update filename preview based on current settings."""
    try:
        # Extract voice name from selection
        voice_name = "unknown"
        if voice_selection:
            voice_name = os.path.splitext(os.path.basename(voice_selection))[0]
        
        # Extract source filename if available
        source_filename = None
        if file_upload_path:
            source_filename = os.path.splitext(os.path.basename(file_upload_path))[0]
        
        # Generate filename
        filename = webui_components.update_filename_preview(
            source_filename, voice_name, output_format.lower() if output_format else "wav"
        )
        
        return gr.update(value=filename)
        
    except Exception as e:
        return gr.update(value=f"Error: {str(e)}")

def refresh_voice_samples():
    """Refresh voice sample dropdown and update preview."""
    try:
        updated_dropdown, status_html = webui_components.refresh_voice_samples()
        
        # After refreshing, auto-update the voice preview to the first available sample
        samples = enhanced_webui.get_voice_manager().get_available_samples()
        preview_path = samples[0].filepath if samples else None
        preview_update = gr.update(value=preview_path, visible=True if preview_path else False)
        
        return updated_dropdown, status_html, preview_update
    except Exception as e:
        error_html = gr.HTML(
            value=create_status_message(f"Error refreshing samples: {str(e)}", "error")
        )
        # Hide preview on error
        return gr.Dropdown(choices=[], value=None), error_html, gr.update(value=None, visible=False)


def on_voice_sample_change(voice_path):
    """Update the inline preview when a voice sample is selected."""
    if voice_path:
        return gr.update(value=voice_path, visible=True)
    return gr.update(value=None, visible=False)

def gen_single(emo_control_method, voice_selection, prompt, text,
               emo_ref_path, emo_weight,
               vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8,
               emo_text,emo_random,
               output_format, mp3_bitrate, enable_segmentation, chapters_per_file,
               auto_save, filename_preview,
               file_upload_path, file_cleaning_enabled, chapter_recognition_enabled,
               incremental_auto_save_enabled, incremental_auto_save_interval,
               max_text_tokens_per_segment=120,
                *args, progress=gr.Progress()):
    # Automatic file processing if file is uploaded
    processed_text = text
    chapters_info = []
    
    if file_upload_path and (file_cleaning_enabled or chapter_recognition_enabled):
        try:
            import time
            from indextts.file_processing.console_feedback import ProcessingFeedbackManager
            from indextts.file_processing import FileProcessor, FileProcessingConfig
            
            start_time = time.time()
            progress(0.05, "正在读取文件...")
            
            # Create console callback for real-time feedback
            console_messages = []
            def console_callback(message):
                console_messages.append(message)
                print(message)  # Also print to console for immediate feedback
            
            # Create file processor with console feedback
            config = FileProcessingConfig.default()
            config.text_cleaning_enabled = file_cleaning_enabled
            file_processor = FileProcessor(config, console_callback)
            
            if file_cleaning_enabled:
                progress(0.1, "正在进行文件清理...")
            
            if chapter_recognition_enabled:
                progress(0.15, "正在识别章节结构...")
            
            # Process the file with detailed feedback
            processed_file = file_processor.process_file(
                file_upload_path,
                use_native_chapters=not chapter_recognition_enabled  # Use native chapters when smart recognition is disabled
            )
            
            # Use processed content if available, otherwise use original text
            if processed_file and processed_file.content:
                processed_text = processed_file.content
                chapters_info = processed_file.chapters if processed_file.chapters else []
                
                # Process chapters if chapter recognition is enabled
                if chapter_recognition_enabled and not chapters_info:
                    from indextts.chapter_parsing import SmartChapterParser
                    
                    # Create chapter parser with console feedback
                    chapter_parser = SmartChapterParser(console_callback=console_callback)
                    chapters_info = chapter_parser.parse_with_feedback(processed_text, file_processor.feedback_manager)
                    
                    # Update processed file with chapters
                    processed_file.chapters = chapters_info
                
                # Display processing summary from feedback manager
                if hasattr(processed_file, 'metadata') and 'processing_summary' in processed_file.metadata:
                    summary = processed_file.metadata['processing_summary']
                    
                    print("\n" + "=" * 60)
                    print("📄 文件处理完成摘要")
                    print("=" * 60)
                    
                    # File info
                    print(f"📁 文件名: {processed_file.filename}")
                    print(f"📊 编码: {processed_file.original_encoding}")
                    
                    # File size changes
                    file_stats = summary.get('file_stats', {})
                    original_size = file_stats.get('original_size', 0)
                    processed_size = file_stats.get('processed_size', 0)
                    size_change = file_stats.get('size_change', 0)
                    
                    print(f"📏 文件大小: {original_size:,} → {processed_size:,} 字节 ({size_change:+,})")
                    
                    # Line count changes
                    original_lines = file_stats.get('original_lines', 0)
                    processed_lines = file_stats.get('processed_lines', 0)
                    line_change = file_stats.get('line_change', 0)
                    
                    print(f"📝 行数: {original_lines:,} → {processed_lines:,} 行 ({line_change:+,})")
                    
                    # Cleaning statistics
                    if file_cleaning_enabled:
                        cleaning_stats = summary.get('cleaning_stats', {})
                        print(f"\n🧹 文件清理统计:")
                        
                        if cleaning_stats.get('excess_spaces_removed', 0) > 0:
                            print(f"   • 处理了 {cleaning_stats['excess_spaces_removed']:,} 个多余空格")
                        if cleaning_stats.get('empty_lines_merged', 0) > 0:
                            print(f"   • 合并了 {cleaning_stats['empty_lines_merged']:,} 个空行")
                        if cleaning_stats.get('special_characters_removed', 0) > 0:
                            print(f"   • 清理了 {cleaning_stats['special_characters_removed']:,} 个特殊字符")
                        if cleaning_stats.get('invisible_characters_removed', 0) > 0:
                            print(f"   • 移除了 {cleaning_stats['invisible_characters_removed']:,} 个不可见字符")
                        if cleaning_stats.get('sentences_broken', 0) > 0:
                            print(f"   • 分割了 {cleaning_stats['sentences_broken']:,} 个长句")
                        
                        # Check if no cleaning was needed
                        total_cleaning = sum(cleaning_stats.values())
                        if total_cleaning == 0:
                            print("   • 文本已经很干净，无需清理")
                    
                    # Chapter recognition statistics
                    if chapter_recognition_enabled:
                        chapter_stats = summary.get('chapter_stats', {})
                        chapters_detected = chapter_stats.get('high_confidence_chapters', 0)
                        
                        print(f"\n📚 章节识别统计:")
                        if chapters_detected > 0:
                            print(f"   • 共识别到 {chapters_detected} 个有效章节")
                            
                            filtered_chapters = chapter_stats.get('filtered_chapters', 0)
                            if filtered_chapters > 0:
                                print(f"   • 过滤了 {filtered_chapters} 个低置信度章节")
                            
                            avg_confidence = chapter_stats.get('average_confidence', 0)
                            if avg_confidence > 0:
                                print(f"   • 平均置信度: {avg_confidence:.2f}")
                            
                            patterns_used = chapter_stats.get('patterns_used', [])
                            if patterns_used:
                                print(f"   • 使用的模式: {', '.join(patterns_used)}")
                            
                            # Show first few chapter titles
                            if chapters_info:
                                print(f"   • 章节预览:")
                                for i, chapter in enumerate(chapters_info[:3], 1):
                                    title = chapter.title[:30] + "..." if len(chapter.title) > 30 else chapter.title
                                    confidence = getattr(chapter, 'confidence_score', 0.8)
                                    print(f"     {i}. {title} (置信度: {confidence:.2f})")
                                if len(chapters_info) > 3:
                                    print(f"     ... 还有 {len(chapters_info) - 3} 个章节")
                        else:
                            print("   • 未检测到明显的章节结构")
                    
                    # Timing information
                    timing = summary.get('timing', {})
                    total_duration = timing.get('total_duration', 0)
                    if total_duration:
                        print(f"\n⏱️  总处理时间: {format_time(total_duration)}")
                        
                        stage_timings = timing.get('stage_timings', {})
                        if stage_timings:
                            print(f"   各阶段耗时:")
                            for stage, duration in stage_timings.items():
                                percentage = (duration / total_duration * 100) if total_duration > 0 else 0
                                print(f"   • {stage}: {format_time(duration)} ({percentage:.1f}%)")
                    
                    print("=" * 60)
            
            progress(0.2, "文件处理完成，开始音频生成...")
            
        except Exception as e:
            print(f"文件处理错误: {str(e)}")
            # Continue with original text if processing fails
            progress(0.2, "文件处理失败，使用原始文本...")
    
    # Use processed text for generation
    text = processed_text
    
    # Determine voice prompt source
    voice_prompt = voice_selection if voice_selection else prompt
    
    # Validate voice selection
    if not voice_prompt:
        return gr.update(value=None, visible=True)
    
    # Determine output format and path
    format_ext = output_format.lower() if output_format else "wav"
    
    if auto_save and filename_preview:
        # Extract filename from HTML content if it contains HTML tags
        if filename_preview.strip().startswith('<'):
            # Parse HTML to extract the actual filename
            import re
            match = re.search(r'<code>([^<]+)</code>', filename_preview)
            if match:
                actual_filename = match.group(1)
            else:
                # Fallback: generate a new filename
                actual_filename = f"spk_{int(time.time())}.{format_ext}"
        else:
            actual_filename = filename_preview
        
        output_path = os.path.join("outputs", actual_filename)
    else:
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.{format_ext}")
    
    # For TTS generation, always use WAV first, then convert if needed
    temp_output = output_path
    if format_ext != "wav":
        # Generate temporary WAV path for TTS generation
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        temp_output = os.path.join("outputs", f"{base_name}.wav")
    
    # set gradio progress
    tts.gr_progress = progress
    do_sample, top_p, top_k, temperature, \
        length_penalty, num_beams, repetition_penalty, max_mel_tokens = args
    kwargs = {
        "do_sample": bool(do_sample),
        "top_p": float(top_p),
        "top_k": int(top_k) if int(top_k) > 0 else None,
        "temperature": float(temperature),
        "length_penalty": float(length_penalty),
        "num_beams": num_beams,
        "repetition_penalty": float(repetition_penalty),
        "max_mel_tokens": int(max_mel_tokens),
        # "typical_sampling": bool(typical_sampling),
        # "typical_mass": float(typical_mass),
    }
    if type(emo_control_method) is not int:
        emo_control_method = emo_control_method.value
    if emo_control_method == 0:  # emotion from speaker
        emo_ref_path = None  # remove external reference audio
    if emo_control_method == 1:  # emotion from reference audio
        # normalize emo_alpha for better user experience
        emo_weight = emo_weight * 0.8
        pass
    if emo_control_method == 2:  # emotion from custom vectors
        vec = [vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8]
        vec = normalize_emo_vec(vec)
    else:
        # don't use the emotion vector inputs for the other modes
        vec = None

    if emo_text == "":
        # erase empty emotion descriptions; `infer()` will then automatically use the main prompt
        emo_text = None

    print(f"🎛️  情感控制模式: {emo_control_method}, 权重: {emo_weight}, 向量: {vec}")
    
    # Audio generation feedback
    print(f"🎵 开始音频生成...")
    print(f"   • 输出格式: {format_ext.upper()}")
    print(f"   • 文本长度: {len(text):,} 字符")
    if chapters_info:
        print(f"   • 章节数量: {len(chapters_info)}")
    
    # Generate audio (always as WAV first) using background integration when appropriate
    if format_ext == "wav":
        temp_output = output_path
    else:
        # Remove the original extension and add .wav for temporary output
        base_path = os.path.splitext(output_path)[0]
        temp_output = base_path + ".wav"
    
    # Prepare generation parameters for background integration
    generation_kwargs = kwargs
    generation_params = {
        'emo_ref_path': emo_ref_path,
        'emo_weight': emo_weight,
        'emo_vector': vec,
        'use_emo_text': (emo_control_method==3),
        'emo_text': emo_text,
        'use_random': emo_random,
        'max_text_tokens_per_segment': int(max_text_tokens_per_segment),
        'generation_kwargs': generation_kwargs,
        'output_format': format_ext,
        'mp3_bitrate': int(mp3_bitrate) if mp3_bitrate else 64,
        'enable_segmentation': enable_segmentation,
        'chapters_per_file': int(chapters_per_file) if chapters_per_file else 10,
        'verbose': cmd_args.verbose
    }
    
    # Create progress callback compatible with BackgroundTTSIntegration
    def _progress_cb(task_status):
        try:
            progress(task_status.progress, desc=task_status.current_stage)
        except Exception:
            pass
    
    # Console capture for task messages
    status_messages = []
    def _console_cb(message: str):
        status_messages.append(message)
        print(message)
    
    background_tts_integration = webui_components.get_background_tts_integration()
    output = None
    
    # Helper to format seconds
    def _fmt_time(sec: float):
        if sec is None:
            return "?"
        if sec < 60:
            return f"{sec:.1f}s"
        m = int(sec // 60)
        s = sec % 60
        return f"{m}m {s:.1f}s"
    
    # Decide background or synchronous streaming
    use_background = False
    if background_tts_integration:
        try:
            use_background = background_tts_integration.should_use_background_processing(
                text,
                output_format=format_ext,
                enable_segmentation=enable_segmentation
            )
        except Exception:
            use_background = False
    
    # Helper to render a wide progress bar with text
    def _progress_html(percent: float, text: str) -> str:
        pct = max(0.0, min(100.0, percent))
        return f"""
        <div class='generation-progress' style="padding:8px;border:1px solid #dee2e6;border-radius:6px;background:#f8f9fa;">
            <div style="font-size:12px;color:#6c757d;margin-bottom:6px;">{text}</div>
            <div style="width:100%;background:#e9ecef;height:12px;border-radius:6px;overflow:hidden;">
                <div style="width:{pct:.1f}%;height:100%;background:linear-gradient(90deg,#3b82f6,#10b981);transition:width .2s ease;"></div>
            </div>
        </div>
        """.strip()
    
    if background_tts_integration and use_background:
        print(f"🔍 DEBUG: 使用背景 TTS 处理 - webui.py")
        # Queue to background and immediately show status in progress area
        result = background_tts_integration.generate_audio_sync_or_async(
            text=text,
            voice_prompt=voice_prompt,
            output_path=temp_output,
            generation_params=generation_params,
            force_background=True,
            progress_callback=None,
            console_callback=_console_cb
        )
        task_msg = result.get('message', '已进入后台处理')
        return (
            gr.update(value=None, visible=True),
            gr.update(value=_progress_html(0.0, task_msg), visible=True),
            gr.update(value=f"⏳ {task_msg}", visible=True)
        )
    
    # Synchronous streaming path: run infer in a thread and stream status_line updates
    print(f"🔍 DEBUG: 使用同步处理路径 - webui.py")
    import threading
    done_event = threading.Event()
    result_holder = {'path': None, 'err': None}
    start_ts = time.time()
    last_status_line = '0.0% | Stage: Initializing | Elapsed: 0.0s'
    
    def _progress_cb(value, desc=None):
        nonlocal last_status_line, last_progress
        try:
            last_progress = float(value) if value is not None else last_progress
        except Exception:
            pass
        elapsed = time.time() - start_ts
        eta = (elapsed / last_progress - elapsed) if last_progress and last_progress > 0 else None
        parts = [f"{last_progress*100:.1f}%", f"Stage: {desc or 'Generating'}", f"Elapsed: {_fmt_time(elapsed)}"]
        if eta is not None and eta >= 0:
            parts.append(f"ETA: {_fmt_time(eta)}")
        last_status_line = " | ".join(parts)
    
    last_progress = 0.0
    def _run_infer():
        try:
            # Extract voice name and source filename for consistent naming
            voice_name = None
            if voice_selection:
                voice_name = os.path.splitext(os.path.basename(voice_selection))[0]
            
            source_filename = None
            if file_upload_path:
                source_filename = os.path.splitext(os.path.basename(file_upload_path))[0]
            
            # Configure auto-save settings
            if incremental_auto_save_enabled:
                tts.set_auto_save_config(
                    save_interval=int(incremental_auto_save_interval),
                    enabled=True,
                    output_path=temp_output,
                    voice_name=voice_name,
                    source_filename=source_filename
                )
            else:
                tts.set_auto_save_config(
                    save_interval=5,
                    enabled=False,
                    output_path=temp_output,
                    voice_name=voice_name,
                    source_filename=source_filename
                )
            
            # Hook progress callback into TTS engine
            tts.gr_progress = _progress_cb
            result_holder['path'] = tts.infer(
                spk_audio_prompt=voice_prompt, text=text,
                output_path=temp_output,
                emo_audio_prompt=emo_ref_path, emo_alpha=emo_weight,
                emo_vector=vec,
                use_emo_text=(emo_control_method==3), emo_text=emo_text,use_random=emo_random,
                verbose=cmd_args.verbose,
                max_text_tokens_per_segment=int(max_text_tokens_per_segment),
                **kwargs
            )
        except Exception as e:
            result_holder['err'] = str(e)
        finally:
            done_event.set()
    
    worker = threading.Thread(target=_run_infer, daemon=True)
    worker.start()
    
    # Stream progress updates to progress_display while infer is running
    while not done_event.is_set():
        time.sleep(0.25)
    
    if result_holder['err']:
        print(f"❌ 音频生成失败: {result_holder['err']}")
        return (
            gr.update(value=None, visible=True),
            gr.update(value=_progress_html(0.0, f"❌ {result_holder['err']}"), visible=True),
            gr.update(value=f"❌ 音频生成失败", visible=True)
        )
    
    output = result_holder['path']
    generation_time = time.time() - start_ts
    print(f"✅ 音频生成完成，耗时: {format_time(generation_time)}")
    
    # Handle segmentation based on file type and settings
    if enable_segmentation and chapters_info and file_upload_path:
        try:
            # Validate segmentation settings
            file_ext = os.path.splitext(file_upload_path)[1].lower().replace('.', '')
            is_valid, error_msg = webui_components.validate_segmentation_settings(
                chapters_per_file, file_ext, chapter_recognition_enabled
            )
            
            if not is_valid:
                print(f"❌ 分割设置验证失败: {error_msg}")
                # Continue without segmentation
            else:
                progress(0.8, "正在进行章节分割...")
                
                # Get audio segmenter
                audio_segmenter = enhanced_webui.get_audio_segmenter()
                
                # Segment audio based on chapters
                segmentation_start_time = time.time()
                segmented_files = audio_segmenter.segment_by_chapters(
                    output, chapters_info, chapters_per_file
                )
                
                # For segmented output, return the folder path or first file
                if segmented_files:
                    segmentation_time = time.time() - segmentation_start_time
                    output = segmented_files[0] if isinstance(segmented_files, list) else segmented_files
                    file_count = len(segmented_files) if isinstance(segmented_files, list) else 1
                    print(f"✂️  章节分割完成:")
                    print(f"   • 分割为 {file_count} 个文件")
                    print(f"   • 每文件包含 {chapters_per_file} 个章节")
                    print(f"   • 分割耗时: {format_time(segmentation_time)}")
            
        except Exception as e:
            print(f"章节分割失败: {e}")
            # Continue with unsegmented output
    
    # Convert format if needed
    if format_ext != "wav" and output:
        try:
            conversion_start_time = time.time()
            progress(0.9, f"正在转换为 {format_ext.upper()} 格式...")
            
            # Update progress (no longer yielding intermediate results)
            
            format_converter = enhanced_webui.get_format_converter()
            
            if format_ext == "mp3":
                print(f"🔄 开始转换为 MP3 格式...")
                print(f"   🎚️ 比特率设置: {mp3_bitrate} kbps")
                print(f"   📁 源文件: {output}")
                print(f"   📁 目标文件: {output_path}")
                print(f"🔍 DEBUG: 即将调用 format_converter.convert_to_format() - webui.py 第984行")
                
                # Check if source file exists before conversion
                if os.path.exists(output):
                    source_size = os.path.getsize(output)
                    print(f"   📊 源文件大小: {source_size / 1024 / 1024:.2f} MB")
                else:
                    print(f"⚠️  警告: 源文件不存在: {output}")
                
                # Use the original output_path for MP3 conversion
                final_output = format_converter.convert_to_format(
                    output, "mp3", 
                    bitrate=int(mp3_bitrate),
                    output_path=output_path
                )
                print(f"🔍 DEBUG: format_converter.convert_to_format() 调用完成，返回: {final_output}")
                
                # Verify the conversion result
                if final_output == output_path and os.path.exists(output_path):
                    final_size = os.path.getsize(output_path)
                    print(f"✅ MP3 转换验证成功!")
                    print(f"   📁 最终文件: {final_output}")
                    print(f"   📊 最终文件大小: {final_size / 1024 / 1024:.2f} MB")
                elif final_output == output:
                    print(f"⚠️  MP3 转换失败，使用原始 WAV 文件: {final_output}")
                else:
                    print(f"🔄 MP3 转换返回了不同的路径: {final_output}")
            elif format_ext == "m4b":
                print(f"🔄 创建 M4B 有声书格式...")
                if chapters_info:
                    print(f"   • 包含 {len(chapters_info)} 个章节书签")
                    # For M4B, use chapter information from processed file
                    final_output = format_converter.create_m4b_audiobook([output], chapters_info, {})
                else:
                    # Convert to M4B without chapters
                    final_output = format_converter.convert_to_format(output, "m4b")
            else:
                final_output = output
            
            # Remove temp WAV file and cleanup temp directories if conversion was successful
            if final_output != output and os.path.exists(output):
                # Remove the temp WAV file
                os.remove(output)
                print(f"   🧹 清理临时WAV文件: {os.path.basename(output)}")
                
                # Check if the temp file was in a specific folder and clean it up
                temp_dir = os.path.dirname(output)
                if temp_dir != "outputs" and temp_dir != ".":
                    # This is a subdirectory, check if it's empty and remove it
                    try:
                        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                            os.rmdir(temp_dir)
                            print(f"   🧹 清理空的临时文件夹: {temp_dir}")
                    except Exception as e:
                        print(f"   ⚠️  无法清理临时文件夹 {temp_dir}: {e}")
                
                # Also cleanup any auto-save related temp directories
                if hasattr(tts, 'save_manager') and tts.save_manager:
                    try:
                        cleanup_summary = tts.save_manager.cleanup_temp_files(preserve_current=False)
                        if cleanup_summary.get('temp_dir_removed'):
                            print(f"   🧹 清理自动保存临时目录")
                    except Exception as e:
                        print(f"   ⚠️  自动保存清理失败: {e}")
            
            conversion_time = time.time() - conversion_start_time
            print(f"✅ 格式转换完成，耗时: {format_time(conversion_time)}")
            
            output = final_output
            
        except Exception as e:
            print(f"❌ 格式转换失败: {e}")
            # Keep original WAV output
    
    # Final summary
    total_time = time.time() - start_ts
    print("\n" + "=" * 50)
    print("🎉 音频生成流程完成!")
    if total_time > 0:
        print(f"⏱️  总耗时: {format_time(total_time)}")
    if output:
        print(f"📁 输出文件: {os.path.basename(output)}")
    print("=" * 50)
    
    # Return audio output, progress line, and status
    # Enhanced completion message with file details
    completion_message = "✅ 生成完成"
    if output and os.path.exists(output):
        file_size = os.path.getsize(output)
        file_ext = os.path.splitext(output)[1].upper()
        completion_message = f"✅ 生成完成: {os.path.basename(output)} ({file_ext}, {file_size / 1024 / 1024:.2f} MB)"
        
        # Also print detailed completion info to console
        abs_path = os.path.abspath(output)
        print(f"\n🎉 最终生成结果:")
        print(f"   📁 文件路径: {output}")
        print(f"   📂 绝对路径: {abs_path}")
        print(f"   📊 文件大小: {file_size / 1024 / 1024:.2f} MB")
        print(f"   🎵 文件格式: {file_ext}")
        print(f"   ⏱️  总耗时: {total_time:.1f}s")
    elif output:
        completion_message = f"✅ 生成完成: {os.path.basename(output)}"
    
    return (
        gr.update(value=output, visible=True),
        gr.update(value=_progress_html(100.0, f"✅ 完成 | 耗时 {total_time:.1f}s"), visible=True),
        gr.update(value=completion_message, visible=True)
    )

def update_prompt_audio():
    update_button = gr.update(interactive=True)
    return update_button

with gr.Blocks(title="IndexTTS Demo", css=get_theme_manager().get_custom_css()) as demo:
    mutex = threading.Lock()
    gr.HTML('''
    <h2><center>IndexTTS2: A Breakthrough in Emotionally Expressive and Duration-Controlled Auto-Regressive Zero-Shot Text-to-Speech</h2>
<p align="center">
<a href='https://arxiv.org/abs/2506.21619'><img src='https://img.shields.io/badge/ArXiv-2506.21619-red'></a>
</p>
    ''')

    with gr.Tab(i18n("音频生成")):
        # Enhanced file upload section with improved layout
        with gr.Accordion(i18n("📁 文件上传"), open=True) as file_upload_section:
            # File upload and processing options in compact layout
            with gr.Row():
                with gr.Column(scale=3):
                    file_upload = gr.File(
                        label="📁 上传 TXT 或 EPUB 文件",
                        file_types=[".txt", ".epub"],
                        type="filepath",
                        elem_classes=["file-upload-area"]
                    )
                with gr.Column(scale=2):
                    # Compact processing options
                    with gr.Group():
                        gr.Markdown("**处理选项**")
                        file_cleaning_toggle = gr.Checkbox(
                            label="🧹 文件清理",
                            value=True,
                            info="清理多余空格、合并空行等"
                        )
                        chapter_recognition_toggle = gr.Checkbox(
                            label="🔍 智能章节识别",
                            value=False,
                            info="自动识别章节标题和结构"
                        )
                        use_native_chapters = gr.Checkbox(
                            label="使用原生EPUB章节",
                            value=False,
                            visible=False,
                            info="使用EPUB文件的原始章节结构"
                        )
            
            # File processing status
            file_status = gr.HTML(value="", visible=False)
            
            # Enhanced preview sections with better width allocation
            with gr.Row():
                with gr.Column(scale=3):
                    # File content preview with larger width
                    file_preview = gr.HTML(
                        value="",
                        visible=False,
                        label="文件预览",
                        elem_classes=["file-preview-large"]
                    )
                with gr.Column(scale=2):
                    # Chapter detection preview with chapter count info
                    chapter_preview = gr.HTML(
                        value="",
                        visible=False,
                        label="章节预览",
                        elem_classes=["chapter-preview"]
                    )
            

        
        with gr.Row():
            os.makedirs("prompts",exist_ok=True)
            # Enhanced voice sample selection with preview
            with gr.Column():
                voice_dropdown, refresh_button, voice_status, voice_preview = webui_components.create_enhanced_voice_selection_components()
                
                # Voice preview player (shown when voice is selected)
                voice_preview
                
                # Fallback to traditional upload if no samples available
                with gr.Group() as upload_fallback:
                    prompt_audio = gr.Audio(label=i18n("或上传音色参考音频"),key="prompt_audio",
                                            sources=["upload","microphone"],type="filepath", visible=True)
            
            prompt_list = os.listdir("prompts")
            default = ''
            if prompt_list:
                default = prompt_list[0]
            with gr.Column():
                input_text_single = gr.TextArea(label=i18n("文本"),key="input_text_single", placeholder=i18n("请输入目标文本"), info=f"{i18n('当前模型版本')}{tts.model_version or '1.0'}")
                
                # Enhanced auto-save and output management
                auto_save_checkbox, filename_preview, save_info = webui_components.create_enhanced_auto_save_components()
                
                # Enhanced generation button with progress tracking
                gen_button, progress_display, status_display = webui_components.create_enhanced_generation_components()
            output_audio = gr.Audio(label=i18n("生成结果"), visible=True,key="output_audio")
            
        # Enhanced task monitoring for background processing (moved below progress/status)
        with gr.Row():
            with gr.Column():
                with gr.Accordion(i18n("🔄 Background Tasks"), open=False) as task_monitoring_section:
                    task_list, refresh_tasks_button, task_info = webui_components.create_task_monitoring_components()
        experimental_checkbox = gr.Checkbox(label=i18n("显示实验功能"),value=False)
        with gr.Accordion(i18n("功能设置")):
            # Enhanced audio format selection with tooltips and info
            with gr.Row():
                format_dropdown, mp3_bitrate, enable_segmentation, chapters_per_file, format_info = webui_components.create_enhanced_format_selection_components()
            
            # Format information display
            format_info
            
            # Incremental auto-save configuration section
            with gr.Accordion("🔄 增量自动保存设置", open=False):
                with gr.Row():
                    with gr.Column(scale=2):
                        incremental_auto_save_enabled, incremental_auto_save_interval, incremental_auto_save_info = webui_components.create_incremental_auto_save_components()

            
            # 情感控制选项部分
            with gr.Row():
                emo_control_method = gr.Radio(
                    choices=EMO_CHOICES_BASE,
                    type="index",
                    value=EMO_CHOICES_BASE[0],label=i18n("情感控制方式"))
        # 情感参考音频部分
        with gr.Group(visible=False) as emotion_reference_group:
            with gr.Row():
                emo_upload = gr.Audio(label=i18n("上传情感参考音频"), type="filepath")

        # 情感随机采样
        with gr.Row(visible=False) as emotion_randomize_group:
            emo_random = gr.Checkbox(label=i18n("情感随机采样"), value=False)

        # 情感向量控制部分
        with gr.Group(visible=False) as emotion_vector_group:
            with gr.Row():
                with gr.Column():
                    vec1 = gr.Slider(label=i18n("喜"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec2 = gr.Slider(label=i18n("怒"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec3 = gr.Slider(label=i18n("哀"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec4 = gr.Slider(label=i18n("惧"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                with gr.Column():
                    vec5 = gr.Slider(label=i18n("厌恶"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec6 = gr.Slider(label=i18n("低落"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec7 = gr.Slider(label=i18n("惊喜"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)
                    vec8 = gr.Slider(label=i18n("平静"), minimum=0.0, maximum=1.0, value=0.0, step=0.05)

        with gr.Group(visible=False) as emo_text_group:
            with gr.Row():
                emo_text = gr.Textbox(label=i18n("情感描述文本"),
                                      placeholder=i18n("请输入情绪描述（或留空以自动使用目标文本作为情绪描述）"),
                                      value="",
                                      info=i18n("例如：委屈巴巴、危险在悄悄逼近"))


        with gr.Row(visible=False) as emo_weight_group:
            emo_weight = gr.Slider(label=i18n("情感权重"), minimum=0.0, maximum=1.0, value=0.8, step=0.01)

        with gr.Accordion(i18n("高级生成参数设置"), open=False,visible=False) as advanced_settings_group:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(f"**{i18n('GPT2 采样设置')}** _{i18n('参数会影响音频多样性和生成速度详见')} [Generation strategies](https://huggingface.co/docs/transformers/main/en/generation_strategies)._")
                    with gr.Row():
                        do_sample = gr.Checkbox(label="do_sample", value=True, info=i18n("是否进行采样"))
                        temperature = gr.Slider(label="temperature", minimum=0.1, maximum=2.0, value=0.8, step=0.1)
                    with gr.Row():
                        top_p = gr.Slider(label="top_p", minimum=0.0, maximum=1.0, value=0.8, step=0.01)
                        top_k = gr.Slider(label="top_k", minimum=0, maximum=100, value=30, step=1)
                        num_beams = gr.Slider(label="num_beams", value=3, minimum=1, maximum=10, step=1)
                    with gr.Row():
                        repetition_penalty = gr.Number(label="repetition_penalty", precision=None, value=10.0, minimum=0.1, maximum=20.0, step=0.1)
                        length_penalty = gr.Number(label="length_penalty", precision=None, value=0.0, minimum=-2.0, maximum=2.0, step=0.1)
                    max_mel_tokens = gr.Slider(label="max_mel_tokens", value=1500, minimum=50, maximum=tts.cfg.gpt.max_mel_tokens, step=10, info=i18n("生成Token最大数量，过小导致音频被截断"), key="max_mel_tokens")
                    # with gr.Row():
                    #     typical_sampling = gr.Checkbox(label="typical_sampling", value=False, info="不建议使用")
                    #     typical_mass = gr.Slider(label="typical_mass", value=0.9, minimum=0.0, maximum=1.0, step=0.1)
                with gr.Column(scale=2):
                    gr.Markdown(f'**{i18n("分句设置")}** _{i18n("参数会影响音频质量和生成速度")}_')
                    with gr.Row():
                        initial_value = max(20, min(tts.cfg.gpt.max_text_tokens, cmd_args.gui_seg_tokens))
                        max_text_tokens_per_segment = gr.Slider(
                            label=i18n("分句最大Token数"), value=initial_value, minimum=20, maximum=tts.cfg.gpt.max_text_tokens, step=2, key="max_text_tokens_per_segment",
                            info=i18n("建议80~200之间，值越大，分句越长；值越小，分句越碎；过小过大都可能导致音频质量不高"),
                        )
                    with gr.Accordion(i18n("预览分句结果"), open=True) as segments_settings:
                        segments_preview = gr.Dataframe(
                            headers=[i18n("序号"), i18n("分句内容"), i18n("Token数")],
                            key="segments_preview",
                            wrap=True,
                        )
            advanced_params = [
                do_sample, top_p, top_k, temperature,
                length_penalty, num_beams, repetition_penalty, max_mel_tokens,
                # typical_sampling, typical_mass,
            ]
        
        if len(example_cases) > 2:
            example_table = gr.Examples(
                examples=example_cases[:-2],
                examples_per_page=20,
                inputs=[prompt_audio,
                        emo_control_method,
                        input_text_single,
                        emo_upload,
                        emo_weight,
                        emo_text,
                        vec1,vec2,vec3,vec4,vec5,vec6,vec7,vec8,experimental_checkbox]
            )
        elif len(example_cases) > 0:
            example_table = gr.Examples(
                examples=example_cases,
                examples_per_page=20,
                inputs=[prompt_audio,
                        emo_control_method,
                        input_text_single,
                        emo_upload,
                        emo_weight,
                        emo_text,
                        vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8, experimental_checkbox]
            )

    def on_input_text_change(text, max_text_tokens_per_segment):
        if text and len(text) > 0:
            text_tokens_list = tts.tokenizer.tokenize(text)

            segments = tts.tokenizer.split_segments(text_tokens_list, max_text_tokens_per_segment=int(max_text_tokens_per_segment))
            data = []
            for i, s in enumerate(segments):
                segment_str = ''.join(s)
                tokens_count = len(s)
                data.append([i, segment_str, tokens_count])
            return {
                segments_preview: gr.update(value=data, visible=True, type="array"),
            }
        else:
            df = pd.DataFrame([], columns=[i18n("序号"), i18n("分句内容"), i18n("Token数")])
            return {
                segments_preview: gr.update(value=df),
            }

    def on_method_select(emo_control_method):
        if emo_control_method == 1:  # emotion reference audio
            return (gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=True)
                    )
        elif emo_control_method == 2:  # emotion vectors
            return (gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False)
                    )
        elif emo_control_method == 3:  # emotion text description
            return (gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True)
                    )
        else:  # 0: same as speaker voice
            return (gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                    )

    def on_experimental_change(is_exp):
        # 切换情感控制选项
        # 第三个返回值实际没有起作用
        if is_exp:
            return gr.update(choices=EMO_CHOICES_EXPERIMENTAL, value=EMO_CHOICES_EXPERIMENTAL[0]), gr.update(visible=True),gr.update(value=example_cases)
        else:
            return gr.update(choices=EMO_CHOICES_BASE, value=EMO_CHOICES_BASE[0]), gr.update(visible=False),gr.update(value=example_cases[:-2])

    emo_control_method.select(on_method_select,
        inputs=[emo_control_method],
        outputs=[emotion_reference_group,
                 emotion_randomize_group,
                 emotion_vector_group,
                 emo_text_group,
                 emo_weight_group]
    )

    input_text_single.change(
        on_input_text_change,
        inputs=[input_text_single, max_text_tokens_per_segment],
        outputs=[segments_preview]
    )

    experimental_checkbox.change(
        on_experimental_change,
        inputs=[experimental_checkbox],
        outputs=[emo_control_method, advanced_settings_group,example_table.dataset]  # 高级参数Accordion
    )

    max_text_tokens_per_segment.change(
        on_input_text_change,
        inputs=[input_text_single, max_text_tokens_per_segment],
        outputs=[segments_preview]
    )

    prompt_audio.upload(update_prompt_audio,
                         inputs=[],
                         outputs=[gen_button])

    gen_button.click(gen_single,
                     inputs=[emo_control_method, voice_dropdown, prompt_audio, input_text_single, emo_upload, emo_weight,
                            vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8,
                             emo_text,emo_random,
                             format_dropdown, mp3_bitrate, enable_segmentation, chapters_per_file,
                             auto_save_checkbox, filename_preview,
                             file_upload, file_cleaning_toggle, chapter_recognition_toggle,
                             incremental_auto_save_enabled, incremental_auto_save_interval,
                             max_text_tokens_per_segment,
                             *advanced_params,
                     ],
                     outputs=[output_audio, progress_display, status_display])

    # File upload event handlers
    file_upload.upload(
        on_file_upload,
        inputs=[file_upload],
        outputs=[file_status, use_native_chapters, file_preview]
    )
    
    # Chapter recognition toggle handler with real-time preview
    chapter_recognition_toggle.change(
        on_chapter_recognition_change,
        inputs=[chapter_recognition_toggle, file_upload],
        outputs=[chapter_preview]
    )
    
    # File cleaning toggle handler with real-time preview update
    file_cleaning_toggle.change(
        fn=on_file_cleaning_change,
        inputs=[file_cleaning_toggle, file_upload],
        outputs=[file_preview]
    )
    
    # Enhanced format selection event handlers with info updates
    format_dropdown.change(
        webui_components.update_format_info,
        inputs=[format_dropdown, mp3_bitrate],
        outputs=[format_info]
    )
    
    mp3_bitrate.change(
        webui_components.update_format_info,
        inputs=[format_dropdown, mp3_bitrate],
        outputs=[format_info]
    )
    
    # Format selection event handlers
    format_dropdown.change(
        on_format_change,
        inputs=[format_dropdown],
        outputs=[mp3_bitrate]
    )
    
    enable_segmentation.change(
        on_segmentation_change,
        inputs=[enable_segmentation],
        outputs=[chapters_per_file]
    )
    
    # Voice sample event handlers
    refresh_button.click(
        refresh_voice_samples,
        inputs=[],
        outputs=[voice_dropdown, voice_status, voice_preview]
    )

    # Update the voice preview when selection changes
    voice_dropdown.change(
        on_voice_sample_change,
        inputs=[voice_dropdown],
        outputs=[voice_preview]
    )
    
    # Enhanced filename preview updates
    voice_dropdown.change(
        webui_components.update_filename_preview,
        inputs=[file_upload, voice_dropdown, format_dropdown],
        outputs=[filename_preview]
    )
    
    format_dropdown.change(
        webui_components.update_filename_preview,
        inputs=[file_upload, voice_dropdown, format_dropdown],
        outputs=[filename_preview]
    )
    
    file_upload.change(
        webui_components.update_filename_preview,
        inputs=[file_upload, voice_dropdown, format_dropdown],
        outputs=[filename_preview]
    )
    
    # Segmentation availability updates
    file_upload.change(
        update_segmentation_availability,
        inputs=[file_upload, chapter_recognition_toggle],
        outputs=[enable_segmentation]
    )
    
    chapter_recognition_toggle.change(
        update_segmentation_availability,
        inputs=[file_upload, chapter_recognition_toggle],
        outputs=[enable_segmentation]
    )
    
    # Enhanced task monitoring event handlers
    refresh_tasks_button.click(
        webui_components.update_task_list,
        inputs=[],
        outputs=[task_list]
    )
    
    # Enhanced incremental auto-save event handlers with validation
    def handle_auto_save_config_change(enabled, interval, text_input="", file_path=""):
        """Handle auto-save configuration changes with enhanced validation."""
        # Get context information for better validation
        context = webui_components.get_auto_save_context_info(text_input, file_path)
        
        # Handle configuration change with validation
        updated_info, feedback_data = webui_components.handle_auto_save_config_change(
            enabled, interval, context
        )
        
        return updated_info
    
    incremental_auto_save_enabled.change(
        handle_auto_save_config_change,
        inputs=[incremental_auto_save_enabled, incremental_auto_save_interval, input_text_single, file_upload],
        outputs=[incremental_auto_save_info]
    )
    
    incremental_auto_save_interval.change(
        handle_auto_save_config_change,
        inputs=[incremental_auto_save_enabled, incremental_auto_save_interval, input_text_single, file_upload],
        outputs=[incremental_auto_save_info]
    )



if __name__ == "__main__":
    demo.queue(20)
    demo.launch(server_name=cmd_args.host, server_port=cmd_args.port, inbrowser=True)
