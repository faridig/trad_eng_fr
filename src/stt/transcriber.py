from faster_whisper import WhisperModel
import numpy as np

class Transcriber:
    """
    Transicripteur utilisant Faster-Whisper.
    Optimisé pour CUDA.
    """
    def __init__(self, model_size="large-v3", device="cuda", compute_type="float16"):
        # Utilisation de large-v3 par défaut pour une meilleure robustesse multi-langue
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, language: str = "fr"):
        """
        Transcrit un segment audio.
        audio: tableau numpy (float32) à 16kHz.
        """
        # Paramètres optimisés pour réduire les hallucinations et forcer le langage
        segments, info = self.model.transcribe(
            audio, 
            beam_size=5, 
            language=language, 
            task="transcribe",
            vad_filter=False, # On fait déjà la VAD en amont, on évite les conflits
            condition_on_previous_text=False,
            no_speech_threshold=0.3 # Plus permissif pour éviter les textes vides
        )
        
        # On concatène les segments pour avoir le texte complet
        full_text = " ".join([segment.text for segment in segments]).strip()
        
        return full_text, info
