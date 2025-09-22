"""
Performance tests for preview generation and processing systems.
"""

import os
import time
import tempfile
import threading
from unittest import TestCase
from unittest.mock import Mock, patch

from indextts.performance.preview_optimizer import PreviewCache, PreviewOptimizer, PreviewMetrics
from indextts.performance.memory_manager import MemoryOptimizer, MemoryManager
from indextts.performance.chapter_optimizer import ChapterParsingOptimizer
from indextts.file_processing.models import FilePreview
from indextts.chapter_parsing.models import ChapterPattern


class TestPreviewCache(TestCase):
    """Test preview cache functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = PreviewCache(max_entries=5, max_age_hours=1)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test file
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.cache.shutdown()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get operations."""
        preview = FilePreview(
            filename="test.txt",
            preview_text="Line 1\nLine 2\n",
            total_lines=3,
            encoding="utf-8",
            file_size="10 B",
            preview_truncated=True
        )
        
        # Cache the preview
        self.cache.put(self.test_file, preview)
        
        # Retrieve from cache
        cached_preview = self.cache.get(self.test_file)
        self.assertIsNotNone(cached_preview)
        self.assertEqual(cached_preview.filename, "test.txt")
        self.assertEqual(cached_preview.total_lines, 3)
    
    def test_cache_invalidation_on_file_change(self):
        """Test cache invalidation when file is modified."""
        preview = FilePreview(
            filename="test.txt",
            preview_text="Line 1\nLine 2\n",
            total_lines=3,
            encoding="utf-8",
            file_size="10 B",
            preview_truncated=True
        )
        
        # Cache the preview
        self.cache.put(self.test_file, preview)
        
        # Modify the file
        time.sleep(0.1)  # Ensure different mtime
        with open(self.test_file, 'a', encoding='utf-8') as f:
            f.write("Line 4\n")
        
        # Cache should be invalidated
        cached_preview = self.cache.get(self.test_file)
        self.assertIsNone(cached_preview)
    
    def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        # Fill cache beyond limit
        for i in range(10):
            file_path = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Content {i}\n")
            
            preview = FilePreview(
                filename=f"test_{i}.txt",
                preview_text=f"Content {i}\n",
                total_lines=1,
                encoding="utf-8",
                file_size="10 B",
                preview_truncated=False
            )
            
            self.cache.put(file_path, preview)
        
        # Cache should not exceed max_entries
        stats = self.cache.get_stats()
        self.assertLessEqual(stats['total_entries'], self.cache.max_entries)
        
        # Clean up test files
        for i in range(10):
            file_path = os.path.join(self.temp_dir, f"test_{i}.txt")
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        preview = FilePreview(
            filename="test.txt",
            preview_text="Line 1\nLine 2\n",
            total_lines=3,
            encoding="utf-8",
            file_size="10 B",
            preview_truncated=True
        )
        
        results = []
        
        def cache_worker():
            for i in range(100):
                self.cache.put(self.test_file, preview)
                cached = self.cache.get(self.test_file)
                results.append(cached is not None)
        
        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        self.assertTrue(all(results))


