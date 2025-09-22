"""
File management for incremental auto-save functionality.
"""

import os
import tempfile
import shutil
import torch
import torchaudio
import wave
import struct
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


class AutoSaveFileManager:
    """Manages file operations for incremental audio saving."""
    
    def __init__(self, base_output_path: str):
        """
        Initialize the file manager.
        
        Args:
            base_output_path: Base path for output files
        """
        self.base_output_path = base_output_path
        self.temp_dir = self._create_temp_directory()
        self.backup_files: List[str] = []
        self.current_temp_file: Optional[str] = None
        self.sampling_rate = 22050  # Default sampling rate
        self.fallback_locations = self._get_fallback_locations()
        self.save_attempts = 0
        self.max_save_attempts = 3
        
        # Store naming information for consistent filename generation
        self.voice_name: Optional[str] = None
        self.source_filename: Optional[str] = None
    
    def _create_temp_directory(self) -> str:
        """Create temporary directory for auto-save operations."""
        temp_dir = tempfile.mkdtemp(prefix="indextts_autosave_")
        return temp_dir
    
    def _get_fallback_locations(self) -> List[str]:
        """Get list of fallback save locations in order of preference."""
        fallback_dirs = []
        
        # User's home temp directory
        home_temp = os.path.expanduser("~/tmp/indextts_autosave")
        fallback_dirs.append(home_temp)
        
        # System temp directory
        system_temp = os.path.join(tempfile.gettempdir(), "indextts_autosave")
        fallback_dirs.append(system_temp)
        
        # Current working directory temp
        cwd_temp = os.path.join(os.getcwd(), "temp_autosave")
        fallback_dirs.append(cwd_temp)
        
        return fallback_dirs
    
    def set_naming_info(self, voice_name: Optional[str] = None, source_filename: Optional[str] = None):
        """
        Set voice name and source filename for consistent naming.
        
        Args:
            voice_name: Name of the voice being used for generation
            source_filename: Original source filename if from uploaded file
        """
        self.voice_name = voice_name
        self.source_filename = source_filename
    
    def _ensure_directory_exists(self, directory: str) -> bool:
        """Ensure directory exists and is writable."""
        try:
            os.makedirs(directory, exist_ok=True)
            # Test write access
            test_file = os.path.join(directory, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception:
            return False
    
    def generate_incremental_filename(self, step: int) -> str:
        """
        Generate filename for incremental save.
        
        Args:
            step: Current generation step
            
        Returns:
            Temporary file path for incremental save
        """
        base_name = Path(self.base_output_path).stem
        temp_filename = f"{base_name}_step_{step:04d}.wav"
        temp_path = os.path.join(self.temp_dir, temp_filename)
        return temp_path
    
    def generate_consistent_filename(self, voice_name: Optional[str] = None, 
                                   source_filename: Optional[str] = None) -> str:
        """
        Generate filename following existing naming conventions.
        Implements requirement 3.1, 3.2, 3.3: consistent file naming.
        
        Args:
            voice_name: Name of the voice being used
            source_filename: Original filename if from uploaded file
            
        Returns:
            Generated filename following conventions
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if source_filename:
            # From uploaded file: filename + date + voice_name + extension
            base_name = Path(source_filename).stem
            if voice_name:
                filename = f"{base_name}_{timestamp}_{voice_name}.wav"
            else:
                filename = f"{base_name}_{timestamp}.wav"
        else:
            # From direct text input: generation_date + voice_name + extension
            if voice_name:
                filename = f"generation_{timestamp}_{voice_name}.wav"
            else:
                filename = f"generation_{timestamp}.wav"
        
        return filename    

    def save_audio_incremental(self, audio: torch.Tensor, step: int, 
                             sampling_rate: Optional[int] = None) -> str:
        """
        Save audio incrementally to temporary file.
        
        Args:
            audio: Audio tensor to save
            step: Current generation step
            sampling_rate: Audio sampling rate (uses default if None)
            
        Returns:
            Path to saved temporary file
        """
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate
        
        # Generate temporary file path
        temp_path = self.generate_incremental_filename(step)
        
        # Ensure audio is in correct format for saving
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)  # Add channel dimension
        
        # Clamp audio values to prevent clipping
        audio = torch.clamp(audio, -1.0, 1.0)
        
        # Save audio file
        try:
            torchaudio.save(temp_path, audio, self.sampling_rate)
            self.current_temp_file = temp_path
            return temp_path
        except Exception as e:
            raise RuntimeError(f"Failed to save audio to {temp_path}: {str(e)}")
    
    def append_audio_to_file(self, audio: torch.Tensor, target_file: str, 
                           sampling_rate: Optional[int] = None) -> str:
        """
        Append new audio data to existing WAV file.
        
        Args:
            audio: Audio tensor to append
            target_file: Path to existing WAV file to append to
            sampling_rate: Audio sampling rate (uses default if None)
            
        Returns:
            Path to updated file
        """
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate
        
        # Ensure audio is in correct format
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)  # Add channel dimension
        
        # Clamp audio values to prevent clipping
        audio = torch.clamp(audio, -1.0, 1.0)
        
        try:
            if os.path.exists(target_file):
                # Load existing audio
                existing_audio, existing_sr = torchaudio.load(target_file)
                
                # Verify sampling rates match
                if existing_sr != self.sampling_rate:
                    raise ValueError(f"Sampling rate mismatch: existing={existing_sr}, new={self.sampling_rate}")
                
                # Concatenate audio
                combined_audio = torch.cat([existing_audio, audio], dim=1)
            else:
                # First save - just use the new audio
                combined_audio = audio
            
            # Save combined audio
            torchaudio.save(target_file, combined_audio, self.sampling_rate)
            self.current_temp_file = target_file
            return target_file
            
        except Exception as e:
            raise RuntimeError(f"Failed to append audio to {target_file}: {str(e)}")
    
    def save_audio_incremental_append(self, audio: torch.Tensor, 
                                    sampling_rate: Optional[int] = None,
                                    voice_name: Optional[str] = None,
                                    source_filename: Optional[str] = None) -> str:
        """
        Save audio incrementally by appending to the same file with consistent naming.
        This implements requirement 2.3: append new audio to existing file.
        Implements requirement 3.1, 3.2: consistent file naming from first save.
        
        Args:
            audio: Audio tensor to save
            sampling_rate: Audio sampling rate (uses default if None)
            voice_name: Name of the voice being used for generation
            source_filename: Original source filename if from uploaded file
            
        Returns:
            Path to incremental save file
        """
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate
        
        # Use consistent filename for incremental saves
        if not self.current_temp_file:
            # First save - create the file with consistent naming
            consistent_filename = self.generate_consistent_filename(voice_name, source_filename)
            # Use temp directory but with consistent filename
            temp_filename = f"temp_{consistent_filename}"
            self.current_temp_file = os.path.join(self.temp_dir, temp_filename)
        
        # Append to existing file
        return self.append_audio_to_file(audio, self.current_temp_file, sampling_rate)
    
    def create_backup(self, source_path: str) -> str:
        """
        Create backup of current progress.
        
        Args:
            source_path: Path to file to backup
            
        Returns:
            Path to backup file
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{Path(source_path).name}"
        backup_path = os.path.join(self.temp_dir, backup_name)
        
        # Copy file to backup location
        shutil.copy2(source_path, backup_path)
        self.backup_files.append(backup_path)
        
        return backup_path 
   
    def finalize_output(self, temp_path: Optional[str] = None, final_path: Optional[str] = None,
                       voice_name: Optional[str] = None, source_filename: Optional[str] = None) -> str:
        """
        Move temporary file to final output location with proper naming.
        Implements requirement 3.5: maintain same name established at first auto-save.
        
        Args:
            temp_path: Path to temporary file (uses current_temp_file if None)
            final_path: Final output path (generates if None)
            voice_name: Voice name for filename generation
            source_filename: Source filename for naming convention
            
        Returns:
            Final output path
        """
        # Use current temp file if not specified
        if temp_path is None:
            temp_path = self.current_temp_file
        
        if not temp_path or not os.path.exists(temp_path):
            raise FileNotFoundError(f"Temporary file not found: {temp_path}")
        
        # Generate final path if not provided
        if final_path is None:
            filename = self.generate_consistent_filename(voice_name, source_filename)
            final_dir = os.path.dirname(self.base_output_path)
            
            # Handle case where base_output_path is just a filename (no directory)
            if not final_dir:
                final_dir = os.getcwd()  # Use current working directory
            
            final_path = os.path.join(final_dir, filename)
        
        # Ensure output directory exists
        final_dir = os.path.dirname(final_path)
        if final_dir:  # Only create directory if there is one
            os.makedirs(final_dir, exist_ok=True)
        
        # Validate temp file before moving
        validation = self.validate_audio_file(temp_path)
        if not validation['valid']:
            raise RuntimeError(f"Cannot finalize invalid audio file: {validation['errors']}")
        
        # Move file to final location
        shutil.move(temp_path, final_path)
        
        # Update current temp file reference
        if self.current_temp_file == temp_path:
            self.current_temp_file = None
        
        return final_path
    
    def cleanup_temp_files(self, preserve_current: bool = False):
        """
        Clean up all temporary and backup files.
        Implements requirement 2.7, 6.6: proper resource cleanup.
        
        Args:
            preserve_current: If True, keep the current temp file for recovery
        """
        cleanup_summary = {
            'backups_removed': 0,
            'backups_failed': 0,
            'temp_file_removed': False,
            'temp_dir_removed': False,
            'fallback_dirs_cleaned': 0,
            'total_size_freed_mb': 0.0,
            'errors': []
        }
        
        total_size_freed = 0
        
        # Clean up backup files
        for backup_path in self.backup_files:
            try:
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)
                    os.remove(backup_path)
                    cleanup_summary['backups_removed'] += 1
                    total_size_freed += file_size
            except Exception as e:
                cleanup_summary['backups_failed'] += 1
                cleanup_summary['errors'].append(f"Failed to remove backup {backup_path}: {e}")
        
        self.backup_files.clear()
        
        # Clean up current temp file (unless preserving for recovery)
        if not preserve_current and self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                file_size = os.path.getsize(self.current_temp_file)
                os.remove(self.current_temp_file)
                cleanup_summary['temp_file_removed'] = True
                total_size_freed += file_size
                self.current_temp_file = None
            except Exception as e:
                cleanup_summary['errors'].append(f"Failed to remove temp file {self.current_temp_file}: {e}")
        
        # Clean up temporary directory (only if empty or not preserving)
        if not preserve_current:
            try:
                if os.path.exists(self.temp_dir):
                    # Calculate directory size before removal
                    dir_size = self._calculate_directory_size(self.temp_dir)
                    shutil.rmtree(self.temp_dir)
                    cleanup_summary['temp_dir_removed'] = True
                    total_size_freed += dir_size
            except Exception as e:
                cleanup_summary['errors'].append(f"Failed to remove temp directory {self.temp_dir}: {e}")
        
        # Clean up fallback directories if they were used
        for fallback_dir in self.fallback_locations:
            try:
                if os.path.exists(fallback_dir):
                    # Only clean up files that match our naming pattern
                    cleaned_files = self._cleanup_fallback_directory(fallback_dir)
                    if cleaned_files > 0:
                        cleanup_summary['fallback_dirs_cleaned'] += 1
            except Exception as e:
                cleanup_summary['errors'].append(f"Failed to clean fallback directory {fallback_dir}: {e}")
        
        cleanup_summary['total_size_freed_mb'] = total_size_freed / (1024**2)
        return cleanup_summary
    
    def _calculate_directory_size(self, directory: str) -> int:
        """
        Calculate total size of directory in bytes.
        
        Args:
            directory: Path to directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception:
            pass  # Return 0 if calculation fails
        return total_size
    
    def _cleanup_fallback_directory(self, fallback_dir: str) -> int:
        """
        Clean up files in fallback directory that match our naming patterns.
        
        Args:
            fallback_dir: Path to fallback directory
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        try:
            if not os.path.exists(fallback_dir):
                return 0
            
            # Look for files with our naming patterns
            patterns = [
                "temp_generation_*",
                "temp_*_step_*",
                "emergency_save_*",
                "backup_*"
            ]
            
            for file in os.listdir(fallback_dir):
                file_path = os.path.join(fallback_dir, file)
                if os.path.isfile(file_path):
                    # Check if file matches our patterns
                    for pattern in patterns:
                        import fnmatch
                        if fnmatch.fnmatch(file, pattern):
                            try:
                                os.remove(file_path)
                                cleaned_count += 1
                                break
                            except Exception:
                                pass  # Continue with other files
        except Exception:
            pass  # Return count of successfully cleaned files
        
        return cleaned_count
    
    def cleanup_on_cancellation(self, preserve_partial: bool = True) -> Dict[str, Any]:
        """
        Specialized cleanup for generation cancellation.
        Implements requirement 5.4: proper resource cleanup on generation cancellation.
        
        Args:
            preserve_partial: If True, preserve partial results for recovery
            
        Returns:
            Dictionary with cleanup results
        """
        cancellation_cleanup = {
            'partial_preserved': False,
            'partial_path': None,
            'backup_created': False,
            'backup_path': None,
            'temp_cleanup': None,
            'recovery_available': False,
            'errors': []
        }
        
        try:
            # Preserve current temp file if requested and available
            if preserve_partial and self.current_temp_file and os.path.exists(self.current_temp_file):
                # Validate the current temp file
                validation = self.validate_audio_file(self.current_temp_file)
                if validation['valid']:
                    # Create a backup with cancellation marker
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    cancelled_filename = f"cancelled_{timestamp}_{Path(self.current_temp_file).name}"
                    cancelled_path = os.path.join(self.temp_dir, cancelled_filename)
                    
                    try:
                        shutil.copy2(self.current_temp_file, cancelled_path)
                        cancellation_cleanup['partial_preserved'] = True
                        cancellation_cleanup['partial_path'] = cancelled_path
                        
                        # Create additional backup
                        backup_path = self.create_backup(cancelled_path)
                        cancellation_cleanup['backup_created'] = True
                        cancellation_cleanup['backup_path'] = backup_path
                        cancellation_cleanup['recovery_available'] = True
                        
                    except Exception as e:
                        cancellation_cleanup['errors'].append(f"Failed to preserve partial results: {e}")
            
            # Perform selective cleanup - preserve recovery files
            temp_cleanup = self.cleanup_temp_files(preserve_current=preserve_partial)
            cancellation_cleanup['temp_cleanup'] = temp_cleanup
            
        except Exception as e:
            cancellation_cleanup['errors'].append(f"Cancellation cleanup error: {e}")
        
        return cancellation_cleanup
    
    def recover_from_backup(self) -> Dict[str, Any]:
        """
        Recover audio from most recent backup.
        Implements requirement 5.4, 5.5: recovery mechanisms for partial generation failures.
        
        Returns:
            Dictionary with recovery information
        """
        recovery_info = {
            'success': False,
            'backup_path': None,
            'backup_count': len(self.backup_files),
            'current_temp_available': False,
            'validation': None,
            'errors': []
        }
        
        # Check if current temp file is available
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            recovery_info['current_temp_available'] = True
            validation = self.validate_audio_file(self.current_temp_file)
            if validation['valid']:
                recovery_info['success'] = True
                recovery_info['backup_path'] = self.current_temp_file
                recovery_info['validation'] = validation
                return recovery_info
        
        # Try to recover from backups
        if not self.backup_files:
            recovery_info['errors'].append("No backup files available")
            return recovery_info
        
        # Check backups from most recent to oldest
        for backup_path in reversed(self.backup_files):
            if os.path.exists(backup_path):
                validation = self.validate_audio_file(backup_path)
                if validation['valid']:
                    recovery_info['success'] = True
                    recovery_info['backup_path'] = backup_path
                    recovery_info['validation'] = validation
                    return recovery_info
                else:
                    recovery_info['errors'].append(f"Backup {backup_path} is invalid: {validation['errors']}")
            else:
                recovery_info['errors'].append(f"Backup file missing: {backup_path}")
        
        recovery_info['errors'].append("No valid backup files found")
        return recovery_info
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """
        Get current recovery status and available options.
        
        Returns:
            Dictionary with recovery status information
        """
        status = {
            'current_temp_file': self.current_temp_file,
            'temp_file_exists': False,
            'temp_file_valid': False,
            'backup_count': len(self.backup_files),
            'valid_backups': 0,
            'total_duration': 0.0,
            'last_save_size': 0
        }
        
        # Check current temp file
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            status['temp_file_exists'] = True
            validation = self.validate_audio_file(self.current_temp_file)
            status['temp_file_valid'] = validation['valid']
            if validation['valid']:
                status['total_duration'] = validation['duration_seconds']
                status['last_save_size'] = validation['size_bytes']
        
        # Check backup files
        for backup_path in self.backup_files:
            if os.path.exists(backup_path):
                validation = self.validate_audio_file(backup_path)
                if validation['valid']:
                    status['valid_backups'] += 1
        
        return status    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate integrity of saved audio file with detailed results.
        
        Args:
            file_path: Path to audio file to validate
            
        Returns:
            Dictionary with validation results and details
        """
        validation_result = {
            'valid': False,
            'exists': False,
            'size_bytes': 0,
            'duration_seconds': 0.0,
            'sample_rate': 0,
            'channels': 0,
            'errors': []
        }
        
        try:
            if not os.path.exists(file_path):
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            validation_result['exists'] = True
            validation_result['size_bytes'] = os.path.getsize(file_path)
            
            # Check file size
            if validation_result['size_bytes'] == 0:
                validation_result['errors'].append("File is empty")
                return validation_result
            
            # Try to load audio file
            audio, sr = torchaudio.load(file_path)
            validation_result['sample_rate'] = sr
            validation_result['channels'] = audio.shape[0] if audio.dim() > 1 else 1
            validation_result['duration_seconds'] = audio.shape[-1] / sr if sr > 0 else 0
            
            # Basic validation checks
            if audio.numel() == 0:
                validation_result['errors'].append("Audio tensor is empty")
                return validation_result
            
            if sr <= 0:
                validation_result['errors'].append(f"Invalid sample rate: {sr}")
                return validation_result
            
            # Check for reasonable audio values
            if torch.isnan(audio).any():
                validation_result['errors'].append("Audio contains NaN values")
                return validation_result
                
            if torch.isinf(audio).any():
                validation_result['errors'].append("Audio contains infinite values")
                return validation_result
            
            # Check audio range
            audio_min, audio_max = audio.min().item(), audio.max().item()
            if audio_max > 1.0 or audio_min < -1.0:
                validation_result['errors'].append(f"Audio values out of range: [{audio_min:.3f}, {audio_max:.3f}]")
            
            # If we get here, file is valid
            validation_result['valid'] = True
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'exists': False,
            'size_bytes': 0,
            'duration_seconds': 0.0,
            'sample_rate': 0,
            'channels': 0,
            'valid': False
        }
        
        try:
            if os.path.exists(file_path):
                info['exists'] = True
                info['size_bytes'] = os.path.getsize(file_path)
                
                # Load audio to get detailed info
                audio, sr = torchaudio.load(file_path)
                info['sample_rate'] = sr
                info['channels'] = audio.shape[0] if audio.dim() > 1 else 1
                info['duration_seconds'] = audio.shape[-1] / sr
                info['valid'] = self.validate_audio_file(file_path)
                
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def save_audio_with_fallback(self, audio: torch.Tensor, filename: str, 
                                sampling_rate: Optional[int] = None) -> Dict[str, Any]:
        """
        Save audio with fallback locations and retry logic.
        Implements requirement 5.3: fallback save locations when primary location fails.
        
        Args:
            audio: Audio tensor to save
            filename: Desired filename
            sampling_rate: Audio sampling rate
            
        Returns:
            Dictionary with save result information
        """
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate
        
        save_result = {
            'success': False,
            'file_path': None,
            'attempts': 0,
            'errors': [],
            'fallback_used': False
        }
        
        # Ensure audio is in correct format
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)
        audio = torch.clamp(audio, -1.0, 1.0)
        
        # Try primary location first
        primary_path = os.path.join(self.temp_dir, filename)
        locations_to_try = [self.temp_dir] + self.fallback_locations
        
        for i, location in enumerate(locations_to_try):
            save_result['attempts'] += 1
            
            try:
                # Ensure directory exists and is writable
                if not self._ensure_directory_exists(location):
                    save_result['errors'].append(f"Cannot access directory: {location}")
                    continue
                
                file_path = os.path.join(location, filename)
                
                # Save the audio
                torchaudio.save(file_path, audio, self.sampling_rate)
                
                # Validate the saved file
                validation = self.validate_audio_file(file_path)
                if not validation['valid']:
                    save_result['errors'].append(f"Validation failed at {file_path}: {validation['errors']}")
                    continue
                
                # Success!
                save_result['success'] = True
                save_result['file_path'] = file_path
                save_result['fallback_used'] = (i > 0)
                
                if i > 0:
                    # Update temp_dir to successful fallback location
                    self.temp_dir = location
                
                return save_result
                
            except Exception as e:
                save_result['errors'].append(f"Save failed at {location}: {str(e)}")
                continue
        
        # All locations failed
        save_result['errors'].append("All save locations failed")
        return save_result
    
    def save_audio_incremental_robust(self, audio: torch.Tensor, 
                                    sampling_rate: Optional[int] = None) -> Dict[str, Any]:
        """
        Robust incremental save with fallback and validation.
        Implements requirements 2.3, 3.4, 5.1, 5.2, 5.3.
        
        Args:
            audio: Audio tensor to save
            sampling_rate: Audio sampling rate
            
        Returns:
            Dictionary with save operation results
        """
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate
        
        # Generate consistent filename for incremental saves
        if not self.current_temp_file:
            # Use consistent naming from the start
            consistent_filename = self.generate_consistent_filename(self.voice_name, self.source_filename)
            temp_filename = f"temp_{consistent_filename}"
            
            # Try to save initial file
            save_result = self.save_audio_with_fallback(audio, temp_filename, sampling_rate)
            if save_result['success']:
                self.current_temp_file = save_result['file_path']
            return save_result
        else:
            # Append to existing file
            try:
                # Create backup before appending
                backup_path = self.create_backup(self.current_temp_file)
                
                # Append new audio
                result_path = self.append_audio_to_file(audio, self.current_temp_file, sampling_rate)
                
                # Validate the result
                validation = self.validate_audio_file(result_path)
                
                save_result = {
                    'success': validation['valid'],
                    'file_path': result_path if validation['valid'] else None,
                    'attempts': 1,
                    'errors': validation['errors'] if not validation['valid'] else [],
                    'fallback_used': False,
                    'backup_created': backup_path
                }
                
                if not validation['valid']:
                    # Restore from backup if append failed
                    try:
                        shutil.copy2(backup_path, self.current_temp_file)
                        save_result['errors'].append("Restored from backup after failed append")
                    except Exception as e:
                        save_result['errors'].append(f"Failed to restore backup: {str(e)}")
                
                return save_result
                
            except Exception as e:
                return {
                    'success': False,
                    'file_path': None,
                    'attempts': 1,
                    'errors': [f"Incremental append failed: {str(e)}"],
                    'fallback_used': False
                }