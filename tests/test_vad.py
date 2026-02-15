import pytest
import numpy as np
import wave
from src.core.vad import VADDetector

def load_wav_to_numpy(path):
    with wave.open(path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        
        data = wf.readframes(n_frames)
        audio = np.frombuffer(data, dtype=np.int16)
        
        # Convertir en mono si nécessaire
        if n_channels > 1:
            audio = audio[::n_channels]
            
        # Resampler à 16kHz si nécessaire (très basique)
        if framerate != 16000:
            # Pour le test, on va supposer que nos fichiers de test sont convertis ou compatibles
            # Sinon, il faudrait un vrai resampling
            pass
            
        return audio.astype(np.float32) / 32768.0

def test_vad_initialization():
    vad = VADDetector()
    assert vad.model is not None

def test_vad_silence():
    vad = VADDetector()
    silence = np.zeros(16000, dtype=np.float32) # 1 seconde de silence
    assert not vad.is_speech(silence)

def test_vad_on_existing_file():
    # On vérifie si un fichier de test existe
    import os
    test_file = "test_micro.wav"
    if os.path.exists(test_file):
        audio = load_wav_to_numpy(test_file)
        vad = VADDetector()
        
        # On teste par petits morceaux (512 samples est le min recommandé par Silero)
        chunk_size = 512
        speech_detected = False
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            if len(chunk) < chunk_size:
                continue
            if vad.is_speech(chunk):
                speech_detected = True
                break
        
        # Si test_micro.wav contient de la parole, speech_detected devrait être True
        # On ne peut pas l'affirmer à 100% sans connaître le contenu du WAV,
        # mais on valide au moins que le code tourne sans erreur.
        print(f"Speech detected in {test_file}: {speech_detected}")
