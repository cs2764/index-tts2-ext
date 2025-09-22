"""
推理性能优化器 - 实现推理加速的各种优化策略
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import time
import numpy as np
from functools import lru_cache
import hashlib


@dataclass
class InferenceConfig:
    """推理配置类"""
    max_text_tokens_per_segment: int = 100
    segments_bucket_max_size: int = 4
    chunk_size: int = 2
    use_fp16: bool = True
    use_cuda_kernel: bool = False
    use_deepspeed: bool = False
    use_cuda_graphs: bool = False
    enable_parallel_processing: bool = True
    max_parallel_workers: int = 2
    memory_optimization: bool = True
    streaming_output: bool = False
    cache_size: int = 1000


class GPUMemoryManager:
    """GPU 内存管理器"""
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.memory_stats = {}
        
    def get_available_memory(self) -> int:
        """获取可用显存（字节）"""
        if not torch.cuda.is_available():
            return 0
        
        torch.cuda.synchronize()
        return torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        if not torch.cuda.is_available():
            return {"allocated": 0, "reserved": 0, "free": 0}
        
        allocated = torch.cuda.memory_allocated(0)
        reserved = torch.cuda.memory_reserved(0)
        free = torch.cuda.get_device_properties(0).total_memory - allocated
        
        return {
            "allocated_gb": allocated / (1024**3),
            "reserved_gb": reserved / (1024**3),
            "free_gb": free / (1024**3)
        }
    
    def smart_empty_cache(self, threshold_gb: float = 2.0):
        """智能清理显存缓存"""
        if not torch.cuda.is_available():
            return
        
        memory_stats = self.get_memory_usage()
        fragmentation = memory_stats["reserved_gb"] - memory_stats["allocated_gb"]
        
        if fragmentation > threshold_gb:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            return True
        return False


class TensorBufferPool:
    """张量缓冲池 - 预分配内存以减少分配开销"""
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.buffers = {}
        self.lock = threading.Lock()
    
    def get_buffer(self, shape: Tuple, dtype: torch.dtype) -> torch.Tensor:
        """获取或创建缓冲区"""
        key = (shape, dtype)
        
        with self.lock:
            if key not in self.buffers:
                self.buffers[key] = torch.empty(shape, dtype=dtype, device=self.device)
            return self.buffers[key].clone()
    
    def clear(self):
        """清空缓冲池"""
        with self.lock:
            self.buffers.clear()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class AdaptiveConfigOptimizer:
    """自适应配置优化器 - 根据硬件动态调整参数"""
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.memory_manager = GPUMemoryManager(device)
    
    def optimize_config(self, base_config: InferenceConfig) -> InferenceConfig:
        """根据硬件优化配置"""
        config = InferenceConfig(**base_config.__dict__)
        
        if not torch.cuda.is_available():
            # CPU 配置
            config.segments_bucket_max_size = 1
            config.chunk_size = 1
            config.use_fp16 = False
            config.use_cuda_kernel = False
            config.use_deepspeed = False
            config.use_cuda_graphs = False
            config.enable_parallel_processing = False
            return config
        
        # 获取显存大小
        total_memory = torch.cuda.get_device_properties(0).total_memory
        free_memory = self.memory_manager.get_available_memory()
        
        # 根据显存调整配置
        if total_memory > 24 * 1024**3:  # 24GB+
            config.max_text_tokens_per_segment = 150
            config.segments_bucket_max_size = 16
            config.chunk_size = 8
            config.max_parallel_workers = 4
        elif total_memory > 16 * 1024**3:  # 16GB+
            config.max_text_tokens_per_segment = 120
            config.segments_bucket_max_size = 12
            config.chunk_size = 6
            config.max_parallel_workers = 3
        elif total_memory > 8 * 1024**3:  # 8GB+
            config.max_text_tokens_per_segment = 100
            config.segments_bucket_max_size = 8
            config.chunk_size = 4
            config.max_parallel_workers = 2
        elif total_memory > 4 * 1024**3:  # 4GB+
            config.max_text_tokens_per_segment = 50
            config.segments_bucket_max_size = 4
            config.chunk_size = 2
            config.max_parallel_workers = 1
        else:
            config.max_text_tokens_per_segment = 30
            config.segments_bucket_max_size = 2
            config.chunk_size = 1
            config.enable_parallel_processing = False
        
        # 检查 CUDA 能力
        if torch.cuda.is_available():
            capability = torch.cuda.get_device_capability()
            if capability[0] >= 7:  # Volta 及以上架构
                config.use_cuda_graphs = True
                config.use_cuda_kernel = True
        
        return config


class ParallelInferenceProcessor:
    """并行推理处理器"""
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_parallel(self, 
                        items: List[Any], 
                        process_func: Callable,
                        *args, **kwargs) -> List[Any]:
        """并行处理多个项目"""
        if len(items) <= 1 or self.max_workers == 1:
            # 单项或单线程，直接处理
            return [process_func(item, *args, **kwargs) for item in items]
        
        # 并行处理
        futures = []
        for item in items:
            future = self.executor.submit(process_func, item, *args, **kwargs)
            futures.append(future)
        
        # 收集结果（保持顺序）
        results = []
        for future in futures:
            results.append(future.result())
        
        return results
    
    def process_parallel_with_progress(self,
                                      items: List[Any],
                                      process_func: Callable,
                                      progress_callback: Optional[Callable] = None,
                                      *args, **kwargs) -> List[Any]:
        """带进度回调的并行处理"""
        total = len(items)
        completed = 0
        results = [None] * total
        
        futures_to_index = {}
        for i, item in enumerate(items):
            future = self.executor.submit(process_func, item, *args, **kwargs)
            futures_to_index[future] = i
        
        for future in as_completed(futures_to_index):
            index = futures_to_index[future]
            results[index] = future.result()
            completed += 1
            
            if progress_callback:
                progress_callback(completed, total)
        
        return results
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)


class StreamingAudioProcessor:
    """流式音频处理器"""
    
    def __init__(self, buffer_size: int = 3):
        self.buffer_size = buffer_size
        self.queue = queue.Queue(maxsize=buffer_size)
        self.producer_thread = None
        self.stop_event = threading.Event()
    
    def start_streaming(self, 
                        producer_func: Callable,
                        *args, **kwargs):
        """启动流式处理"""
        self.stop_event.clear()
        
        def producer_wrapper():
            try:
                for item in producer_func(*args, **kwargs):
                    if self.stop_event.is_set():
                        break
                    self.queue.put(item)
            finally:
                self.queue.put(None)  # 结束标记
        
        self.producer_thread = threading.Thread(target=producer_wrapper)
        self.producer_thread.start()
    
    def get_stream(self):
        """获取流式数据"""
        while True:
            item = self.queue.get()
            if item is None:
                break
            yield item
    
    def stop_streaming(self):
        """停止流式处理"""
        self.stop_event.set()
        if self.producer_thread:
            self.producer_thread.join()


class CachedTokenizer:
    """缓存的分词器"""
    
    def __init__(self, tokenizer, cache_size: int = 1000):
        self.tokenizer = tokenizer
        self.cache_size = cache_size
        self._cache = {}
        self._access_count = {}
        self.lock = threading.Lock()
    
    def _get_text_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @lru_cache(maxsize=1000)
    def tokenize_cached(self, text_hash: str, text: str):
        """缓存的分词方法"""
        return self.tokenizer.tokenize(text)
    
    def tokenize(self, text: str):
        """分词（带缓存）"""
        text_hash = self._get_text_hash(text)
        
        with self.lock:
            if text_hash in self._cache:
                self._access_count[text_hash] += 1
                return self._cache[text_hash].copy()
        
        # 分词
        tokens = self.tokenizer.tokenize(text)
        
        # 添加到缓存
        with self.lock:
            if len(self._cache) >= self.cache_size:
                # LRU 驱逐
                min_access = min(self._access_count.values())
                for h, count in list(self._access_count.items()):
                    if count == min_access:
                        del self._cache[h]
                        del self._access_count[h]
                        break
            
            self._cache[text_hash] = tokens
            self._access_count[text_hash] = 1
        
        return tokens


class CUDAGraphOptimizer:
    """CUDA Graph 优化器"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and torch.cuda.is_available()
        self.graph_cache = {}
    
    def capture_graph(self, 
                     model_func: Callable,
                     input_shape: Tuple,
                     *args, **kwargs) -> Callable:
        """捕获 CUDA Graph"""
        if not self.enabled:
            return model_func
        
        key = str(input_shape)
        
        if key in self.graph_cache:
            return self.graph_cache[key]
        
        # 创建静态输入
        static_input = torch.randn(input_shape, device="cuda")
        
        # 预热
        for _ in range(3):
            _ = model_func(static_input, *args, **kwargs)
        
        # 捕获图
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph):
            static_output = model_func(static_input, *args, **kwargs)
        
        def graph_callable(input_tensor):
            static_input.copy_(input_tensor)
            graph.replay()
            return static_output.clone()
        
        self.graph_cache[key] = graph_callable
        return graph_callable


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.lock = threading.Lock()
    
    def start_timer(self, name: str):
        """开始计时"""
        self.start_times[name] = time.perf_counter()
    
    def end_timer(self, name: str) -> float:
        """结束计时并记录"""
        if name not in self.start_times:
            return 0.0
        
        elapsed = time.perf_counter() - self.start_times[name]
        
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(elapsed)
        
        del self.start_times[name]
        return elapsed
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """获取统计信息"""
        with self.lock:
            if name not in self.metrics:
                return {}
            
            values = self.metrics[name]
            return {
                "count": len(values),
                "total": sum(values),
                "mean": np.mean(values),
                "std": np.std(values),
                "min": min(values),
                "max": max(values)
            }
    
    def get_report(self) -> str:
        """生成性能报告"""
        report = ["Performance Report:", "=" * 50]
        
        with self.lock:
            for name, values in self.metrics.items():
                stats = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": min(values),
                    "max": max(values)
                }
                
                report.append(f"\n{name}:")
                report.append(f"  Count: {stats['count']}")
                report.append(f"  Mean: {stats['mean']:.4f}s")
                report.append(f"  Std: {stats['std']:.4f}s")
                report.append(f"  Min: {stats['min']:.4f}s")
                report.append(f"  Max: {stats['max']:.4f}s")
        
        return "\n".join(report)
    
    def reset(self):
        """重置所有指标"""
        with self.lock:
            self.metrics.clear()
            self.start_times.clear()


