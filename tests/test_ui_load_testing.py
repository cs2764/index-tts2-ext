"""
Load tests for enhanced UI components under high usage scenarios.
"""

import time
import threading
import concurrent.futures
from unittest import TestCase
from unittest.mock import Mock, patch
import tempfile
import os

from indextts.enhanced_webui.enhanced_ui_components import EnhancedUIComponents
from indextts.enhanced_webui.ui_theme_manager import get_theme_manager
from indextts.performance.preview_optimizer import PreviewOptimizer


class TestUILoadTesting(TestCase):
    """Test UI components under high load conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock enhanced webui
        self.mock_enhanced_webui = Mock()
        self.mock_enhanced_webui.get_config.return_value = Mock()
        
        self.ui_components = EnhancedUIComponents(self.mock_enhanced_webui)
        self.theme_manager = get_theme_manager()
        
        # Create test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        for i in range(10):
            test_file = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f"第{i+1}章 测试章节\n这是第{i+1}个测试文件的内容。\n")
                for j in range(50):
                    f.write(f"这是第{j+1}行内容，包含了丰富的文本信息。\n")
            self.test_files.append(test_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        for test_file in self.test_files:
            if os.path.exists(test_file):
                os.remove(test_file)
        os.rmdir(self.temp_dir)
    
    def test_high_concurrency_file_preview(self):
        """Test file preview generation under high concurrency."""
        results = []
        errors = []
        
        def preview_worker(file_path):
            try:
                start_time = time.time()
                preview_html, chapter_html, show_native = self.ui_components.update_file_preview(
                    file_path,
                    file_cleaning_enabled=True,
                    chapter_recognition_enabled=True
                )
                processing_time = time.time() - start_time
                
                results.append({
                    'file': file_path,
                    'time': processing_time,
                    'preview_length': len(preview_html),
                    'chapter_length': len(chapter_html),
                    'success': True
                })
            except Exception as e:
                errors.append({
                    'file': file_path,
                    'error': str(e),
                    'success': False
                })
        
        # Run high concurrency test
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Submit 100 tasks (10 files * 10 times each)
            futures = []
            for _ in range(10):
                for file_path in self.test_files:
                    future = executor.submit(preview_worker, file_path)
                    futures.append(future)
            
            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 100)
        
        # Performance analysis
        avg_time = sum(r['time'] for r in results) / len(results)
        max_time = max(r['time'] for r in results)
        
        print(f"High concurrency preview test:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average processing time: {avg_time:.3f}s")
        print(f"  Maximum processing time: {max_time:.3f}s")
        print(f"  Throughput: {len(results)/total_time:.1f} previews/second")
        
        # Performance assertions
        self.assertLess(avg_time, 1.0)  # Average should be less than 1 second
        self.assertLess(max_time, 5.0)  # Maximum should be less than 5 seconds
        self.assertGreater(len(results)/total_time, 5.0)  # At least 5 previews/second
    
    def test_sustained_load_theme_operations(self):
        """Test sustained load on theme operations."""
        results = []
        errors = []
        
        def theme_worker(worker_id):
            try:
                worker_results = []
                for i in range(100):  # Each worker does 100 operations
                    start_time = time.time()
                    
                    # Mix of theme operations
                    css = self.theme_manager.get_custom_css()
                    status = self.theme_manager.create_status_message(f"Worker {worker_id} - Op {i}", "info")
                    progress = self.theme_manager.create_progress_bar(i / 100.0, f"{i}%")
                    tooltip = self.theme_manager.create_tooltip(f"Element {i}", f"Tooltip for worker {worker_id}")
                    
                    operation_time = time.time() - start_time
                    worker_results.append(operation_time)
                
                results.extend(worker_results)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
        
        # Run sustained load test with 10 workers
        start_time = time.time()
        
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=theme_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 1000)  # 10 workers * 100 operations each
        
        # Performance analysis
        avg_time = sum(results) / len(results)
        max_time = max(results)
        min_time = min(results)
        
        print(f"Sustained load theme test:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average operation time: {avg_time:.4f}s")
        print(f"  Min/Max operation time: {min_time:.4f}s / {max_time:.4f}s")
        print(f"  Throughput: {len(results)/total_time:.1f} operations/second")
        
        # Performance assertions
        self.assertLess(avg_time, 0.01)  # Average should be less than 10ms
        self.assertLess(max_time, 0.1)   # Maximum should be less than 100ms
        self.assertGreater(len(results)/total_time, 100.0)  # At least 100 ops/second
    
    def test_memory_stability_under_load(self):
        """Test memory stability under sustained load."""
        import psutil
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        memory_samples = [initial_memory]
        
        def memory_monitor():
            for _ in range(60):  # Monitor for 60 seconds
                time.sleep(1)
                current_memory = process.memory_info().rss
                memory_samples.append(current_memory)
        
        def load_generator():
            for i in range(1000):
                # Generate various UI operations
                css = self.theme_manager.get_custom_css()
                status = self.theme_manager.create_status_message(f"Load test {i}", "success")
                
                # File preview operations
                if i % 10 == 0 and self.test_files:
                    file_path = self.test_files[i % len(self.test_files)]
                    try:
                        preview_html, chapter_html, show_native = self.ui_components.update_file_preview(
                            file_path,
                            file_cleaning_enabled=True,
                            chapter_recognition_enabled=True
                        )
                    except:
                        pass  # Ignore errors for memory test
                
                time.sleep(0.01)  # Small delay to simulate real usage
        
        # Start memory monitoring
        monitor_thread = threading.Thread(target=memory_monitor)
        monitor_thread.start()
        
        # Start load generation
        load_thread = threading.Thread(target=load_generator)
        load_thread.start()
        
        # Wait for completion
        load_thread.join()
        monitor_thread.join()
        
        # Analyze memory usage
        final_memory = memory_samples[-1]
        max_memory = max(memory_samples)
        memory_increase = final_memory - initial_memory
        peak_increase = max_memory - initial_memory
        
        print(f"Memory stability test:")
        print(f"  Initial memory: {initial_memory / 1024 / 1024:.1f} MB")
        print(f"  Final memory: {final_memory / 1024 / 1024:.1f} MB")
        print(f"  Peak memory: {max_memory / 1024 / 1024:.1f} MB")
        print(f"  Memory increase: {memory_increase / 1024 / 1024:.1f} MB")
        print(f"  Peak increase: {peak_increase / 1024 / 1024:.1f} MB")
        
        # Memory assertions
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # Less than 100MB increase
        self.assertLess(peak_increase, 200 * 1024 * 1024)    # Less than 200MB peak increase
    
    def test_component_creation_under_load(self):
        """Test component creation performance under load."""
        results = []
        errors = []
        
        def component_worker(worker_id):
            try:
                worker_results = []
                for i in range(50):  # Each worker creates 50 component sets
                    start_time = time.time()
                    
                    # Create all component types
                    file_components = self.ui_components.create_enhanced_file_upload_components()
                    format_components = self.ui_components.create_enhanced_format_selection_components()
                    voice_components = self.ui_components.create_enhanced_voice_selection_components()
                    auto_save_components = self.ui_components.create_enhanced_auto_save_components()
                    generation_components = self.ui_components.create_enhanced_generation_components()
                    task_components = self.ui_components.create_task_monitoring_components()
                    
                    creation_time = time.time() - start_time
                    worker_results.append(creation_time)
                
                results.extend(worker_results)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
        
        # Run component creation load test
        start_time = time.time()
        
        threads = []
        for worker_id in range(5):  # 5 workers
            thread = threading.Thread(target=component_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 250)  # 5 workers * 50 operations each
        
        # Performance analysis
        avg_time = sum(results) / len(results)
        max_time = max(results)
        
        print(f"Component creation load test:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average creation time: {avg_time:.3f}s")
        print(f"  Maximum creation time: {max_time:.3f}s")
        print(f"  Throughput: {len(results)/total_time:.1f} component sets/second")
        
        # Performance assertions
        self.assertLess(avg_time, 0.5)  # Average should be less than 0.5 seconds
        self.assertLess(max_time, 2.0)  # Maximum should be less than 2 seconds
    
    def test_preview_cache_under_load(self):
        """Test preview cache performance under high load."""
        preview_optimizer = PreviewOptimizer()
        
        try:
            results = []
            errors = []
            
            def cache_worker(worker_id):
                try:
                    worker_results = []
                    for i in range(20):  # Each worker does 20 operations
                        file_path = self.test_files[i % len(self.test_files)]
                        
                        start_time = time.time()
                        preview, metrics = preview_optimizer.generate_optimized_preview(file_path)
                        operation_time = time.time() - start_time
                        
                        worker_results.append({
                            'time': operation_time,
                            'cache_hit': metrics.cache_hit,
                            'file': file_path
                        })
                    
                    results.extend(worker_results)
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run cache load test
            start_time = time.time()
            
            threads = []
            for worker_id in range(10):  # 10 workers
                thread = threading.Thread(target=cache_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Analyze results
            self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
            self.assertEqual(len(results), 200)  # 10 workers * 20 operations each
            
            # Cache performance analysis
            cache_hits = sum(1 for r in results if r['cache_hit'])
            cache_misses = len(results) - cache_hits
            cache_hit_rate = cache_hits / len(results) if results else 0
            
            avg_time = sum(r['time'] for r in results) / len(results)
            avg_cache_hit_time = sum(r['time'] for r in results if r['cache_hit']) / cache_hits if cache_hits else 0
            avg_cache_miss_time = sum(r['time'] for r in results if not r['cache_hit']) / cache_misses if cache_misses else 0
            
            print(f"Preview cache load test:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Cache hit rate: {cache_hit_rate:.1%}")
            print(f"  Average time: {avg_time:.3f}s")
            print(f"  Average cache hit time: {avg_cache_hit_time:.3f}s")
            print(f"  Average cache miss time: {avg_cache_miss_time:.3f}s")
            print(f"  Throughput: {len(results)/total_time:.1f} previews/second")
            
            # Performance assertions
            self.assertGreater(cache_hit_rate, 0.5)  # At least 50% cache hit rate
            self.assertLess(avg_cache_hit_time, avg_cache_miss_time)  # Cache hits should be faster
            self.assertLess(avg_time, 0.5)  # Average should be less than 0.5 seconds
            
        finally:
            preview_optimizer.shutdown()
    
    def test_error_handling_under_load(self):
        """Test error handling under high load conditions."""
        results = []
        errors = []
        
        def error_test_worker(worker_id):
            try:
                for i in range(50):
                    try:
                        # Mix of valid and invalid operations
                        if i % 5 == 0:
                            # Invalid file operation
                            preview_html, chapter_html, show_native = self.ui_components.update_file_preview(
                                "/non/existent/file.txt",
                                file_cleaning_enabled=True,
                                chapter_recognition_enabled=True
                            )
                        else:
                            # Valid operation
                            file_path = self.test_files[i % len(self.test_files)]
                            preview_html, chapter_html, show_native = self.ui_components.update_file_preview(
                                file_path,
                                file_cleaning_enabled=True,
                                chapter_recognition_enabled=True
                            )
                        
                        results.append({'worker': worker_id, 'operation': i, 'success': True})
                    except Exception as e:
                        results.append({'worker': worker_id, 'operation': i, 'success': False, 'error': str(e)})
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {str(e)}")
        
        # Run error handling test
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=error_test_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Analyze error handling
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r['success'])
        failed_operations = total_operations - successful_operations
        
        print(f"Error handling load test:")
        print(f"  Total operations: {total_operations}")
        print(f"  Successful operations: {successful_operations}")
        print(f"  Failed operations: {failed_operations}")
        print(f"  Success rate: {successful_operations/total_operations:.1%}")
        
        # Should handle errors gracefully
        self.assertEqual(len(errors), 0)  # No worker should crash
        self.assertGreater(successful_operations, failed_operations)  # More successes than failures
        self.assertGreater(successful_operations / total_operations, 0.7)  # At least 70% success rate
    
    def test_ui_responsiveness_under_load(self):
        """Test UI responsiveness under background load."""
        response_times = []
        
        def background_load():
            """Generate background load."""
            for i in range(500):
                css = self.theme_manager.get_custom_css()
                status = self.theme_manager.create_status_message(f"Background {i}", "info")
                time.sleep(0.01)
        
        def ui_responsiveness_test():
            """Test UI responsiveness during background load."""
            for i in range(20):
                start_time = time.time()
                
                # Simulate UI interaction
                format_info = self.ui_components.update_format_info("MP3", 128)
                progress_html = self.ui_components.update_generation_progress(0.5, "Testing", 60.0)
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                time.sleep(0.1)  # Simulate user interaction interval
        
        # Start background load
        background_thread = threading.Thread(target=background_load)
        background_thread.start()
        
        # Test UI responsiveness
        ui_thread = threading.Thread(target=ui_responsiveness_test)
        ui_thread.start()
        
        # Wait for completion
        ui_thread.join()
        background_thread.join()
        
        # Analyze responsiveness
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        print(f"UI responsiveness test:")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Maximum response time: {max_response_time:.3f}s")
        print(f"  Response times: {[f'{t:.3f}' for t in response_times]}")
        
        # UI should remain responsive
        self.assertLess(avg_response_time, 0.1)  # Average should be less than 100ms
        self.assertLess(max_response_time, 0.5)  # Maximum should be less than 500ms


if __name__ == '__main__':
    import unittest
    unittest.main()