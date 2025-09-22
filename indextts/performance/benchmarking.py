"""
Performance benchmarking and testing for all components.
"""

import time
import gc
import os
import tempfile
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import psutil
import numpy as np


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    component_name: str
    test_name: str
    execution_time: float
    memory_usage_mb: float
    memory_peak_mb: float
    throughput: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    suite_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[BenchmarkResult] = field(default_factory=list)
    
    @property
    def total_time(self) -> float:
        """Get total execution time."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.success)
        return (successful / len(self.results)) * 100


class PerformanceBenchmark:
    """Main performance benchmarking system."""
    
    def __init__(self, enable_memory_tracking: bool = True):
        """Initialize benchmark system."""
        self.enable_memory_tracking = enable_memory_tracking
        self.process = psutil.Process()
        self.benchmark_suites: List[BenchmarkSuite] = []
        self._temp_files: List[str] = []
    
    def create_benchmark_suite(self, suite_name: str) -> BenchmarkSuite:
        """Create a new benchmark suite."""
        suite = BenchmarkSuite(
            suite_name=suite_name,
            start_time=datetime.now()
        )
        self.benchmark_suites.append(suite)
        return suite
    
    def benchmark_function(self, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Benchmark a function execution.
        
        Args:
            func: Function to benchmark
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            BenchmarkResult with performance metrics
        """
        # Get function name
        func_name = getattr(func, '__name__', str(func))
        
        # Pre-benchmark cleanup
        if self.enable_memory_tracking:
            gc.collect()
            initial_memory = self._get_memory_usage()
        
        # Execute and measure
        start_time = time.time()
        peak_memory = initial_memory if self.enable_memory_tracking else 0.0
        
        try:
            # Monitor memory during execution if enabled
            if self.enable_memory_tracking:
                memory_monitor = MemoryMonitor()
                memory_monitor.start()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Stop memory monitoring
            if self.enable_memory_tracking:
                memory_monitor.stop()
                peak_memory = memory_monitor.get_peak_memory()
            
            execution_time = time.time() - start_time
            
            # Calculate final memory usage
            final_memory = self._get_memory_usage() if self.enable_memory_tracking else 0.0
            
            return BenchmarkResult(
                component_name="function",
                test_name=func_name,
                execution_time=execution_time,
                memory_usage_mb=final_memory - initial_memory if self.enable_memory_tracking else 0.0,
                memory_peak_mb=peak_memory - initial_memory if self.enable_memory_tracking else 0.0,
                success=True,
                metadata={'result_type': type(result).__name__}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return BenchmarkResult(
                component_name="function",
                test_name=func_name,
                execution_time=execution_time,
                memory_usage_mb=0.0,
                memory_peak_mb=0.0,
                success=False,
                error_message=str(e)
            )
    
    def benchmark_file_processing(self, file_processor, test_files: List[str]) -> List[BenchmarkResult]:
        """Benchmark file processing performance."""
        results = []
        
        for file_path in test_files:
            if not os.path.exists(file_path):
                # Create test file if it doesn't exist
                file_path = self._create_test_file(file_path)
            
            file_size = os.path.getsize(file_path)
            
            def process_file():
                return file_processor.process_file(file_path)
            
            result = self.benchmark_function(process_file)
            result.component_name = "file_processor"
            result.test_name = f"process_{os.path.basename(file_path)}"
            result.throughput = file_size / result.execution_time if result.execution_time > 0 else 0
            result.metadata.update({
                'file_size_mb': file_size / (1024 * 1024),
                'file_type': os.path.splitext(file_path)[1]
            })
            
            results.append(result)
        
        return results
    
    def benchmark_chapter_parsing(self, chapter_parser, test_texts: List[str]) -> List[BenchmarkResult]:
        """Benchmark chapter parsing performance."""
        results = []
        
        for i, text in enumerate(test_texts):
            text_length = len(text)
            
            def parse_chapters():
                return chapter_parser.parse(text)
            
            result = self.benchmark_function(parse_chapters)
            result.component_name = "chapter_parser"
            result.test_name = f"parse_text_{i+1}"
            result.throughput = text_length / result.execution_time if result.execution_time > 0 else 0
            result.metadata.update({
                'text_length': text_length,
                'text_size_mb': text_length / (1024 * 1024)
            })
            
            results.append(result)
        
        return results
    
    def benchmark_audio_processing(self, audio_processor, test_audio_files: List[str]) -> List[BenchmarkResult]:
        """Benchmark audio processing performance."""
        results = []
        
        for audio_path in test_audio_files:
            if not os.path.exists(audio_path):
                # Create test audio file if it doesn't exist
                audio_path = self._create_test_audio_file(audio_path)
            
            file_size = os.path.getsize(audio_path)
            
            def process_audio():
                return audio_processor.process_audio(audio_path)
            
            result = self.benchmark_function(process_audio)
            result.component_name = "audio_processor"
            result.test_name = f"process_{os.path.basename(audio_path)}"
            result.throughput = file_size / result.execution_time if result.execution_time > 0 else 0
            result.metadata.update({
                'file_size_mb': file_size / (1024 * 1024),
                'audio_format': os.path.splitext(audio_path)[1]
            })
            
            results.append(result)
        
        return results
    
    def benchmark_task_management(self, task_manager, num_tasks: int = 10) -> List[BenchmarkResult]:
        """Benchmark task management performance."""
        results = []
        
        # Test task creation
        def create_tasks():
            task_ids = []
            for i in range(num_tasks):
                task_id = task_manager.create_task(
                    task_type="test_task",
                    params={'task_number': i}
                )
                task_ids.append(task_id)
            return task_ids
        
        result = self.benchmark_function(create_tasks)
        result.component_name = "task_manager"
        result.test_name = "create_tasks"
        result.throughput = num_tasks / result.execution_time if result.execution_time > 0 else 0
        result.metadata.update({'num_tasks': num_tasks})
        results.append(result)
        
        # Test task status retrieval
        def get_all_statuses():
            return task_manager.get_all_tasks()
        
        result = self.benchmark_function(get_all_statuses)
        result.component_name = "task_manager"
        result.test_name = "get_all_statuses"
        results.append(result)
        
        return results
    
    def run_comprehensive_benchmark(self, components: Dict[str, Any]) -> BenchmarkSuite:
        """Run comprehensive benchmark of all components."""
        suite = self.create_benchmark_suite("comprehensive_benchmark")
        
        # Benchmark file processing
        if 'file_processor' in components:
            test_files = self._generate_test_files()
            file_results = self.benchmark_file_processing(
                components['file_processor'], test_files
            )
            suite.results.extend(file_results)
        
        # Benchmark chapter parsing
        if 'chapter_parser' in components:
            test_texts = self._generate_test_texts()
            chapter_results = self.benchmark_chapter_parsing(
                components['chapter_parser'], test_texts
            )
            suite.results.extend(chapter_results)
        
        # Benchmark audio processing
        if 'audio_processor' in components:
            test_audio_files = self._generate_test_audio_files()
            audio_results = self.benchmark_audio_processing(
                components['audio_processor'], test_audio_files
            )
            suite.results.extend(audio_results)
        
        # Benchmark task management
        if 'task_manager' in components:
            task_results = self.benchmark_task_management(components['task_manager'])
            suite.results.extend(task_results)
        
        suite.end_time = datetime.now()
        return suite
    
    def generate_performance_report(self, suite: BenchmarkSuite) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not suite.results:
            return {"error": "No benchmark results available"}
        
        # Group results by component
        component_results = {}
        for result in suite.results:
            if result.component_name not in component_results:
                component_results[result.component_name] = []
            component_results[result.component_name].append(result)
        
        # Calculate statistics for each component
        component_stats = {}
        for component, results in component_results.items():
            successful_results = [r for r in results if r.success]
            
            if successful_results:
                execution_times = [r.execution_time for r in successful_results]
                memory_usage = [r.memory_usage_mb for r in successful_results]
                throughputs = [r.throughput for r in successful_results if r.throughput]
                
                component_stats[component] = {
                    'total_tests': len(results),
                    'successful_tests': len(successful_results),
                    'success_rate': len(successful_results) / len(results) * 100,
                    'avg_execution_time': np.mean(execution_times),
                    'min_execution_time': np.min(execution_times),
                    'max_execution_time': np.max(execution_times),
                    'avg_memory_usage_mb': np.mean(memory_usage),
                    'max_memory_usage_mb': np.max(memory_usage),
                    'avg_throughput': np.mean(throughputs) if throughputs else 0,
                    'failed_tests': [r.test_name for r in results if not r.success]
                }
        
        return {
            'suite_info': {
                'name': suite.suite_name,
                'start_time': suite.start_time.isoformat(),
                'end_time': suite.end_time.isoformat() if suite.end_time else None,
                'total_time': suite.total_time,
                'total_tests': len(suite.results),
                'overall_success_rate': suite.success_rate
            },
            'component_statistics': component_stats,
            'system_info': self._get_system_info(),
            'recommendations': self._generate_recommendations(component_stats)
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'platform': psutil.sys.platform
        }
    
    def _generate_recommendations(self, component_stats: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []
        
        for component, stats in component_stats.items():
            if stats['success_rate'] < 90:
                recommendations.append(f"{component}: Low success rate ({stats['success_rate']:.1f}%) - investigate failed tests")
            
            if stats['avg_execution_time'] > 5.0:
                recommendations.append(f"{component}: High average execution time ({stats['avg_execution_time']:.2f}s) - consider optimization")
            
            if stats['max_memory_usage_mb'] > 500:
                recommendations.append(f"{component}: High memory usage ({stats['max_memory_usage_mb']:.1f}MB) - consider memory optimization")
            
            if stats['avg_throughput'] > 0 and stats['avg_throughput'] < 1000:
                recommendations.append(f"{component}: Low throughput ({stats['avg_throughput']:.1f} units/s) - consider performance tuning")
        
        return recommendations
    
    def _generate_test_files(self) -> List[str]:
        """Generate test files for benchmarking."""
        test_files = []
        
        # Small text file
        small_file = self._create_test_file("small_test.txt", size_kb=10)
        test_files.append(small_file)
        
        # Medium text file
        medium_file = self._create_test_file("medium_test.txt", size_kb=100)
        test_files.append(medium_file)
        
        # Large text file
        large_file = self._create_test_file("large_test.txt", size_kb=1000)
        test_files.append(large_file)
        
        return test_files
    
    def _generate_test_texts(self) -> List[str]:
        """Generate test texts for chapter parsing benchmarks."""
        return [
            # Short text with chapters
            "第一章 开始\n这是第一章的内容。\n\n第二章 继续\n这是第二章的内容。",
            
            # Medium text with multiple chapters
            "\n".join([f"第{i}章 章节{i}\n" + "内容" * 100 for i in range(1, 11)]),
            
            # Long text with many chapters
            "\n".join([f"第{i}章 章节{i}\n" + "内容" * 500 for i in range(1, 51)])
        ]
    
    def _generate_test_audio_files(self) -> List[str]:
        """Generate test audio files for benchmarking."""
        test_files = []
        
        # Create small test audio file
        small_audio = self._create_test_audio_file("small_test.wav", duration=5.0)
        test_files.append(small_audio)
        
        # Create medium test audio file
        medium_audio = self._create_test_audio_file("medium_test.wav", duration=30.0)
        test_files.append(medium_audio)
        
        return test_files
    
    def _create_test_file(self, filename: str, size_kb: int = 10) -> str:
        """Create a test text file."""
        temp_file = tempfile.mktemp(suffix='.txt')
        self._temp_files.append(temp_file)
        
        # Generate content
        content = "测试内容 " * (size_kb * 1024 // 10)  # Approximate size
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return temp_file
    
    def _create_test_audio_file(self, filename: str, duration: float = 5.0) -> str:
        """Create a test audio file."""
        temp_file = tempfile.mktemp(suffix='.wav')
        self._temp_files.append(temp_file)
        
        try:
            import soundfile as sf
            import numpy as np
            
            # Generate simple sine wave
            sample_rate = 22050
            samples = int(duration * sample_rate)
            t = np.linspace(0, duration, samples)
            audio_data = 0.1 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
            
            sf.write(temp_file, audio_data, sample_rate)
            
        except ImportError:
            # Fallback: create empty file
            with open(temp_file, 'wb') as f:
                f.write(b'\x00' * 1024)  # 1KB of zeros
        
        return temp_file
    
    def cleanup_temp_files(self):
        """Clean up temporary test files."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
        self._temp_files.clear()


class ComponentBenchmark:
    """Specialized benchmarking for individual components."""
    
    def __init__(self, component_name: str):
        """Initialize component benchmark."""
        self.component_name = component_name
        self.benchmark_system = PerformanceBenchmark()
    
    def benchmark_memory_efficiency(self, test_func: Callable, test_data_sizes: List[int]) -> List[BenchmarkResult]:
        """Benchmark memory efficiency across different data sizes."""
        results = []
        
        for size in test_data_sizes:
            # Generate test data of specified size
            test_data = self._generate_test_data(size)
            
            def test_with_data():
                return test_func(test_data)
            
            result = self.benchmark_system.benchmark_function(test_with_data)
            result.component_name = self.component_name
            result.test_name = f"memory_test_{size}"
            result.metadata.update({'data_size': size})
            
            results.append(result)
        
        return results
    
    def benchmark_scalability(self, test_func: Callable, scale_factors: List[int]) -> List[BenchmarkResult]:
        """Benchmark scalability with increasing load."""
        results = []
        
        for factor in scale_factors:
            def scaled_test():
                return test_func(scale_factor=factor)
            
            result = self.benchmark_system.benchmark_function(scaled_test)
            result.component_name = self.component_name
            result.test_name = f"scalability_test_{factor}x"
            result.metadata.update({'scale_factor': factor})
            
            results.append(result)
        
        return results
    
    def _generate_test_data(self, size: int) -> str:
        """Generate test data of specified size."""
        return "测试数据" * (size // 8)  # Approximate size in bytes


class MemoryMonitor:
    """Monitor memory usage during function execution."""
    
    def __init__(self, interval: float = 0.1):
        """Initialize memory monitor."""
        self.interval = interval
        self.process = psutil.Process()
        self.monitoring = False
        self.peak_memory = 0.0
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start memory monitoring."""
        self.monitoring = True
        self.peak_memory = self._get_current_memory()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return self.peak_memory
    
    def _monitor_loop(self):
        """Memory monitoring loop."""
        while self.monitoring:
            current_memory = self._get_current_memory()
            self.peak_memory = max(self.peak_memory, current_memory)
            time.sleep(self.interval)
    
    def _get_current_memory(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)