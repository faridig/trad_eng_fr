from faster_whisper import WhisperModel
import numpy as np

import torch

class Transcriber:
    """
    Transicripteur utilisant Faster-Whisper.
    """
    def __init__(self, model_size="large-v3", device="auto", compute_type="auto"):
        # Détection automatique du device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Détection automatique du type de calcul
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"
            
        print(f"STT: Initialisation de {model_size} sur {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, language: str = "fr"):
        """
        Transcrit un segment audio.
        audio: tableau numpy (float32) à 16kHz.
        """
        # Paramètres optimisés pour la latence (beam_size=1) et forcer le langage
        segments, info = self.model.transcribe(
            audio, 
            beam_size=1, 
            language=language, 
            task="transcribe",
            vad_filter=False, 
            condition_on_previous_text=False,
            no_speech_threshold=0.3
        )
        
        # On concatène les segments pour avoir le texte complet
        full_text = " ".join([segment.text for segment in segments]).strip()
        
        return full_text, info
