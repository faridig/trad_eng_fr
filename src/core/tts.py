import os
import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro
from huggingface_hub import hf_hub_download

# Monkey-patch np.load pour allow_pickle=True car kokoro-onnx ne le fait pas
# et NumPy 2.0+ l'interdit par défaut pour les objets.
orig_load = np.load
def patched_load(*args, **kwargs):
    if "allow_pickle" not in kwargs:
        kwargs["allow_pickle"] = True
    return orig_load(*args, **kwargs)
np.load = patched_load

class TTS:
    """
    Synthèse vocale utilisant Kokoro-82M.
    """
    def __init__(self, model_dir="models/tts", device="auto"):
        self.model_dir = model_dir
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            
        self.model_path = self._ensure_model()
        self.voices_path = self._ensure_voices()
        
        self.kokoro = Kokoro(self.model_path, self.voices_path)

    def _ensure_model(self):
        path = os.path.join(self.model_dir, "model.onnx")
        if not os.path.exists(path):
            print("Téléchargement du modèle Kokoro ONNX...")
            hf_hub_download(
                repo_id="onnx-community/Kokoro-82M-ONNX",
                filename="onnx/model.onnx",
                local_dir=self.model_dir
            )
            # Déplacer le fichier si hf_hub_download a créé un sous-répertoire
            if os.path.exists(os.path.join(self.model_dir, "onnx/model.onnx")):
                os.rename(os.path.join(self.model_dir, "onnx/model.onnx"), path)
        return path

    def _ensure_voices(self):
        path = os.path.join(self.model_dir, "voices.bin")
        if not os.path.exists(path):
            print("Téléchargement des voix Kokoro...")
            # Note: Téléchargement via curl dans le processus de build ou ici
            # Pour l'instant, on suppose qu'il a été téléchargé par le dev ou via une commande bash
            # Mais on peut utiliser hf_hub_download si on trouve un repo public qui l'a.
            # On va essayer de le télécharger si absent.
            import subprocess
            subprocess.run([
                "curl", "-L", 
                "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin", 
                "-o", path
            ])
        return path

    def generate(self, text: str, voice: str = "af_sarah", lang: str = "en-us"):
        """
        Génère l'audio à partir du texte.
        """
        if not text.strip():
            return None, None
            
        # Si la voix demandée n'est pas chargée, on utilise la première disponible
        voices = self.kokoro.get_voices()
        if voice not in voices:
            voice = voices[0] if voices else voice

        samples, sample_rate = self.kokoro.create(
            text, 
            voice=voice, 
            speed=1.0, 
            lang=lang
        )
        return samples, sample_rate

    def play(self, samples, sample_rate):
        """
        Joue l'audio sur la sortie par défaut.
        """
        if samples is not None:
            try:
                sd.play(samples, sample_rate)
                sd.wait()
            except Exception as e:
                print(f"TTS: Lecture audio impossible (Pas de carte son ?): {e}")
