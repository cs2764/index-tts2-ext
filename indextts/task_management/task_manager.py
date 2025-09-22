"""
Background task manager for handling long-running TTS operations.
"""

import os
import threading
import time
import uuid
from queue import Queue, Empty
from typing import Dict, Optional, Callable, Any, List
from .models import TaskStatus, TaskResult, TaskStatusEnum, TaskManagerConfig
from .progress_tracker import ProgressTracker, ConsoleOutputManager
from .error_handler import ErrorHandler, TaskRecoveryManager, ErrorType
from .task_persistence import TaskStateManager, TaskResultManager


class TaskManager:
    """Manages background tasks with queue system and progress tracking."""
    
    def __init__(self, config: Optional[TaskManagerConfig] = None):
        """Initialize the task manager with configuration."""
        self.config = config or TaskManagerConfig.default()
        self.tasks: Dict[str, TaskStatus] = {}
        self.task_queue = Queue(maxsize=self.config.max_queue_size)
        self.worker_threads: List[threading.Thread] = []
        self.status_callbacks: Dict[str, Callable] = {}
        self.running = False
        self._lock = threading.Lock()
        
        # Initialize progress tracking
        self.console_manager = ConsoleOutputManager()
        self.progress_trackers: Dict[str, ProgressTracker] = {}
        
        # Initialize error handling and persistence
        self.error_handler = ErrorHandler()
        self.recovery_manager = TaskRecoveryManager(self.error_handler)
        self.state_manager = TaskStateManager(enable_persistence=self.config.enable_persistence)
        self.result_manager = TaskResultManager()
        
        # Performance optimization will be initialized lazily to avoid circular imports
        self._memory_optimizer = None
        
        # Restore active tasks from persistence
        self._restore_active_tasks()
        
        # Start worker threads
        self._start_workers()
    
    def create_task(self, task_type: str, params: Dict[str, Any], 
                   callback: Optional[Callable] = None, 
                   console_callback: Optional[Callable] = None) -> str:
        """
        Create new background task and return task ID.
        
        Args:
            task_type: Type of task to create
            params: Parameters for the task
            callback: Optional callback for status updates
            console_callback: Optional callback for console output
            
        Returns:
            Unique task ID
            
        Raises:
            RuntimeError: If task queue is full
        """
        task_id = str(uuid.uuid4())
        
        # Create task status
        task_status = TaskStatus(
            task_id=task_id,
            status=TaskStatusEnum.QUEUED,
            progress=0.0,
            current_stage="Queued",
            estimated_remaining=None,
            result_path=None,
            error_message=None,
            created_at=None,  # Will be set in __post_init__
            updated_at=None,  # Will be set in __post_init__
            metadata={
                'task_type': task_type,
                'params': params
            }
        )
        
        with self._lock:
            self.tasks[task_id] = task_status
            if callback:
                self.status_callbacks[task_id] = callback
            
            # Register progress tracker
            if console_callback:
                self.console_manager.add_output_callback(console_callback)
            progress_tracker = self.console_manager.register_task(task_id)
            self.progress_trackers[task_id] = progress_tracker
        
        # Add to queue
        try:
            self.task_queue.put((task_id, task_type, params), block=False)
        except:
            # Queue is full
            with self._lock:
                del self.tasks[task_id]
                if task_id in self.status_callbacks:
                    del self.status_callbacks[task_id]
                if task_id in self.progress_trackers:
                    self.console_manager.unregister_task(task_id)
                    del self.progress_trackers[task_id]
            raise RuntimeError("Task queue is full")
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get current status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskStatus object or None if task not found
        """
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskStatus]:
        """Get status of all tasks."""
        with self._lock:
            return self.tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it's not already processing.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False otherwise
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatusEnum.QUEUED:
                task.status = TaskStatusEnum.CANCELLED
                task.current_stage = "Cancelled"
                self._update_task_timestamp(task_id)
                return True
        return False
    
    def update_task_progress(self, task_id: str, progress: float, 
                           stage: str, estimated_remaining: Optional[float] = None):
        """
        Update task progress and status.
        
        Args:
            task_id: ID of the task
            progress: Progress value between 0.0 and 1.0
            stage: Current processing stage description
            estimated_remaining: Estimated remaining time in seconds
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatusEnum.PROCESSING:
                task.progress = max(0.0, min(1.0, progress))
                task.current_stage = stage
                task.estimated_remaining = estimated_remaining
                self._update_task_timestamp(task_id)
                
                # Call status callback if registered
                callback = self.status_callbacks.get(task_id)
                if callback:
                    try:
                        callback(task)
                    except Exception as e:
                        print(f"Error in status callback for task {task_id}: {e}")
    
    def complete_task(self, task_id: str, result_path: Optional[str] = None, 
                     error_message: Optional[str] = None):
        """
        Mark task as completed or failed.
        
        Args:
            task_id: ID of the task
            result_path: Path to result file (if successful)
            error_message: Error message (if failed)
        """
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                if error_message:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = error_message
                    task.current_stage = "Failed"
                else:
                    task.status = TaskStatusEnum.COMPLETED
                    task.result_path = result_path
                    task.current_stage = "Completed"
                    task.progress = 1.0
                
                self._update_task_timestamp(task_id)
                
                # Store results if successful
                if not error_message and result_path:
                    result_data = {
                        'task_type': task.metadata.get('task_type', 'unknown'),
                        'completion_time': task.updated_at.isoformat(),
                        'processing_duration': (task.updated_at - task.created_at).total_seconds()
                    }
                    output_files = [result_path] if result_path else []
                    self.result_manager.store_task_result(task_id, result_data, output_files)
    
    def fail_task(self, task_id: str, error_message: str):
        """
        Mark task as failed (convenience method).
        
        Args:
            task_id: ID of the task
            error_message: Error message describing the failure
        """
        self.complete_task(task_id, result_path=None, error_message=error_message)
        
        # Clean up progress tracker
        if task_id in self.progress_trackers:
            self.console_manager.unregister_task(task_id)
            del self.progress_trackers[task_id]
        
        # Clean up recovery tracking
        self.recovery_manager.cleanup_task_recovery(task_id)
    
    def cleanup_old_tasks(self):
        """Remove old completed tasks based on configuration."""
        current_time = time.time()
        cleanup_threshold = self.config.cleanup_completed_after
        
        with self._lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if (task.is_complete and 
                    (current_time - task.updated_at.timestamp()) > cleanup_threshold):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                if task_id in self.status_callbacks:
                    del self.status_callbacks[task_id]
                if task_id in self.progress_trackers:
                    self.console_manager.unregister_task(task_id)
                    del self.progress_trackers[task_id]
                
                # Clean up persistence and results
                self.state_manager.cleanup_task_state(task_id)
                self.result_manager.cleanup_task_results(task_id)
                self.recovery_manager.cleanup_task_recovery(task_id)
    
    def shutdown(self):
        """Shutdown the task manager and stop all workers."""
        self.running = False
        
        # Stop memory monitoring if initialized
        if self._memory_optimizer:
            self._memory_optimizer.memory_manager.stop_monitoring()
        
        # Wait for worker threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=5.0)
    
    def _start_workers(self):
        """Start worker threads for processing tasks."""
        self.running = True
        
        for i in range(self.config.max_concurrent_tasks):
            worker = threading.Thread(target=self._worker_loop, name=f"TaskWorker-{i}")
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
    
    def _worker_loop(self):
        """Main loop for worker threads."""
        while self.running:
            try:
                # Get task from queue with timeout
                task_id, task_type, params = self.task_queue.get(timeout=1.0)
                
                # Update task status to processing
                with self._lock:
                    task = self.tasks.get(task_id)
                    if task and task.status == TaskStatusEnum.QUEUED:
                        task.status = TaskStatusEnum.PROCESSING
                        task.current_stage = "Starting"
                        self._update_task_timestamp(task_id)
                
                # Process the task with error handling
                try:
                    self._process_task_with_recovery(task_id, task_type, params)
                except Exception as e:
                    # Final error handling if recovery fails
                    error_type = self.error_handler.classify_error(e, {'task_id': task_id, 'task_type': task_type})
                    self.complete_task(task_id, error_message=f"{error_type.value}: {str(e)}")
                
                self.task_queue.task_done()
                
            except Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                print(f"Error in worker loop: {e}")
    
    def _process_task(self, task_id: str, task_type: str, params: Dict[str, Any]):
        """
        Process a specific task with detailed progress tracking.
        
        Args:
            task_id: ID of the task
            task_type: Type of task to process
            params: Task parameters
        """
        progress_tracker = self.progress_trackers.get(task_id)
        if not progress_tracker:
            # Fallback to basic processing without detailed tracking
            self._process_task_basic(task_id, task_type, params)
            return
        
        try:
            if task_type == 'tts_generation':
                self._process_tts_task(task_id, params, progress_tracker)
            else:
                # Handle other task types
                self._process_generic_task(task_id, task_type, params, progress_tracker)
                
        except Exception as e:
            self.complete_task(task_id, error_message=str(e))
    
    def _process_tts_task(self, task_id: str, params: Dict[str, Any], progress_tracker):
        """
        Process a TTS generation task with real TTS engine.
        
        Args:
            task_id: ID of the task
            params: Task parameters containing TTS settings
            progress_tracker: Progress tracker for this task
        """
        # Extract parameters
        text = params.get('text', '')
        voice_prompt = params.get('voice_prompt', '')
        output_path = params.get('output_path', '')
        generation_params = params.get('generation_params', {})
        
        # Get TTS engine from params or use a global reference
        tts_engine = params.get('tts_engine')
        if not tts_engine:
            # Try to get TTS engine from a global registry or similar
            # For now, raise an error if not provided
            raise ValueError("TTS engine not provided in task parameters")
        
        # Start text processing stage with detailed progress
        progress_tracker.start_stage("Text Processing", ["Tokenizing", "Segmentation"])
        self.update_task_progress(task_id, 0.05, "Text Processing")
        
        # Set up progress callbacks for text processing
        def tokenize_progress_callback(progress, desc):
            stage_progress = 0.5 * progress  # First half of text processing
            progress_tracker.update_stage_progress(stage_progress, desc)
            self.update_task_progress(task_id, 0.05 + 0.05 * stage_progress, f"Text Processing - {desc}")
        
        def segment_progress_callback(progress, desc):
            stage_progress = 0.5 + 0.5 * progress  # Second half of text processing
            progress_tracker.update_stage_progress(stage_progress, desc)
            self.update_task_progress(task_id, 0.05 + 0.05 * stage_progress, f"Text Processing - {desc}")
        
        # Tokenize text to get segments with progress
        try:
            text_tokens_list = tts_engine.tokenizer.tokenize(text, progress_callback=tokenize_progress_callback)
            max_tokens_per_segment = generation_params.get('max_text_tokens_per_segment', 120)
            segments = tts_engine.tokenizer.split_segments(text_tokens_list, max_tokens_per_segment, progress_callback=segment_progress_callback)
            segments_count = len(segments)
        except Exception as e:
            segments = [text]  # Fallback to single segment
            segments_count = 1
        
        progress_tracker.update_stage_progress(1.0, f"Text processing complete: {segments_count} segments")
        progress_tracker.complete_stage()
        
        # Audio generation stage (main processing) - simplified progress
        progress_tracker.start_stage("Audio Generation", ["TTS Inference"])
        self.update_task_progress(task_id, 0.15, "Audio Generation")
        
        # Set up progress callback for TTS engine - only show segment-level progress
        def tts_progress_callback(progress, desc):
            # Only update on significant progress changes or segment completion
            if "完成" in desc or progress >= 1.0 or progress == 0.0:
                stage_progress = min(1.0, max(0.0, (progress - 0.15) / 0.8))  # Map 0.15-0.95 to 0.0-1.0
                progress_tracker.update_stage_progress(stage_progress, desc)
                overall_progress = 0.15 + (stage_progress * 0.8)  # 80% of total for audio generation
                self.update_task_progress(task_id, overall_progress, desc)
        
        # Hook progress callback into TTS engine
        tts_engine.gr_progress = tts_progress_callback
        
        # Call TTS engine for actual audio generation
        result_path = tts_engine.infer(
            spk_audio_prompt=voice_prompt,
            text=text,
            output_path=output_path,
            emo_audio_prompt=generation_params.get('emo_ref_path'),
            emo_alpha=generation_params.get('emo_weight', 1.0),
            emo_vector=generation_params.get('emo_vector'),
            use_emo_text=generation_params.get('use_emo_text', False),
            emo_text=generation_params.get('emo_text'),
            use_random=generation_params.get('use_random', False),
            verbose=generation_params.get('verbose', False),
            max_text_tokens_per_segment=generation_params.get('max_text_tokens_per_segment', 120),
            **generation_params.get('generation_kwargs', {})
        )
        
        progress_tracker.complete_stage()
        
        # Format conversion stage (if needed)
        output_format = generation_params.get('output_format', 'wav').lower()
        if output_format != 'wav' and result_path:
            progress_tracker.start_stage("Format Conversion", ["Converting to target format"])
            self.update_task_progress(task_id, 0.9, "Format Conversion")
            progress_tracker.update_stage_progress(0.5, "Converting audio format")
            
            # Perform actual format conversion
            print(f"🔍 DEBUG: TaskManager 正在执行格式转换 - task_manager.py")
            print(f"   📁 输入文件: {result_path}")
            print(f"   🎵 目标格式: {output_format}")
            
            try:
                # Get format converter from enhanced webui if available
                if hasattr(self, 'enhanced_webui') and self.enhanced_webui:
                    format_converter = self.enhanced_webui.get_format_converter()
                    
                    if output_format == "mp3":
                        bitrate = generation_params.get('mp3_bitrate', 128)
                        print(f"   🎚️ MP3 比特率: {bitrate} kbps")
                        
                        # Create output path
                        output_path = result_path.replace('.wav', '.mp3')
                        
                        # This should trigger our enhanced logging
                        converted_path = format_converter.convert_to_format(
                            result_path, "mp3", 
                            bitrate=bitrate,
                            output_path=output_path
                        )
                        
                        # Update result path to the converted file
                        result_path = converted_path
                        print(f"✅ TaskManager 格式转换完成: {result_path}")
                    
                    elif output_format == "m4b":
                        # Handle M4B conversion
                        chapters = generation_params.get('chapters', [])
                        metadata = generation_params.get('metadata', {})
                        converted_path = format_converter.create_m4b_audiobook([result_path], chapters, metadata)
                        result_path = converted_path
                        print(f"✅ TaskManager M4B 转换完成: {result_path}")
                
                else:
                    print("⚠️  无法获取格式转换器，跳过转换")
                    import time
                    time.sleep(0.3)  # Fallback simulation
                    
            except Exception as e:
                print(f"❌ TaskManager 格式转换失败: {e}")
                import time
                time.sleep(0.3)  # Fallback simulation
            
            progress_tracker.update_stage_progress(1.0, "Format conversion complete")
            progress_tracker.complete_stage()
        
        # Complete the task
        self.complete_task(task_id, result_path=result_path)
    
    def _process_generic_task(self, task_id: str, task_type: str, params: Dict[str, Any], progress_tracker):
        """
        Process a generic task with actual TTS processing (no longer simulated).
        
        Args:
            task_id: ID of the task
            task_type: Type of task to process
            params: Task parameters
            progress_tracker: Progress tracker for this task
        """
        print(f"🔍 DEBUG: TaskManager._process_generic_task 被调用 - task_manager.py")
        print(f"   📋 任务ID: {task_id}")
        print(f"   📋 任务类型: {task_type}")
        
        try:
            # Get TTS engine from parameters
            tts_engine = params.get('tts_engine')
            if not tts_engine:
                print(f"❌ 错误: 未提供 TTS 引擎")
                raise ValueError("TTS engine not provided in task parameters")
            
            # Get generation parameters
            text = params.get('text', '')
            voice_prompt = params.get('voice_prompt', '')
            output_path = params.get('output_path', f'outputs/task_{task_id}.wav')
            generation_kwargs = params.get('generation_kwargs', {})
            
            print(f"   📝 文本长度: {len(text)} 字符")
            print(f"   🎤 语音提示: {voice_prompt}")
            print(f"   📁 输出路径: {output_path}")
            
            # Start text processing stage
            progress_tracker.start_stage("Text Processing", ["Loading text", "Cleaning", "Segmentation"])
            self.update_task_progress(task_id, 0.05, "Text Processing")
            progress_tracker.update_stage_progress(0.3, "Loading text content")
            
            # Actual text processing (if needed)
            if hasattr(tts_engine, 'preprocess_text'):
                processed_text = tts_engine.preprocess_text(text)
            else:
                processed_text = text
            
            progress_tracker.update_stage_progress(0.7, "Cleaning and formatting text")
            progress_tracker.update_stage_progress(1.0, "Text segmentation complete")
            progress_tracker.complete_stage()
            
            # Model loading stage (models should already be loaded)
            progress_tracker.start_stage("Model Loading", ["Checking models", "Initializing"])
            self.update_task_progress(task_id, 0.15, "Model Loading")
            progress_tracker.update_stage_progress(0.5, "Checking model status")
            progress_tracker.update_stage_progress(1.0, "Models ready")
            progress_tracker.complete_stage()
            
            # Audio generation stage (actual TTS processing)
            progress_tracker.start_stage("Audio Generation", ["TTS Inference"])
            self.update_task_progress(task_id, 0.25, "Audio Generation")
            
            print(f"🎵 开始实际 TTS 生成...")
            
            # Call actual TTS inference
            result_path = tts_engine.infer(
                text=processed_text,
                voice_prompt=voice_prompt,
                output_path=output_path,
                **generation_kwargs
            )
            
            print(f"✅ TTS 生成完成: {result_path}")
            progress_tracker.update_stage_progress(1.0, "Audio generation complete")
            progress_tracker.complete_stage()
            
            # Format conversion stage (already fixed)
            output_format = params.get('output_format', 'wav').lower()
            if output_format != 'wav' and result_path:
                progress_tracker.start_stage("Format Conversion", ["Converting to target format"])
                self.update_task_progress(task_id, 0.9, "Format Conversion")
                progress_tracker.update_stage_progress(0.5, "Converting audio format")
                
                print(f"🔍 DEBUG: TaskManager 正在执行格式转换 - task_manager.py")
                print(f"   📁 输入文件: {result_path}")
                print(f"   🎵 目标格式: {output_format}")
                
                try:
                    # Get format converter from enhanced webui if available
                    if hasattr(self, 'enhanced_webui') and self.enhanced_webui:
                        format_converter = self.enhanced_webui.get_format_converter()
                        
                        if output_format == "mp3":
                            bitrate = params.get('mp3_bitrate', 128)
                            print(f"   🎚️ MP3 比特率: {bitrate} kbps")
                            
                            # Create output path
                            converted_output_path = result_path.replace('.wav', '.mp3')
                            
                            # This should trigger our enhanced logging
                            converted_path = format_converter.convert_to_format(
                                result_path, "mp3", 
                                bitrate=bitrate,
                                output_path=converted_output_path
                            )
                            
                            # Update result path to the converted file
                            result_path = converted_path
                            print(f"✅ TaskManager 格式转换完成: {result_path}")
                        
                        elif output_format == "m4b":
                            # Handle M4B conversion
                            chapters = params.get('chapters', [])
                            metadata = params.get('metadata', {})
                            converted_path = format_converter.create_m4b_audiobook([result_path], chapters, metadata)
                            result_path = converted_path
                            print(f"✅ TaskManager M4B 转换完成: {result_path}")
                    
                    else:
                        print("⚠️  无法获取格式转换器，跳过转换")
                        
                except Exception as e:
                    print(f"❌ TaskManager 格式转换失败: {e}")
                
                progress_tracker.update_stage_progress(1.0, "Format conversion complete")
                progress_tracker.complete_stage()
            
            # File saving stage (file should already be saved by TTS engine)
            progress_tracker.start_stage("File Saving", ["Verifying output file"])
            self.update_task_progress(task_id, 0.95, "File Saving")
            progress_tracker.update_stage_progress(0.5, "Verifying audio file")
            
            # Verify the output file exists
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"✅ 输出文件验证成功: {result_path} ({file_size / 1024 / 1024:.2f} MB)")
            else:
                print(f"⚠️  警告: 输出文件不存在: {result_path}")
            
            progress_tracker.update_stage_progress(1.0, "File verification complete")
            progress_tracker.complete_stage()
            
            # Complete the task with actual result
            print(f"🎉 任务完成: {task_id}")
            self.complete_task(task_id, result_path=result_path)
            
        except Exception as e:
            print(f"❌ 任务处理失败: {task_id} - {e}")
            import traceback
            traceback.print_exc()
            self.fail_task(task_id, str(e))
    
    def _process_task_basic(self, task_id: str, task_type: str, params: Dict[str, Any]):
        """
        Basic task processing with actual TTS processing (no longer simulated).
        
        Args:
            task_id: ID of the task
            task_type: Type of task to process
            params: Task parameters
        """
        print(f"🔍 DEBUG: TaskManager._process_task_basic 被调用 - task_manager.py")
        print(f"   📋 任务ID: {task_id}")
        print(f"   📋 任务类型: {task_type}")
        
        try:
            # Get TTS engine from parameters
            tts_engine = params.get('tts_engine')
            if not tts_engine:
                print(f"❌ 错误: 未提供 TTS 引擎")
                raise ValueError("TTS engine not provided in task parameters")
            
            # Get generation parameters
            text = params.get('text', '')
            voice_prompt = params.get('voice_prompt', '')
            output_path = params.get('output_path', f'outputs/task_{task_id}.wav')
            generation_kwargs = params.get('generation_kwargs', {})
            
            print(f"   📝 文本: {text[:50]}..." if len(text) > 50 else f"   📝 文本: {text}")
            print(f"   🎤 语音提示: {voice_prompt}")
            print(f"   📁 输出路径: {output_path}")
            
            # Basic processing with actual TTS
            self.update_task_progress(task_id, 0.1, "Initializing")
            print(f"🔧 初始化 TTS 处理...")
            
            self.update_task_progress(task_id, 0.5, "Processing")
            print(f"🎵 执行 TTS 生成...")
            
            # Call actual TTS inference
            result_path = tts_engine.infer(
                text=text,
                voice_prompt=voice_prompt,
                output_path=output_path,
                **generation_kwargs
            )
            
            self.update_task_progress(task_id, 0.9, "Finalizing")
            print(f"✅ TTS 生成完成: {result_path}")
            
            # Verify the output file exists
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"✅ 输出文件验证成功: {result_path} ({file_size / 1024 / 1024:.2f} MB)")
            else:
                print(f"⚠️  警告: 输出文件不存在: {result_path}")
            
            # Complete the task with actual result
            print(f"🎉 基础任务完成: {task_id}")
            self.complete_task(task_id, result_path=result_path)
            
        except Exception as e:
            print(f"❌ 基础任务处理失败: {task_id} - {e}")
            import traceback
            traceback.print_exc()
            self.fail_task(task_id, str(e))
    
    def get_task_progress(self, task_id: str) -> Optional[Dict]:
        """
        Get detailed progress information for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Progress summary dictionary or None if task not found
        """
        return self.console_manager.get_task_progress(task_id)
    
    def get_all_progress(self) -> Dict[str, Dict]:
        """
        Get progress summaries for all active tasks.
        
        Returns:
            Dictionary mapping task IDs to progress summaries
        """
        return self.console_manager.get_all_progress()
    
    def add_console_callback(self, callback: Callable):
        """
        Add callback for console output from all tasks.
        
        Args:
            callback: Function to call with console messages
        """
        self.console_manager.add_output_callback(callback)
    
    def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for a completed task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task results or None if not available
        """
        return self.result_manager.get_task_result(task_id)
    
    def get_download_link(self, task_id: str) -> Optional[str]:
        """
        Get download link for task results.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Download link or None if not available
        """
        return self.result_manager.get_download_link(task_id)
    
    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available task results.
        
        Returns:
            Dictionary mapping task IDs to result summaries
        """
        return self.result_manager.get_all_results()
    
    def create_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]):
        """
        Create a checkpoint for task recovery.
        
        Args:
            task_id: ID of the task
            checkpoint_data: Data to save for recovery
        """
        self.state_manager.create_checkpoint(task_id, checkpoint_data)
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """
        Get recovery and error handling statistics.
        
        Returns:
            Dictionary with recovery statistics
        """
        return {
            'recovery_manager': self.recovery_manager.get_recovery_stats(),
            'persistence': self.state_manager.get_persistence_stats(),
            'results': len(self.result_manager.get_all_results())
        }
    
    def _process_task_with_recovery(self, task_id: str, task_type: str, params: Dict[str, Any]):
        """
        Process task with error handling and recovery.
        
        Args:
            task_id: ID of the task
            task_type: Type of task to process
            params: Task parameters
        """
        max_recovery_attempts = 3
        attempt = 0
        
        while attempt < max_recovery_attempts:
            try:
                # Save task state before processing
                task_status = self.get_task_status(task_id)
                if task_status:
                    self.state_manager.save_task_state(task_status)
                
                # Process the task
                self._process_task(task_id, task_type, params)
                
                # If successful, clean up recovery tracking
                self.recovery_manager.cleanup_task_recovery(task_id)
                return
                
            except Exception as e:
                attempt += 1
                
                # Classify and handle the error
                error_type = self.error_handler.classify_error(e, {
                    'task_id': task_id,
                    'task_type': task_type,
                    'attempt': attempt,
                    'stage': 'task_processing'
                })
                
                # Attempt recovery
                should_retry = self.recovery_manager.attempt_recovery(
                    task_id, error_type, e, {'attempt': attempt}
                )
                
                if not should_retry or attempt >= max_recovery_attempts:
                    # Recovery failed or max attempts reached
                    raise e
                
                # Wait before retry
                retry_delay = self.recovery_manager.get_recovery_delay(task_id, error_type)
                if retry_delay > 0:
                    time.sleep(retry_delay)
                
                # Update task status to show retry attempt
                self.update_task_progress(
                    task_id, 
                    0.0, 
                    f"Retrying after error (attempt {attempt + 1}/{max_recovery_attempts})"
                )
    
    def _restore_active_tasks(self):
        """Restore active tasks from persistence."""
        if not self.config.enable_persistence:
            return
        
        try:
            active_tasks = self.state_manager.get_all_active_tasks()
            
            for task_id, task_status in active_tasks.items():
                # Restore task to our tracking
                with self._lock:
                    self.tasks[task_id] = task_status
                
                # Check if task was processing when system stopped
                if task_status.status == TaskStatusEnum.PROCESSING:
                    # Reset to queued for reprocessing
                    task_status.status = TaskStatusEnum.QUEUED
                    task_status.current_stage = "Restored from persistence"
                    self._update_task_timestamp(task_id)
                    
                    # Re-queue the task
                    task_type = task_status.metadata.get('task_type', 'unknown')
                    params = task_status.metadata.get('params', {})
                    
                    try:
                        self.task_queue.put((task_id, task_type, params), block=False)
                    except:
                        # Queue is full, mark task as failed
                        self.complete_task(task_id, error_message="Failed to restore: queue full")
                        
        except Exception as e:
            print(f"Error restoring active tasks: {e}")
    
    def _update_task_timestamp(self, task_id: str):
        """Update the task's updated_at timestamp."""
        task = self.tasks.get(task_id)
        if task:
            from datetime import datetime
            task.updated_at = datetime.now()
            
            # Save updated state to persistence
            if self.config.enable_persistence:
                self.state_manager.save_task_state(task)