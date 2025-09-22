"""
Audio format handling utilities for incremental auto-save.
"""

import torch
import torchaudio
import numpy as np
from typing import Tuple, Optional, Union
import warnings


def normalize_audio_tensor(audio: torch.Tensor) -> torch.Tensor:
    """
    Normalize audio tensor for consistent processing.
    
    Args:
        audio: Input audio tensor
        
    Returns:
        Normalized audio tensor
    """
    # Ensure tensor is float
    if audio.dtype != torch.float32:
        audio = audio.float()
    
    # Add channel dimension if needed
    if audio.dim() == 1:
        audio = audio.unsqueeze(0)
    
    # Clamp values to prevent clipping
    audio = torch.clamp(audio, -1.0, 1.0)
    
    return audio


def concatenate_audio_tensors(tensors: list, dim: int = -1) -> torch.Tensor:
    """
    Efficiently concatenate multiple audio tensors.
    
    Args:
        tensors: List of audio tensors to concatenate
        dim: Dimension along which to concatenate (default: last dimension)
        
    Returns:
        Concatenated audio tensor
    """
    if not tensors:
        return torch.empty(0)
    
    if len(tensors) == 1:
        return tensors[0].clone()
    
    # Normalize all tensors to same format
    normalized_tensors = [normalize_audio_tensor(t) for t in tensors]
    
    # Ensure all tensors have same number of dimensions
    max_dims = max(t.dim() for t in normalized_tensors)
    
    aligned_tensors = []
    for tensor in normalized_tensors:
        while tensor.dim() < max_dims:
            tensor = tensor.unsqueeze(0)
        aligned_tensors.append(tensor)
    
    # Concatenate along specified dimension
    return torch.cat(aligned_tensors, dim=dim)


def validate_audio_format(audio: torch.Tensor, sample_rate: int) -> bool:
    """
    Validate audio tensor format and properties.
    
    Args:
        audio: Audio tensor to validate
        sample_rate: Expected sample rate
        
    Returns:
        True if audio format is valid
    """
    try:
        # Check tensor properties
        if not isinstance(audio, torch.Tensor):
            return False
        
        if audio.numel() == 0:
            return False
        
        # Check for invalid values
        if torch.isnan(audio).any() or torch.isinf(audio).any():
            return False
        
        # Check sample rate
        if sample_rate <= 0:
            return False
        
        # Check audio dimensions (should be 1D or 2D)
        if audio.dim() > 2:
            return False
        
        return True
        
    except Exception:
        return False


def estimate_audio_duration(audio: torch.Tensor, sample_rate: int) -> float:
    """
    Estimate duration of audio tensor in seconds.
    
    Args:
        audio: Audio tensor
        sample_rate: Sample rate in Hz
        
    Returns:
        Duration in seconds
    """
    if audio.numel() == 0 or sample_rate <= 0:
        return 0.0
    
    # Get number of samples (last dimension)
    num_samples = audio.shape[-1]
    return num_samples / sample_rate


def prepare_audio_for_save(audio: torch.Tensor, target_sample_rate: int = 22050) -> Tuple[torch.Tensor, int]:
    """
    Prepare audio tensor for saving to file.
    
    Args:
        audio: Input audio tensor
        target_sample_rate: Target sample rate for output
        
    Returns:
        Tuple of (prepared_audio, sample_rate)
    """
    # Normalize audio format
    prepared_audio = normalize_audio_tensor(audio)
    
    # Ensure reasonable amplitude range
    max_val = torch.abs(prepared_audio).max()
    if max_val > 1.0:
        prepared_audio = prepared_audio / max_val
        warnings.warn(f"Audio amplitude normalized from {max_val:.3f} to 1.0")
    
    return prepared_audio, target_sample_rate