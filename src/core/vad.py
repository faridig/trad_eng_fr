import torch
import numpy as np

class VADDetector:
    """
    Détecteur de voix utilisant Silero VAD.
    Optimisé pour fonctionner à 16kHz.
    """
    def __init__(self, threshold=0.5, sampling_rate=16000):
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                          model='silero_vad',
                                          force_reload=False,
                                          onnx=False,
                                          trust_repo=True)
        self.threshold = threshold
        self.sampling_rate = sampling_rate
        
        # Passer le modèle en mode évaluation
        self.model.eval()

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Détermine si le chunk audio contient de la parole.
        audio_chunk: tableau numpy (float32).
        Supporte des chunks de taille arbitraire en les découpant.
        """
        # Normalisation Mono automatique
        if audio_chunk.ndim > 1:
            audio_chunk = audio_chunk.mean(axis=-1)

        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)
            
        # Normalisation si nécessaire (Silero attend du [-1, 1])
        if np.max(np.abs(audio_chunk)) > 1.0:
            audio_chunk = audio_chunk / 32768.0

        # Silero VAD attend des chunks de 512 samples pour 16kHz
        chunk_size = 512
        
        # On divise l'audio_chunk en sous-chunks de 512
        for i in range(0, len(audio_chunk), chunk_size):
            sub_chunk = audio_chunk[i:i+chunk_size]
            if len(sub_chunk) < chunk_size:
                # Pad with zeros if last chunk is too small
                sub_chunk = np.pad(sub_chunk, (0, chunk_size - len(sub_chunk)))
            
            tensor_chunk = torch.from_numpy(sub_chunk).unsqueeze(0) # Ajouter dimension batch
            
            with torch.no_grad():
                speech_prob = self.model(tensor_chunk, self.sampling_rate).item()
            
            if speech_prob > self.threshold:
                return True
        
        return False