class TestPreviewOptimizer(TestCase):
    """Test preview optimizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.optimizer = PreviewOptimizer()
        
        # Create test files
        self.small_file = os.path.join(self.temp_dir, "small.txt")
        with open(self.small_file, 'w', encoding='utf-8') as f:
            for i in range(10):
                f.write(f"Line {i+1}\n")
        
        self.large_file = os.path.join(self.temp_dir, "large.txt")
        with open(self.large_file, 'w', encoding='utf-8') as f:
            for i in range(1000):
                f.write(f"Line {i+1} with some content to make it larger\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.optimizer.shutdown()
        if os.path.exists(self.small_file):
            os.remove(self.small_file)
        if os.path.exists(self.large_file):
            os.remove(self.large_file)
        os.rmdir(self.temp_dir)
    
    def test_preview_generation_performance(self):
        """Test preview generation performance."""
        start_time = time.time()
        preview, metrics = self.optimizer.generate_optimized_preview(self.small_file)
        generation_time = time.time() - start_time
        
        # Check that preview was generated
        self.assertIsNotNone(preview)
        self.assertEqual(preview.filename, "small.txt")
        self.assertGreater(preview.total_lines, 0)
        
        # Check metrics
        self.assertIsInstance(metrics, PreviewMetrics)
        self.assertFalse(metrics.cache_hit)  # First generation
        self.assertGreater(metrics.generation_time, 0)
        self.assertLessEqual(metrics.generation_time, generation_time + 0.1)  # Allow small margin
    
    def test_preview_caching_performance(self):
        """Test preview caching improves performance."""
        # First generation (not cached)
        start_time = time.time()
        preview1, metrics1 = self.optimizer.generate_optimized_preview(self.small_file)
        first_time = time.time() - start_time
        
        # Second generation (cached)
        start_time = time.time()
        preview2, metrics2 = self.optimizer.generate_optimized_preview(self.small_file)
        second_time = time.time() - start_time
        
        # Cached version should be faster
        self.assertFalse(metrics1.cache_hit)
        self.assertTrue(metrics2.cache_hit)
        self.assertLess(second_time, first_time)
        
        # Content should be identical
        self.assertEqual(preview1.preview_text, preview2.preview_text)
    
    def test_large_file_optimization(self):
        """Test optimization for large files."""
        memory_optimizer = MemoryOptimizer()
        optimizer = PreviewOptimizer(memory_optimizer=memory_optimizer)
        
        try:
            preview, metrics = optimizer.generate_optimized_preview(self.large_file)
            
            # Should generate preview successfully
            self.assertIsNotNone(preview)
            self.assertGreater(preview.total_lines, 100)
            
            # Should have reasonable performance
            self.assertLess(metrics.generation_time, 5.0)  # Should complete within 5 seconds
            
        finally:
            optimizer.shutdown()
    
    def test_performance_report(self):
        """Test performance reporting."""
        # Generate some previews
        self.optimizer.generate_optimized_preview(self.small_file)
        self.optimizer.generate_optimized_preview(self.small_file)  # Cached
        
        report = self.optimizer.get_performance_report()
        
        # Check report structure
        self.assertIn('cache_performance', report)
        self.assertIn('generation_performance', report)
        self.assertIn('recent_metrics', report)
        
        # Check cache performance
        cache_perf = report['cache_performance']
        self.assertEqual(cache_perf['total_previews'], 2)
        self.assertEqual(cache_perf['cache_hits'], 1)
        self.assertEqual(cache_perf['cache_hit_rate'], "50.0%")


class TestMemoryOptimizer(TestCase):
    """Test memory optimizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.memory_optimizer = MemoryOptimizer()
    
    def test_memory_stats_collection(self):
        """Test memory statistics collection."""
        stats = self.memory_optimizer.memory_manager.get_memory_stats()
        
        # Check that stats are collected
        self.assertGreater(stats.total_memory, 0)
        self.assertGreater(stats.available_memory, 0)
        self.assertGreaterEqual(stats.memory_percent, 0)
        self.assertLessEqual(stats.memory_percent, 1.0)
    
    def test_optimization_context_managers(self):
        """Test optimization context managers."""
        # Test file processing optimization
        with self.memory_optimizer.optimized_file_processing(1024 * 1024) as opt_info:
            self.assertIn('use_chunking', opt_info)
            self.assertIn('chunk_size', opt_info)
            self.assertIn('memory_stats', opt_info)
        
        # Test text processing optimization
        with self.memory_optimizer.optimized_text_processing(10000) as opt_info:
            self.assertIn('use_streaming', opt_info)
            self.assertIn('estimated_memory', opt_info)
            self.assertIn('memory_stats', opt_info)
    
    def test_chapter_parsing_optimization_settings(self):
        """Test chapter parsing optimization settings."""
        settings = self.memory_optimizer.optimize_chapter_parsing(50000)
        
        # Check that settings are provided
        self.assertIn('use_fast_scan', settings)
        self.assertIn('cache_patterns', settings)
        self.assertIn('max_candidates', settings)
        self.assertIn('batch_size', settings)
        
        # Settings should be reasonable
        self.assertIsInstance(settings['use_fast_scan'], bool)
        self.assertIsInstance(settings['cache_patterns'], bool)
        self.assertGreater(settings['max_candidates'], 0)
        self.assertGreater(settings['batch_size'], 0)
    
    def test_memory_report(self):
        """Test memory usage report."""
        report = self.memory_optimizer.get_memory_report()
        
        # Check report structure
        self.assertIn('memory_stats', report)
        self.assertIn('thresholds', report)
        self.assertIn('recommendations', report)
        
        # Check memory stats
        mem_stats = report['memory_stats']
        self.assertIn('total_gb', mem_stats)
        self.assertIn('available_gb', mem_stats)
        self.assertIn('used_percent', mem_stats)


