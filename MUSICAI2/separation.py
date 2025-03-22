"""
Audio separation module for MUSICAI2.
Handles vocal and instrumental separation using Demucs.
"""

import os
from pathlib import Path
import torch
import torchaudio
from typing import Optional, Tuple
from demucs.pretrained import get_model
from demucs.apply import apply_model


class AudioSeparator:
    def __init__(
        self,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        model_name: str = 'htdemucs'  # High-quality separation model
    ):
        """Initialize audio separator.
        
        Args:
            device: Device to use for processing
            model_name: Name of Demucs model to use
        """
        self.device = device
        self.separator = get_model(model_name)
        self.separator.to(device)

    def separate_audio(
        self,
        input_path: str,
        output_dir: Optional[str] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Separate audio into vocals and instrumental.
        
        Args:
            input_path: Path to input audio file
            output_dir: Optional directory to save separated tracks
            
        Returns:
            Tuple of (vocals, instrumental) as tensors
        """
        # Load audio
        audio, sr = torchaudio.load(input_path)
        
        # Convert to mono if stereo
        if audio.size(0) > 1:
            audio = torch.mean(audio, dim=0, keepdim=True)
        
        # Apply source separation
        sources = apply_model(
            self.separator,
            audio,
            device=self.device,
            progress=True
        )
        
        # Extract vocals and instrumental
        vocals = sources[0]  # First source is vocals
        instrumental = sum(sources[1:])  # Remaining sources form instrumental
        
        # Save if output directory provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save vocals
            vocals_path = output_dir / 'vocals.wav'
            torchaudio.save(str(vocals_path), vocals.cpu(), sr)
            
            # Save instrumental
            instrumental_path = output_dir / 'instrumental.wav'
            torchaudio.save(str(instrumental_path), instrumental.cpu(), sr)
        
        return vocals, instrumental

    def separate_stems(
        self,
        input_path: str,
        output_dir: str
    ) -> dict:
        """Separate audio into all available stems.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save separated stems
            
        Returns:
            Dictionary mapping stem names to file paths
        """
        # Load audio
        audio, sr = torchaudio.load(input_path)
        
        # Convert to mono if stereo
        if audio.size(0) > 1:
            audio = torch.mean(audio, dim=0, keepdim=True)
        
        # Apply source separation
        sources = apply_model(
            self.separator,
            audio,
            device=self.device,
            progress=True
        )
        
        # Save stems
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stem_paths = {}
        stem_names = ['vocals', 'drums', 'bass', 'other']
        
        for source, name in zip(sources, stem_names):
            path = output_dir / f'{name}.wav'
            torchaudio.save(str(path), source.cpu(), sr)
            stem_paths[name] = str(path)
        
        return stem_paths
