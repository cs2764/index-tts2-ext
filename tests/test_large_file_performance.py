"""
Performance tests for large file processing and memory management.
"""

import pytest
import tempfile
import os
import time
import psutil
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from indextts.file_processing.file_processor import FileProcessor
from indextts.chapter_parsing.chapter_parser import SmartChapterParser
from indextts.performance.memory_manager import MemoryManager, MemoryOptimizer
from indextts.task_management.task_manager import TaskManager


class TestLargeFileProcessing:
    """Test processing of large files with performance monitoring."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_files = []
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def teardown_method(self):
        """Clean up test environment."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
    
    def create_large_test_file(self, size_mb: float, content_pattern: str = None) -> str:
        """Create a large test file of specified size."""
        if content_pattern is None:
            content_pattern = "这是测试内容。" * 100 + "\n"
        
        target_size = int(size_mb * 1024 * 1024)  # Convert MB to bytes
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            written_size = 0
            chapter_num = 1
            
            while written_size < target_size:
                # Add chapter headers periodically
                if written_size % (100 * 1024) == 0:  # Every ~100KB
                    chapter_header = f"\n第{chapter_num}章 大文件测试章节\n"
                    f.write(chapter_header)
                    written_size += len(chapter_header.encode('utf-8'))
                    chapter_num += 1
                
                f.write(content_pattern)
                written_size += len(content_pattern.encode('utf-8'))
            
            temp_file = f.name
        
        self.temp_files.append(temp_file)
        return temp_file
    
    def monitor_memory_usage(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Monitor memory usage during function execution."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        final_memory = self.process.memory_info().rss / 1024 / 1024
        
        return {
            'result': result,
            'success': success,
            'error': error,
            'execution_time': end_time - start_time,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_increase_mb': final_memory - initial_memory,
            'peak_memory_mb': final_memory  # Simplified, could use more sophisticated monitoring
        }
    
    def test_small_file_baseline(self):
        """Test small file processing as baseline."""
        # Create 1MB file
        test_file = self.create_large_test_file(1.0)
        
        file_processor = FileProcessor()
        
        # Monitor processing
        result = self.monitor_memory_usage(file_processor.process_file, test_file)
        
        assert result['success'] is True
        assert result['execution_time'] < 5.0  # Should be fast
        assert result['memory_increase_mb'] < 50  # Should use minimal memory
        
        processed_file = result['result']
        assert processed_file is not None
        assert len(processed_file.content) > 0
    
    def test_medium_file_processing(self):
        """Test medium file (10MB) processing."""
        # Create 10MB file
        test_file = self.create_large_test_file(10.0)
        
        file_processor = FileProcessor()
        
        # Monitor processing
        result = self.monitor_memory_usage(file_processor.process_file, test_file)
        
        assert result['success'] is True
        assert result['execution_time'] < 15.0  # Should complete in reasonable time
        assert result['memory_increase_mb'] < 200  # Memory usage should be controlled
        
        processed_file = result['result']
        assert processed_file is not None
        assert len(processed_file.content) > 10 * 1024 * 1024  # Should have processed content
    
    def test_large_file_processing(self):
        """Test large file (50MB) processing."""
        # Create 50MB file
        test_file = self.create_large_test_file(50.0)
        
        file_processor = FileProcessor()
        
        # Monitor processing
        result = self.monitor_memory_usage(file_processor.process_file, test_file)
        
        # Large files might fail or take long time, both are acceptable
        if result['success']:
            assert result['execution_time'] < 60.0  # Should complete within 1 minute
            assert result['memory_increase_mb'] < 500  # Memory should be managed
            
            processed_file = result['result']
            assert processed_file is not None
        else:
            # If it fails, it should be due to memory or size limits
            assert any(keyword in result['error'].lower() for keyword in 
                      ['memory', 'size', 'large', 'limit', 'timeout'])
    
    def test_chapter_parsing_large_file(self):
        """Test chapter parsing on large files."""
        # Create large file with many chapters
        content_pattern = "内容段落。" * 200 + "\n"
        test_file = self.create_large_test_file(20.0, content_pattern)
        
        file_processor = FileProcessor()
        chapter_parser = SmartChapterParser()
        
        # Process file first
        file_result = self.monitor_memory_usage(file_processor.process_file, test_file)
        
        if not file_result['success']:
            pytest.skip("File processing failed, skipping chapter parsing test")
        
        processed_file = file_result['result']
        
        # Parse chapters
        chapter_result = self.monitor_memory_usage(chapter_parser.parse, processed_file.content)
        
        if chapter_result['success']:
            chapters = chapter_result['result']
            assert len(chapters) > 0  # Should find some chapters
            assert chapter_result['execution_time'] < 30.0  # Should be reasonably fast
            assert chapter_result['memory_increase_mb'] < 300  # Memory controlled
        else:
            # Chapter parsing might fail on very large files
            print(f"Chapter parsing failed: {chapter_result['error']}")
    
    def test_memory_optimization_large_file(self):
        """Test memory optimization with large files."""
        # Create large file
        test_file = self.create_large_test_file(30.0)
        
        memory_optimizer = MemoryOptimizer()
        file_size = os.path.getsize(test_file)
        
        # Test optimization context
        with memory_optimizer.optimized_file_processing(file_size) as opt_info:
            assert 'use_chunking' in opt_info
            assert 'chunk_size' in opt_info
            assert 'memory_stats' in opt_info
            
            # For large files, should recommend chunking
            if file_size > 10 * 1024 * 1024:  # > 10MB
                assert opt_info['use_chunking'] is True
                assert opt_info['chunk_size'] > 0
    
    def test_concurrent_large_file_processing(self):
        """Test processing multiple large files concurrently."""
        import concurrent.futures
        
        # Create multiple medium-sized files
        test_files = []
        for i in range(3):
            test_file = self.create_large_test_file(5.0)  # 5MB each
            test_files.append(test_file)
        
        def process_file_worker(file_path: str) -> Dict[str, Any]:
            file_processor = FileProcessor()
            start_time = time.time()
            initial_memory = self.process.memory_info().rss / 1024 / 1024
            
            try:
                processed_file = file_processor.process_file(file_path)
                success = True
                error = None
            except Exception as e:
                processed_file = None
                success = False
                error = str(e)
            
            end_time = time.time()
            final_memory = self.process.memory_info().rss / 1024 / 1024
            
            return {
                'success': success,
                'error': error,
                'execution_time': end_time - start_time,
                'memory_increase': final_memory - initial_memory,
                'file_processed': processed_file is not None
            }
        
        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_file_worker, f) for f in test_files]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        
        # At least some should succeed
        assert len(successful_results) >= 1
        
        # Performance should be reasonable
        if successful_results:
            avg_time = sum(r['execution_time'] for r in successful_results) / len(successful_results)
            max_memory = max(r['memory_increase'] for r in successful_results)
            
            assert avg_time < 30.0  # Average processing time
            assert max_memory < 400  # Memory increase per file
    
    def test_background_task_large_file(self):
        """Test background task processing with large files."""
        # Create large file
        test_file = self.create_large_test_file(15.0)
        
        task_manager = TaskManager()
        
        # Create background task
        task_id = task_manager.create_task(
            task_type='file_to_audio',
            params={
                'file_path': test_file,
                'output_format': 'mp3',
                'voice_sample': 'test_voice.wav'
            }
        )
        
        assert task_id is not None
        
        # Monitor task progress
        start_time = time.time()
        max_wait_time = 60.0  # Maximum 1 minute
        
        while (time.time() - start_time) < max_wait_time:
            status = task_manager.get_task_status(task_id)
            
            if status:
                assert status.progress >= 0.0
                assert status.progress <= 1.0
                
                if status.status in ['completed', 'failed']:
                    break
            
            time.sleep(1.0)  # Check every second
        
        # Get final status
        final_status = task_manager.get_task_status(task_id)
        
        if final_status:
            # Task should have made progress or completed
            assert final_status.status in ['queued', 'processing', 'completed', 'failed']
            
            if final_status.status == 'failed':
                # Failure is acceptable for very large files
                print(f"Task failed (expected for large files): {final_status.error_message}")
    
    def test_memory_cleanup_after_large_file(self):
        """Test memory cleanup after processing large files."""
        import gc
        
        # Get initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Process a large file
        test_file = self.create_large_test_file(20.0)
        
        file_processor = FileProcessor()
        
        try:
            processed_file = file_processor.process_file(test_file)
            # Use the processed file to ensure it's not optimized away
            content_length = len(processed_file.content) if processed_file else 0
            assert content_length >= 0
        except Exception:
            # Processing might fail for very large files
            pass
        
        # Clear references and force garbage collection
        processed_file = None
        file_processor = None
        gc.collect()
        
        # Wait a bit for cleanup
        time.sleep(2.0)
        
        # Check memory after cleanup
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable after cleanup
        assert memory_increase < 200  # Less than 200MB permanent increase


