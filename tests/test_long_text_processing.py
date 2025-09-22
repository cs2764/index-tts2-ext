#!/usr/bin/env python3
"""
Long text processing test to identify and fix the inference logic issue.
This test creates a substantial text and monitors the processing behavior.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from indextts.infer_v2 import IndexTTS2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_long_test_text():
    """Create a long text for testing with varied content."""
    
    # Base paragraphs with different characteristics
    paragraphs = [
        "这是一个测试段落，用来验证长文本处理的正确性。我们需要确保每个段落都被正确处理，而不是被跳过或批量处理。",
        "在深度学习和自然语言处理领域，文本到语音合成技术已经取得了显著的进展。现代的TTS系统能够生成高质量、自然流畅的语音。",
        "IndexTTS2是一个突破性的文本到语音系统，它结合了情感表达控制和精确的持续时间控制。这个系统采用了自回归零样本架构。",
        "语音合成技术的发展经历了多个阶段，从早期的参数合成到现在的神经网络方法。每一次技术革新都带来了音质的显著提升。",
        "在实际应用中，我们需要考虑处理效率、内存使用和音频质量之间的平衡。特别是在处理长文本时，这些因素变得更加重要。",
        "Hello, this is an English paragraph to test multilingual processing. The system should handle both Chinese and English text seamlessly.",
        "Testing punctuation and special characters: numbers 12345, symbols !@#$%, and mixed content 中英混合 should all be processed correctly.",
        "Short paragraph.",
        "这是一个包含各种标点符号的段落：问号？感叹号！逗号，句号。分号；冒号：引号\"内容\"括号（内容）。",
        "Performance monitoring is crucial for long text processing. We need to track memory usage, processing time, and audio quality metrics."
    ]
    
    # Create a long text by repeating and varying paragraphs
    long_text_parts = []
    
    for i in range(200):  # Create 200 sections
        section_num = i + 1
        # Add section header
        long_text_parts.append(f"第{section_num}章节：测试内容")
        
        # Add varied paragraphs
        for j, base_paragraph in enumerate(paragraphs):
            # Modify paragraph slightly to make each unique
            modified_paragraph = base_paragraph.replace("测试", f"测试{section_num}-{j+1}")
            modified_paragraph = modified_paragraph.replace("test", f"test-{section_num}-{j+1}")
            long_text_parts.append(modified_paragraph)
        
        # Add separator
        long_text_parts.append("---")
    
    return "\n\n".join(long_text_parts)

def monitor_processing_behavior(tts_model, text, output_path):
    """Monitor the text processing behavior to identify issues."""
    
    logger.info(f"Starting long text processing test")
    logger.info(f"Text length: {len(text)} characters")
    newline_count = text.count('\n\n')
    logger.info(f"Estimated paragraphs: {newline_count + 1}")
    
    start_time = time.time()
    
    try:
        # Process with detailed monitoring
        result = tts_model.infer(
            text=text,
            prompt_audio="examples/voice_01.wav",
            output_path=output_path,
            emotion="calm",
            speed=1.0
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        
        # Check if output file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Output file created: {output_path} ({file_size} bytes)")
            
            # Estimate expected duration based on text length
            # Rough estimate: ~150 characters per second of speech
            expected_duration = len(text) / 150
            logger.info(f"Expected audio duration: ~{expected_duration:.1f} seconds")
            
            # Check if processing was suspiciously fast
            if processing_time < expected_duration / 10:  # If processing was 10x faster than expected
                logger.warning("⚠️  Processing was suspiciously fast - possible logic error!")
                logger.warning(f"Processing time: {processing_time:.2f}s, Expected minimum: {expected_duration/10:.2f}s")
                return False
            else:
                logger.info("✅ Processing time seems reasonable")
                return True
        else:
            logger.error("❌ Output file was not created")
            return False
            
    except Exception as e:
        logger.error(f"❌ Processing failed with error: {e}")
        return False

def analyze_text_segmentation(text):
    """Analyze how the text would be segmented."""
    
    logger.info("Analyzing text segmentation...")
    
    # Simple paragraph splitting (similar to what the TTS might do)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    logger.info(f"Total paragraphs after splitting: {len(paragraphs)}")
    
    # Analyze paragraph characteristics
    short_paragraphs = [p for p in paragraphs if len(p) < 50]
    medium_paragraphs = [p for p in paragraphs if 50 <= len(p) < 200]
    long_paragraphs = [p for p in paragraphs if len(p) >= 200]
    
    logger.info(f"Short paragraphs (<50 chars): {len(short_paragraphs)}")
    logger.info(f"Medium paragraphs (50-200 chars): {len(medium_paragraphs)}")
    logger.info(f"Long paragraphs (>=200 chars): {len(long_paragraphs)}")
    
    # Show first few paragraphs for verification
    logger.info("First 5 paragraphs:")
    for i, p in enumerate(paragraphs[:5]):
        logger.info(f"  {i+1}: {p[:100]}{'...' if len(p) > 100 else ''}")
    
    return paragraphs

def main():
    """Main test function."""
    
    logger.info("=== Long Text Processing Test ===")
    
    # Create test text
    logger.info("Creating long test text...")
    test_text = create_long_test_text()
    
    # Analyze segmentation
    paragraphs = analyze_text_segmentation(test_text)
    
    # Save test text for inspection
    test_text_path = "test_long_text_input.txt"
    with open(test_text_path, 'w', encoding='utf-8') as f:
        f.write(test_text)
    logger.info(f"Test text saved to: {test_text_path}")
    
    # Initialize TTS model
    logger.info("Initializing IndexTTS2 model...")
    try:
        tts_model = IndexTTS2()
        logger.info("✅ Model initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize model: {e}")
        return False
    
    # Run processing test
    output_path = "test_long_text_output.wav"
    success = monitor_processing_behavior(tts_model, test_text, output_path)
    
    if success:
        logger.info("🎉 Test completed successfully!")
    else:
        logger.error("❌ Test revealed processing issues that need to be fixed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)