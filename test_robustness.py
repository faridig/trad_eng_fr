import numpy as np
from src.core.vad import VADDetector
import soundfile as sf

def test_robustness():
    print("Test de robustesse VAD...")
    vad = VADDetector()
    
    # Test 1: Stéréo 48kHz (doit être normalisé mono 16kHz par le pipeline, mais ici on teste VAD direct)
    print("Test 1: Simulation Stéréo...")
    stereo_chunk = np.random.rand(1536, 2).astype(np.float32)
    # VADDetector.is_speech normalise maintenant le mono
    try:
        vad.is_speech(stereo_chunk)
        print("✅ Success: VAD a géré le stéréo")
    except Exception as e:
        print(f"❌ Failed: VAD a crashé sur le stéréo: {e}")

    # Test 2: Audio avec de la parole réelle
    print("Test 2: Parole réelle (test_micro.wav)...")
    data, samplerate = sf.read('test_micro.wav')
    # Normalisation manuelle pour le test VAD direct (le pipeline le fera sinon)
    if data.ndim > 1:
        data = data.mean(axis=-1)
    
    # On teste par blocs
    speech_detected = False
    for i in range(0, len(data), 1536):
        chunk = data[i:i+1536]
        if vad.is_speech(chunk):
            speech_detected = True
            break
    
    if speech_detected:
        print("✅ Success: Parole détectée dans test_micro.wav")
    else:
        print("⚠️ Warning: Aucune parole détectée dans test_micro.wav (seuil trop haut ou pas de parole)")

if __name__ == "__main__":
    test_robustness()
