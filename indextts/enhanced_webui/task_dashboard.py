"""
Task status dashboard for monitoring background tasks in the WebUI.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from datetime import datetime, timedelta
from ..task_management import TaskManager, TaskStatus, TaskStatusEnum


class TaskStatusDashboard:
    """Dashboard component for monitoring background tasks."""
    
    # Status icons mapping
    STATUS_ICONS = {
        TaskStatusEnum.QUEUED: "⏳",
        TaskStatusEnum.PROCESSING: "🔄", 
        TaskStatusEnum.COMPLETED: "✅",
        TaskStatusEnum.FAILED: "❌",
        TaskStatusEnum.CANCELLED: "⏹️"
    }
    
    # Status colors for HTML display
    STATUS_COLORS = {
        TaskStatusEnum.QUEUED: "#6c757d",
        TaskStatusEnum.PROCESSING: "#007bff",
        TaskStatusEnum.COMPLETED: "#28a745", 
        TaskStatusEnum.FAILED: "#dc3545",
        TaskStatusEnum.CANCELLED: "#6c757d"
    }
    
    def __init__(self, task_manager: TaskManager):
        """
        Initialize the task dashboard.
        
        Args:
            task_manager: TaskManager instance to monitor
        """
        self.task_manager = task_manager
        self.last_update = datetime.now()
        self.update_interval = 2.0  # seconds
    
    def create_dashboard_components(self) -> Tuple[gr.HTML, gr.Dataframe, gr.HTML, gr.Button]:
        """
        Create the main dashboard components.
        
        Returns:
            Tuple of (status_summary, task_table, detailed_view, refresh_button)
        """
        # Status summary at the top
        status_summary = gr.HTML(
            value=self._generate_status_summary(),
            label="Task Overview"
        )
        
        # Main task table
        task_table = gr.Dataframe(
            headers=["Status", "Task ID", "Progress", "Stage", "Time", "Actions"],
            datatype=["str", "str", "str", "str", "str", "str"],
            label="Active Tasks",
            interactive=False,
            wrap=True,
            max_height=400
        )
        
        # Detailed view for selected task
        detailed_view = gr.HTML(
            value="<p><em>Select a task to view details</em></p>",
            label="Task Details"
        )
        
        # Manual refresh button
        refresh_button = gr.Button(
            "🔄 Refresh Status",
            variant="secondary",
            size="sm"
        )
        
        return status_summary, task_table, detailed_view, refresh_button
    
    def create_progress_components(self) -> Tuple[gr.HTML, gr.HTML]:
        """
        Create components for detailed progress tracking.
        
        Returns:
            Tuple of (progress_bars, console_output)
        """
        # Progress bars for active tasks
        progress_bars = gr.HTML(
            value=self._generate_progress_bars(),
            label="Task Progress"
        )
        
        # Console output display
        console_output = gr.HTML(
            value=self._generate_console_output(),
            label="Console Output",
            elem_classes=["console-output"]
        )
        
        return progress_bars, console_output
    
    def get_dashboard_data(self) -> Tuple[List[List[str]], str, str, str]:
        """
        Get current dashboard data for all components.
        
        Returns:
            Tuple of (task_table_data, status_summary_html, progress_bars_html, console_output_html)
        """
        tasks = self.task_manager.get_all_tasks()
        
        # Generate task table data
        table_data = []
        for task_id, task in tasks.items():
            table_data.append(self._format_task_row(task_id, task))
        
        # Sort by creation time (newest first)
        table_data.sort(key=lambda x: x[4], reverse=True)
        
        # Generate HTML components
        status_summary_html = self._generate_status_summary()
        progress_bars_html = self._generate_progress_bars()
        console_output_html = self._generate_console_output()
        
        return table_data, status_summary_html, progress_bars_html, console_output_html
    
    def get_task_details(self, task_id: str) -> str:
        """
        Get detailed information for a specific task.
        
        Args:
            task_id: ID of the task to get details for
            
        Returns:
            HTML string with detailed task information
        """
        if not task_id:
            return "<p><em>No task selected</em></p>"
        
        # Find task by partial ID match (since table shows shortened IDs)
        tasks = self.task_manager.get_all_tasks()
        matching_task = None
        
        for full_id, task in tasks.items():
            if full_id.startswith(task_id.replace("...", "")):
                matching_task = task
                task_id = full_id
                break
        
        if not matching_task:
            return f"<p><em>Task {task_id} not found</em></p>"
        
        return self._generate_task_details_html(task_id, matching_task)
    
    def _format_task_row(self, task_id: str, task: TaskStatus) -> List[str]:
        """
        Format a task into a table row.
        
        Args:
            task_id: Full task ID
            task: TaskStatus object
            
        Returns:
            List of formatted strings for table row
        """
        # Status with icon
        status_icon = self.STATUS_ICONS.get(task.status, "❓")
        status_text = f"{status_icon} {task.status.value.title()}"
        
        # Shortened task ID
        short_id = task_id[:8] + "..." if len(task_id) > 8 else task_id
        
        # Progress with bar
        progress_percent = int(task.progress * 100)
        progress_text = f"{progress_percent}%"
        if task.status == TaskStatusEnum.PROCESSING:
            progress_text += f" ({self._format_progress_bar(task.progress)})"
        
        # Current stage
        stage = task.current_stage or "Unknown"
        
        # Time information
        if task.status == TaskStatusEnum.PROCESSING and task.estimated_remaining:
            time_info = f"~{self._format_duration(task.estimated_remaining)} left"
        else:
            elapsed = datetime.now() - task.created_at
            time_info = f"{self._format_duration(elapsed.total_seconds())} ago"
        
        # Actions
        actions = self._generate_task_actions(task_id, task)
        
        return [status_text, short_id, progress_text, stage, time_info, actions]
    
    def _generate_status_summary(self) -> str:
        """
        Generate HTML for the status summary section.
        
        Returns:
            HTML string with status summary
        """
        tasks = self.task_manager.get_all_tasks()
        
        if not tasks:
            return '''
            <div style="padding: 15px; text-align: center; color: #6c757d;">
                <h4>No Tasks</h4>
                <p>No background tasks are currently active or completed.</p>
            </div>
            '''
        
        # Count tasks by status
        status_counts = {}
        for task in tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        # Generate summary cards
        cards = []
        for status, count in status_counts.items():
            if count > 0:
                icon = self.STATUS_ICONS.get(status, "❓")
                color = self.STATUS_COLORS.get(status, "#6c757d")
                
                cards.append(f'''
                <div style="display: inline-block; margin: 5px; padding: 10px 15px; 
                           background-color: {color}15; border: 1px solid {color}40; 
                           border-radius: 8px; text-align: center; min-width: 80px;">
                    <div style="font-size: 24px; color: {color};">{icon}</div>
                    <div style="font-weight: bold; color: {color};">{count}</div>
                    <div style="font-size: 12px; color: {color}80;">{status.value.title()}</div>
                </div>
                ''')
        
        cards_html = "".join(cards)
        
        return f'''
        <div style="padding: 15px; border: 1px solid #dee2e6; border-radius: 8px; background-color: #f8f9fa;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">Task Status Overview</h4>
            <div style="text-align: center;">
                {cards_html}
            </div>
            <div style="margin-top: 10px; text-align: center; font-size: 12px; color: #6c757d;">
                Last updated: {datetime.now().strftime("%H:%M:%S")}
            </div>
        </div>
        '''
    
    def _generate_progress_bars(self) -> str:
        """
        Generate HTML for progress bars of active tasks.
        
        Returns:
            HTML string with progress bars
        """
        tasks = self.task_manager.get_all_tasks()
        active_tasks = {tid: task for tid, task in tasks.items() if task.is_active}
        
        if not active_tasks:
            return '''
            <div style="padding: 15px; text-align: center; color: #6c757d;">
                <p>No active tasks to display progress for.</p>
            </div>
            '''
        
        progress_html = []
        
        for task_id, task in active_tasks.items():
            short_id = task_id[:8] + "..."
            progress_percent = int(task.progress * 100)
            
            # Get detailed progress if available
            detailed_progress = self.task_manager.get_task_progress(task_id)
            
            # Progress bar color based on status
            if task.status == TaskStatusEnum.PROCESSING:
                bar_color = "#007bff"
            else:
                bar_color = "#6c757d"
            
            # Build one-line status from detailed progress if available
            status_line = ""
            if detailed_progress and 'status_line' in detailed_progress:
                status_line = detailed_progress['status_line']
            else:
                eta_text = f" • ~{self._format_duration(task.estimated_remaining)} remaining" if task.estimated_remaining else ""
                status_line = f"{progress_percent}% | Stage: {task.current_stage}{eta_text}"
            
            progress_html.append(f'''
            <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #dee2e6; border-radius: 8px; background:#f8f9fa;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: bold;">{short_id}</span>
                    <span style="font-size: 12px; color: #6c757d;">{status_line}</span>
                </div>
                <div style="width: 100%; background-color: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden; margin-bottom: 6px;">
                    <div style="width: {progress_percent}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); transition: width 0.3s ease;"></div>
                </div>
                {self._generate_detailed_progress_html(detailed_progress) if detailed_progress else ""}
            </div>
            ''')
        
        return f'''
        <div style="padding: 15px; border: 1px solid #dee2e6; border-radius: 8px; background-color: #f8f9fa;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">Active Task Progress</h4>
            {"".join(progress_html)}
        </div>
        '''
    
    def _generate_console_output(self) -> str:
        """
        Generate HTML for console output display.
        
        Returns:
            HTML string with console output
        """
        # Get recent console output from all tasks
        all_progress = self.task_manager.get_all_progress()
        
        if not all_progress:
            return '''
            <div style="padding: 15px; text-align: center; color: #6c757d;">
                <p>No console output available.</p>
            </div>
            '''
        
        console_lines = []
        
        for task_id, progress_data in all_progress.items():
            short_id = task_id[:8] + "..."
            
            # Add task header with latest one-line status if available
            status_line = progress_data.get('status_line', '')
            console_lines.append(f'''
            <div style="color: #007bff; font-weight: bold; margin: 10px 0 5px 0;">
                === Task {short_id} === {status_line}
            </div>
            ''')
            
            # Add recent console messages
            if 'console_messages' in progress_data:
                for message in progress_data['console_messages'][-10:]:  # Last 10 messages
                    timestamp = message.get('timestamp', '')
                    text = message.get('message', '')
                    level = message.get('level', 'info')
                    
                    color = {
                        'error': '#dc3545',
                        'warning': '#ffc107', 
                        'info': '#17a2b8',
                        'success': '#28a745'
                    }.get(level, '#6c757d')
                    
                    console_lines.append(f'''
                    <div style="font-family: monospace; font-size: 12px; margin: 2px 0; color: {color};">
                        <span style="color: #6c757d;">[{timestamp}]</span> {text}
                    </div>
                    ''')
        
        return f'''
        <div style="padding: 15px; border: 1px solid #dee2e6; border-radius: 8px; background-color: #f8f9fa;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">Console Output</h4>
            <div style="max-height: 380px; overflow-y: auto; background-color: #ffffff; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px; font-family: monospace; font-size: 12px;">
                {"".join(console_lines) if console_lines else "<p style='color: #6c757d; text-align: center;'>No recent output</p>"}
            </div>
        </div>
        '''
    
    def _generate_task_details_html(self, task_id: str, task: TaskStatus) -> str:
        """
        Generate detailed HTML view for a specific task.
        
        Args:
            task_id: Full task ID
            task: TaskStatus object
            
        Returns:
            HTML string with detailed task information
        """
        status_icon = self.STATUS_ICONS.get(task.status, "❓")
        status_color = self.STATUS_COLORS.get(task.status, "#6c757d")
        
        # Calculate durations
        elapsed = datetime.now() - task.created_at
        elapsed_str = self._format_duration(elapsed.total_seconds())
        
        # Get detailed progress
        detailed_progress = self.task_manager.get_task_progress(task_id)
        
        # Get task results if completed
        results_html = ""
        if task.status == TaskStatusEnum.COMPLETED:
            results = self.task_manager.get_task_results(task_id)
            download_link = self.task_manager.get_download_link(task_id)
            
            if results or download_link:
                results_html = f'''
                <div style="margin-top: 15px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                    <h5 style="margin: 0 0 10px 0; color: #155724;">Results</h5>
                    {f'<p><a href="{download_link}" target="_blank">📥 Download Result</a></p>' if download_link else ''}
                    {f'<pre style="font-size: 11px; color: #155724;">{str(results)}</pre>' if results else ''}
                </div>
                '''
        
        return f'''
        <div style="padding: 15px; border: 1px solid #dee2e6; border-radius: 8px; background-color: #ffffff;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 24px; margin-right: 10px; color: {status_color};">{status_icon}</span>
                <div>
                    <h4 style="margin: 0; color: #495057;">Task Details</h4>
                    <small style="color: #6c757d;">ID: {task_id}</small>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div>
                    <strong>Status:</strong> <span style="color: {status_color};">{task.status.value.title()}</span><br>
                    <strong>Progress:</strong> {int(task.progress * 100)}%<br>
                    <strong>Current Stage:</strong> {task.current_stage}<br>
                </div>
                <div>
                    <strong>Created:</strong> {task.created_at.strftime("%Y-%m-%d %H:%M:%S")}<br>
                    <strong>Elapsed:</strong> {elapsed_str}<br>
                    <strong>Remaining:</strong> {self._format_duration(task.estimated_remaining) if task.estimated_remaining else "Unknown"}<br>
                </div>
            </div>
            
            {f'<div style="margin-bottom: 15px;"><strong>Error:</strong> <span style="color: #dc3545;">{task.error_message}</span></div>' if task.error_message else ''}
            
            {self._generate_detailed_progress_html(detailed_progress) if detailed_progress else ''}
            
            {results_html}
        </div>
        '''
    
    def _generate_detailed_progress_html(self, progress_data: Optional[Dict]) -> str:
        """
        Generate HTML for detailed progress information.
        
        Args:
            progress_data: Progress data dictionary
            
        Returns:
            HTML string with detailed progress
        """
        if not progress_data:
            return ""
        
        html_parts = []
        
        # Current stage details
        if 'current_stage' in progress_data:
            stage_data = progress_data['current_stage']
            html_parts.append(f'''
            <div style="margin-top: 10px; padding: 8px; background-color: #e3f2fd; border-radius: 4px;">
                <strong>Stage:</strong> {stage_data.get('name', 'Unknown')}<br>
                <small>Progress: {int(stage_data.get('progress', 0) * 100)}% • {stage_data.get('current_step', 'Processing...')}</small>
            </div>
            ''')
        
        # Batch timing information
        if 'batch_timings' in progress_data and progress_data['batch_timings']:
            recent_batches = progress_data['batch_timings'][-3:]  # Last 3 batches
            
            batch_html = []
            for batch in recent_batches:
                batch_html.append(f'''
                <div style="font-size: 11px; margin: 2px 0;">
                    Batch {batch.get('batch_number', '?')}/{batch.get('total_batches', '?')}: 
                    {batch.get('batch_time', 0):.2f}s 
                    ({batch.get('items_processed', 0)} items)
                </div>
                ''')
            
            html_parts.append(f'''
            <div style="margin-top: 10px; padding: 8px; background-color: #f8f9fa; border-radius: 4px;">
                <strong>Recent Batches:</strong>
                {"".join(batch_html)}
            </div>
            ''')
        
        return "".join(html_parts)
    
    def _generate_task_actions(self, task_id: str, task: TaskStatus) -> str:
        """
        Generate action buttons for a task.
        
        Args:
            task_id: Task ID
            task: TaskStatus object
            
        Returns:
            HTML string with action buttons
        """
        actions = []
        
        if task.status == TaskStatusEnum.QUEUED:
            actions.append("🗑️ Cancel")
        
        if task.status == TaskStatusEnum.COMPLETED and task.result_path:
            actions.append("📥 Download")
        
        if task.is_complete:
            actions.append("🗑️ Remove")
        
        return " | ".join(actions) if actions else "-"
    
    def _format_progress_bar(self, progress: float, width: int = 10) -> str:
        """
        Format a text-based progress bar.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            width: Width of the progress bar in characters
            
        Returns:
            Text progress bar string
        """
        filled = int(progress * width)
        empty = width - filled
        return "█" * filled + "░" * empty
    
    def _format_duration(self, seconds: Optional[float]) -> str:
        """
        Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "Unknown"
        
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def should_auto_refresh(self) -> bool:
        """
        Check if dashboard should auto-refresh based on active tasks.
        
        Returns:
            True if auto-refresh is needed
        """
        tasks = self.task_manager.get_all_tasks()
        has_active_tasks = any(task.is_active for task in tasks.values())
        
        # Auto-refresh if there are active tasks and enough time has passed
        time_since_update = (datetime.now() - self.last_update).total_seconds()
        
        if has_active_tasks and time_since_update >= self.update_interval:
            self.last_update = datetime.now()
            return True
        
        return False