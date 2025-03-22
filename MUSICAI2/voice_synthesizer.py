"""
Voice synthesis module for MUSICAI2.
Uses gTTS for basic voice synthesis with pitch and tempo control.
"""

import os
import json
from pathlib import Path
import torch
import torchaudio
from gtts import gTTS
from typing import Optional, Dict


class VoiceSynthesizer:
    def __init__(
        self,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        styles_path: str = 'src/creation/voice_styles.json'
    ):
        """Initialize voice synthesizer.
        
        Args:
            device: Device to use for processing
            styles_path: Path to voice styles configuration
        """
        self.device = device
        
        # Load voice styles
        with open(styles_path, 'r') as f:
            self.voice_styles = json.load(f)

    def generate_vocals(
        self,
        lyrics: str,
        output_path: str,
        voice_style: str = 'male_deep',
        tempo: float = 1.0,
        pitch_shift: float = 0.0
    ) -> Optional[str]:
        """Generate singing vocals from lyrics.
        
        Args:
            lyrics: Input lyrics to sing
            output_path: Path to save generated audio
            voice_style: Name of voice style to use
            tempo: Speed multiplier (1.0 = normal)
            pitch_shift: Semitones to shift pitch
            
        Returns:
            Path to generated audio file if successful
        """
        try:
            # Get voice style config
            if voice_style not in self.voice_styles:
                raise ValueError(f"Unknown voice style: {voice_style}")
            
            style_config = self.voice_styles[voice_style]
            
            # Generate base audio with gTTS
            tts = gTTS(text=lyrics, lang='en', slow=False)
            temp_path = output_path + '.temp.mp3'
            tts.save(temp_path)
            
            # Load generated audio for post-processing
            audio, sr = torchaudio.load(temp_path)
            os.remove(temp_path)  # Clean up temp file
            
            # Apply tempo and pitch adjustments
            if tempo != 1.0 or pitch_shift != 0.0:
                # Time stretching
                if tempo != 1.0:
                    audio = torchaudio.transforms.TimeStretch(
                        n_freq=1024,
                        hop_length=256
                    )(audio, tempo)
                
                # Pitch shifting
                if pitch_shift != 0.0:
                    audio = torchaudio.transforms.PitchShift(
                        sample_rate=sr,
                        n_steps=pitch_shift
                    )(audio)
            
            # Save processed audio
            torchaudio.save(output_path, audio, sr)
            
            return output_path
            
        except Exception as e:
            print(f"Error generating vocals: {e}")
            return None

    def preview_voice(
        self,
        text: str,
        voice_style: str,
        output_path: str,
        duration: float = 3.0
    ) -> Optional[str]:
        """Generate a short preview of a voice style.
        
        Args:
            text: Short text to synthesize
            voice_style: Name of voice style to preview
            output_path: Path to save preview audio
            duration: Maximum duration in seconds
            
        Returns:
            Path to preview audio if successful
        """
        try:
            # Truncate text if needed
            words = text.split()
            preview_text = ' '.join(words[:10])  # First 10 words
            
            # Generate preview
            return self.generate_vocals(
                preview_text,
                output_path,
                voice_style,
                tempo=1.0,
                pitch_shift=0.0
            )
            
        except Exception as e:
            print(f"Error generating preview: {e}")
            return None

    @property
    def available_styles(self) -> Dict[str, dict]:
        """Get available voice styles with descriptions."""
        return {
            style_id: {
                'name': config['name'],
                'description': config['description']
            }
            for style_id, config in self.voice_styles.items()
        }