class OptimizedInferenceEngine:
    """优化的推理引擎 - 整合所有优化技术"""
    
    def __init__(self, base_model, config: Optional[InferenceConfig] = None):
        self.base_model = base_model
        self.device = next(base_model.parameters()).device
        
        # 配置
        self.config = config or InferenceConfig()
        
        # 优化器
        self.config_optimizer = AdaptiveConfigOptimizer(str(self.device))
        self.config = self.config_optimizer.optimize_config(self.config)
        
        # 组件
        self.memory_manager = GPUMemoryManager(str(self.device))
        self.buffer_pool = TensorBufferPool(str(self.device))
        self.parallel_processor = ParallelInferenceProcessor(
            self.config.max_parallel_workers
        )
        self.streaming_processor = StreamingAudioProcessor()
        self.cuda_graph_optimizer = CUDAGraphOptimizer(
            self.config.use_cuda_graphs
        )
        self.performance_monitor = PerformanceMonitor()
    
    def optimize_batch_processing(self, 
                                 segments: List[Any],
                                 process_func: Callable) -> List[Any]:
        """优化的批处理"""
        self.performance_monitor.start_timer("batch_processing")
        
        # 动态调整批大小
        available_memory = self.memory_manager.get_available_memory()
        if available_memory < 2 * 1024**3:  # < 2GB
            batch_size = max(1, self.config.segments_bucket_max_size // 2)
        else:
            batch_size = self.config.segments_bucket_max_size
        
        # 分批处理
        results = []
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            
            if self.config.enable_parallel_processing and len(batch) > 1:
                # 并行处理
                batch_results = self.parallel_processor.process_parallel(
                    batch, process_func
                )
            else:
                # 顺序处理
                batch_results = [process_func(item) for item in batch]
            
            results.extend(batch_results)
            
            # 内存管理
            if self.config.memory_optimization:
                self.memory_manager.smart_empty_cache()
        
        self.performance_monitor.end_timer("batch_processing")
        return results
    
    def process_with_streaming(self,
                              data_generator: Callable,
                              process_func: Callable) -> Any:
        """流式处理"""
        if not self.config.streaming_output:
            # 非流式处理
            data = list(data_generator())
            return process_func(data)
        
        # 流式处理
        self.streaming_processor.start_streaming(data_generator)
        
        results = []
        for item in self.streaming_processor.get_stream():
            result = process_func(item)
            results.append(result)
            yield result
        
        return results
    
    def get_performance_report(self) -> str:
        """获取性能报告"""
        report = [self.performance_monitor.get_report()]
        
        # 添加内存使用情况
        memory_stats = self.memory_manager.get_memory_usage()
        report.append("\nMemory Usage:")
        report.append(f"  Allocated: {memory_stats['allocated_gb']:.2f} GB")
        report.append(f"  Reserved: {memory_stats['reserved_gb']:.2f} GB")
        report.append(f"  Free: {memory_stats['free_gb']:.2f} GB")
        
        # 添加配置信息
        report.append("\nActive Configuration:")
        report.append(f"  Batch Size: {self.config.segments_bucket_max_size}")
        report.append(f"  Chunk Size: {self.config.chunk_size}")
        report.append(f"  Parallel Workers: {self.config.max_parallel_workers}")
        report.append(f"  FP16: {self.config.use_fp16}")
        report.append(f"  CUDA Graphs: {self.config.use_cuda_graphs}")
        
        return "\n".join(report)
    
    def cleanup(self):
        """清理资源"""
        self.parallel_processor.shutdown()
        self.streaming_processor.stop_streaming()
        self.buffer_pool.clear()
        self.memory_manager.smart_empty_cache(threshold_gb=0)  # 强制清理
        self.performance_monitor.reset()


# 使用示例
if __name__ == "__main__":
    # 创建配置
    config = InferenceConfig(
        max_text_tokens_per_segment=100,
        segments_bucket_max_size=8,
        enable_parallel_processing=True,
        memory_optimization=True
    )
    
    # 模拟模型
    class DummyModel(nn.Module):
        def forward(self, x):
            return x * 2
    
    model = DummyModel().cuda() if torch.cuda.is_available() else DummyModel()
    
    # 创建优化引擎
    engine = OptimizedInferenceEngine(model, config)
    
    # 模拟数据
    segments = list(range(100))
    
    # 优化的批处理
    results = engine.optimize_batch_processing(
        segments,
        lambda x: x * 2  # 模拟处理函数
    )
    
    # 打印性能报告
    print(engine.get_performance_report())
    
    # 清理
    engine.cleanup()