class TestChapterParsingOptimizer(TestCase):
    """Test chapter parsing optimizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = ChapterParsingOptimizer(enable_parallel_processing=True, max_workers=2)
        
        # Create test text with chapters
        self.test_text = """
        前言
        这是一本测试书籍。
        
        第一章 开始
        这是第一章的内容。
        这里有更多内容。
        
        第二章 继续
        这是第二章的内容。
        更多的章节内容在这里。
        
        第三章 结束
        这是最后一章。
        """
        
        # Create test patterns
        self.test_patterns = [
            ChapterPattern(
                name="chinese_chapter",
                pattern=r"第[一二三四五六七八九十\d]+章\s+[^\n]+",
                confidence_score=80,
                language="zh"
            )
        ]
    
    def test_optimized_chapter_parsing_performance(self):
        """Test optimized chapter parsing performance."""
        optimization_settings = {
            'use_fast_scan': True,
            'cache_patterns': True,
            'max_candidates': 100,
            'batch_size': 500
        }
        
        start_time = time.time()
        chapters, metrics = self.optimizer.optimize_chapter_parsing(
            self.test_text, self.test_patterns, optimization_settings
        )
        parsing_time = time.time() - start_time
        
        # Check that chapters were found
        self.assertGreater(len(chapters), 0)
        
        # Check metrics
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.total_time, 0)
        self.assertLessEqual(metrics.total_time, parsing_time + 0.1)  # Allow small margin
        self.assertEqual(metrics.optimization_level, "aggressive")
    
    def test_parallel_vs_sequential_performance(self):
        """Test parallel vs sequential processing performance."""
        # Create larger test text
        large_text = self.test_text * 100
        
        optimization_settings = {
            'use_fast_scan': True,
            'cache_patterns': True,
            'max_candidates': 200,
            'batch_size': 1000
        }
        
        # Test parallel processing
        parallel_optimizer = ChapterParsingOptimizer(enable_parallel_processing=True, max_workers=4)
        start_time = time.time()
        chapters_parallel, metrics_parallel = parallel_optimizer.optimize_chapter_parsing(
            large_text, self.test_patterns, optimization_settings
        )
        parallel_time = time.time() - start_time
        
        # Test sequential processing
        sequential_optimizer = ChapterParsingOptimizer(enable_parallel_processing=False)
        start_time = time.time()
        chapters_sequential, metrics_sequential = sequential_optimizer.optimize_chapter_parsing(
            large_text, self.test_patterns, optimization_settings
        )
        sequential_time = time.time() - start_time
        
        # Results should be similar
        self.assertEqual(len(chapters_parallel), len(chapters_sequential))
        
        # Performance comparison (parallel might not always be faster for small texts)
        print(f"Parallel time: {parallel_time:.3f}s, Sequential time: {sequential_time:.3f}s")
    
    def test_optimization_report(self):
        """Test optimization performance report."""
        optimization_settings = {
            'use_fast_scan': True,
            'cache_patterns': True,
            'max_candidates': 100,
            'batch_size': 500
        }
        
        # Run optimization
        self.optimizer.optimize_chapter_parsing(
            self.test_text, self.test_patterns, optimization_settings
        )
        
        # Get report
        report = self.optimizer.get_optimization_report()
        
        # Check report structure
        self.assertIn('performance', report)
        self.assertIn('results', report)
        self.assertIn('optimization', report)
        
        # Check performance metrics
        perf = report['performance']
        self.assertIn('total_time', perf)
        self.assertIn('pattern_matching_time', perf)
        self.assertIn('filtering_time', perf)
        self.assertIn('content_extraction_time', perf)
        
        # Check results
        results = report['results']
        self.assertIn('candidates_found', results)
        self.assertIn('chapters_extracted', results)
        self.assertIn('extraction_rate', results)


class TestIntegratedPerformance(TestCase):
    """Test integrated performance of all optimization systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test file with chapters
        self.test_file = os.path.join(self.temp_dir, "test_book.txt")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("""前言
这是一本测试书籍的前言部分。

第一章 开始的故事
这是第一章的内容，包含了很多有趣的故事。
故事从一个小村庄开始，那里住着一个勇敢的少年。

第二章 冒险之旅
少年踏上了冒险的旅程，遇到了各种挑战。
他学会了勇气和智慧的重要性。

第三章 最终的胜利
经过重重困难，少年最终获得了胜利。
这个故事告诉我们坚持的力量。
""")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def test_end_to_end_performance(self):
        """Test end-to-end performance of file processing and chapter parsing."""
        from indextts.file_processing.file_processor import FileProcessor
        from indextts.chapter_parsing.chapter_parser import SmartChapterParser
        from indextts.performance.memory_manager import MemoryOptimizer
        
        # Initialize components with optimization
        memory_optimizer = MemoryOptimizer()
        file_processor = FileProcessor()
        chapter_parser = SmartChapterParser()
        preview_optimizer = PreviewOptimizer(memory_optimizer=memory_optimizer)
        
        try:
            # Test file preview generation
            start_time = time.time()
            preview, preview_metrics = preview_optimizer.generate_optimized_preview(self.test_file)
            preview_time = time.time() - start_time
            
            # Test file processing
            start_time = time.time()
            processed_file = file_processor.process_file(self.test_file)
            processing_time = time.time() - start_time
            
            # Test chapter parsing
            start_time = time.time()
            chapters = chapter_parser.parse(processed_file.content)
            parsing_time = time.time() - start_time
            
            # Verify results
            self.assertIsNotNone(preview)
            self.assertGreater(len(processed_file.content), 0)
            self.assertGreater(len(chapters), 0)
            
            # Performance should be reasonable
            total_time = preview_time + processing_time + parsing_time
            self.assertLess(total_time, 5.0)  # Should complete within 5 seconds
            
            print(f"Performance breakdown:")
            print(f"  Preview generation: {preview_time:.3f}s")
            print(f"  File processing: {processing_time:.3f}s")
            print(f"  Chapter parsing: {parsing_time:.3f}s")
            print(f"  Total time: {total_time:.3f}s")
            
            # Test caching improves performance
            start_time = time.time()
            cached_preview, cached_metrics = preview_optimizer.generate_optimized_preview(self.test_file)
            cached_time = time.time() - start_time
            
            self.assertTrue(cached_metrics.cache_hit)
            self.assertLess(cached_time, preview_time)
            
        finally:
            preview_optimizer.shutdown()
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization during processing."""
        from indextts.performance.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        
        # Get initial memory stats
        initial_stats = memory_manager.get_memory_stats()
        
        # Simulate processing with memory optimization
        with MemoryOptimizer().optimized_file_processing(os.path.getsize(self.test_file)) as opt_info:
            # Process file
            with open(self.test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get memory stats during processing
            processing_stats = memory_manager.get_memory_stats()
        
        # Get final memory stats
        final_stats = memory_manager.get_memory_stats()
        
        # Memory usage should be reasonable
        self.assertLess(processing_stats.process_percent, 0.5)  # Less than 50% of system memory
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_stats.process_percent*100:.1f}%")
        print(f"  During processing: {processing_stats.process_percent*100:.1f}%")
        print(f"  Final: {final_stats.process_percent*100:.1f}%")


if __name__ == '__main__':
    import unittest
    unittest.main()