from faster_whisper import WhisperModel
import numpy as np

class Transcriber:
    """
    Transicripteur utilisant Faster-Whisper.
    Optimisé pour CUDA.
    """
    def __init__(self, model_size="distil-large-v3", device="cuda", compute_type="float16"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, language: str = "fr"):
        """
        Transcrit un segment audio.
        audio: tableau numpy (float32) à 16kHz.
        """
        segments, info = self.model.transcribe(audio, beam_size=5, language=language, task="transcribe")
        
        # On concatène les segments pour avoir le texte complet
        full_text = " ".join([segment.text for segment in segments]).strip()
        
        return full_text, info