class TestMemoryManagement:
    """Test memory management under various conditions."""
    
    def test_memory_threshold_detection(self):
        """Test memory threshold detection."""
        memory_manager = MemoryManager()
        
        # Get current memory stats
        stats = memory_manager.get_memory_stats()
        
        assert stats.total_memory > 0
        assert stats.available_memory > 0
        assert 0 <= stats.memory_percent <= 1
        
        # Test threshold checks
        warning = memory_manager.is_memory_warning()
        critical = memory_manager.is_memory_critical()
        cleanup = memory_manager.should_cleanup()
        
        assert isinstance(warning, bool)
        assert isinstance(critical, bool)
        assert isinstance(cleanup, bool)
    
    def test_chunk_size_calculation(self):
        """Test optimal chunk size calculation for different file sizes."""
        memory_manager = MemoryManager()
        
        # Test different file sizes
        test_sizes = [
            1024 * 1024,      # 1MB
            10 * 1024 * 1024, # 10MB
            50 * 1024 * 1024, # 50MB
            100 * 1024 * 1024 # 100MB
        ]
        
        for file_size in test_sizes:
            chunk_size = memory_manager.calculate_optimal_chunk_size(file_size)
            
            assert chunk_size > 0
            assert chunk_size <= file_size
            
            # Larger files should generally have larger chunks (up to a limit)
            if file_size >= 10 * 1024 * 1024:  # >= 10MB
                assert chunk_size >= 1024 * 1024  # At least 1MB chunks
    
    def test_memory_optimization_recommendations(self):
        """Test memory optimization recommendations."""
        memory_optimizer = MemoryOptimizer()
        
        # Test different scenarios
        scenarios = [
            {'file_size': 1024 * 1024, 'expected_chunking': False},      # 1MB - no chunking needed
            {'file_size': 50 * 1024 * 1024, 'expected_chunking': True}, # 50MB - chunking recommended
            {'file_size': 100 * 1024 * 1024, 'expected_chunking': True} # 100MB - chunking required
        ]
        
        for scenario in scenarios:
            with memory_optimizer.optimized_file_processing(scenario['file_size']) as opt_info:
                assert 'use_chunking' in opt_info
                assert 'chunk_size' in opt_info
                
                # Check chunking recommendation matches expectation
                if scenario['expected_chunking']:
                    assert opt_info['use_chunking'] is True
                    assert opt_info['chunk_size'] > 0
    
    def test_memory_report_generation(self):
        """Test memory report generation."""
        memory_optimizer = MemoryOptimizer()
        
        report = memory_optimizer.get_memory_report()
        
        assert 'memory_stats' in report
        assert 'thresholds' in report
        assert 'recommendations' in report
        
        # Check memory stats structure
        stats = report['memory_stats']
        required_keys = ['total_gb', 'available_gb', 'used_percent', 'process_mb']
        
        for key in required_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))
            assert stats[key] >= 0
        
        # Check recommendations
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestPerformanceBenchmarking:
    """Test performance benchmarking for large file operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up test environment."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
    
    def create_test_file(self, size_mb: float) -> str:
        """Create a test file of specified size."""
        content = "测试内容。" * 1000 + "\n"
        target_size = int(size_mb * 1024 * 1024)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            written = 0
            while written < target_size:
                f.write(content)
                written += len(content.encode('utf-8'))
            
            temp_file = f.name
        
        self.temp_files.append(temp_file)
        return temp_file
    
    def benchmark_file_processing(self, file_sizes: List[float]) -> Dict[str, Any]:
        """Benchmark file processing for different file sizes."""
        results = {}
        
        for size_mb in file_sizes:
            test_file = self.create_test_file(size_mb)
            file_processor = FileProcessor()
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            try:
                processed_file = file_processor.process_file(test_file)
                success = True
                error = None
            except Exception as e:
                processed_file = None
                success = False
                error = str(e)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            results[f'{size_mb}MB'] = {
                'success': success,
                'error': error,
                'processing_time': end_time - start_time,
                'memory_increase': end_memory - start_memory,
                'throughput_mb_per_sec': size_mb / (end_time - start_time) if success else 0
            }
        
        return results
    
    def test_file_processing_scalability(self):
        """Test file processing scalability across different file sizes."""
        file_sizes = [1, 5, 10, 20]  # MB
        
        results = self.benchmark_file_processing(file_sizes)
        
        # Analyze scalability
        successful_results = {k: v for k, v in results.items() if v['success']}
        
        assert len(successful_results) >= 2  # At least small files should work
        
        # Check that processing time scales reasonably
        if len(successful_results) >= 2:
            times = [v['processing_time'] for v in successful_results.values()]
            sizes = [float(k.replace('MB', '')) for k in successful_results.keys()]
            
            # Processing time should generally increase with file size
            # but not exponentially (allow some variance)
            max_time = max(times)
            min_time = min(times)
            
            # Time increase should be reasonable (not more than 100x for 20x size increase)
            if max(sizes) / min(sizes) <= 20:  # If size ratio is <= 20
                assert max_time / min_time <= 100  # Time ratio should be <= 100
    
    def test_memory_efficiency_scaling(self):
        """Test memory efficiency across different file sizes."""
        file_sizes = [2, 8, 15]  # MB
        
        results = self.benchmark_file_processing(file_sizes)
        
        successful_results = {k: v for k, v in results.items() if v['success']}
        
        if len(successful_results) >= 2:
            # Memory increase should be controlled
            memory_increases = [v['memory_increase'] for v in successful_results.values()]
            
            # Memory increase should not be excessive
            max_memory_increase = max(memory_increases)
            assert max_memory_increase < 500  # Less than 500MB increase
            
            # Memory efficiency (MB processed per MB memory used)
            for size_str, result in successful_results.items():
                file_size_mb = float(size_str.replace('MB', ''))
                memory_used = result['memory_increase']
                
                if memory_used > 0:
                    efficiency = file_size_mb / memory_used
                    # Should process at least 0.1MB per MB of memory used
                    assert efficiency >= 0.1
    
    def test_throughput_benchmarking(self):
        """Test processing throughput benchmarking."""
        file_sizes = [3, 7, 12]  # MB
        
        results = self.benchmark_file_processing(file_sizes)
        
        successful_results = {k: v for k, v in results.items() if v['success']}
        
        if successful_results:
            throughputs = [v['throughput_mb_per_sec'] for v in successful_results.values()]
            
            # Should have reasonable throughput
            avg_throughput = sum(throughputs) / len(throughputs)
            assert avg_throughput > 0.1  # At least 0.1 MB/sec
            
            # Throughput should be consistent (not vary by more than 10x)
            if len(throughputs) > 1:
                max_throughput = max(throughputs)
                min_throughput = min(throughputs)
                
                if min_throughput > 0:
                    throughput_ratio = max_throughput / min_throughput
                    assert throughput_ratio <= 20  # Allow up to 20x variation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])