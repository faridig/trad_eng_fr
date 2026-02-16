import asyncio
import numpy as np
import soundfile as sf
import time
import pytest
from src.core.tts import TTS
from src.core.pipeline import AsyncPipeline
import os
import logging

# Désactiver les logs excessifs pour y voir clair
logging.getLogger("faster_whisper").setLevel(logging.ERROR)

@pytest.mark.asyncio
async def test_full_pipeline_fidelity():
    print("\n=== TEST DE FIDÉLITÉ ET LATENCE E2E ===")
    
    # Détection de l'environnement CI
    is_ci = os.getenv("CI") == "true"
    if is_ci:
        print("⚠️ Environnement CI détecté - tests adaptés")
    
    # 1. Préparation de l'audio de test (Natif Français)
    tts = TTS()
    text_source = "Bonjour tout le monde, ceci est un test de traduction automatique."
    # Utilisation de ff_siwis pour une voix française native
    print(f"Génération de l'audio source (FR) avec la voix 'ff_siwis'...")
    samples, sr = tts.generate(text_source, voice="ff_siwis", lang="fr-fr")
    
    if samples is None or sr is None:
        print("❌ Échec de la génération TTS")
        return

    sf.write('test_system.wav', samples, sr)
    print(f"✅ Échantillon généré: test_system.wav ({len(samples)} samples @ {sr}Hz)")

    # 2. Initialisation du Pipeline avec large-v3
    print(f"\nInitialisation du pipeline avec le modèle 'large-v3'...")
    pipeline = AsyncPipeline(model_size="large-v3", input_sample_rate=sr)
    
    # Warm-up pour CUDA et les modèles
    print("Warm-up des modèles (STT, Trad FR-EN, Trad EN-FR, TTS)...")
    dummy_audio = np.zeros(sr * 1)
    pipeline.transcriber.transcribe(dummy_audio, language="fr")
    pipeline.translator.translate("Test", "fr", "en")
    pipeline.translator.translate("Test", "en", "fr")
    pipeline.tts.generate("Test", voice="ff_siwis", lang="fr-fr")
    
    # 3. Instrumentation pour capturer les résultats
    results = {
        "transcription": "",
        "translation": "",
        "latency": 0.0,
        "start_time": 0.0
    }

    # Monkey-patch pour capturer les sorties
    original_transcription_loop = pipeline.transcription_loop
    async def captured_transcription_loop():
        while pipeline.is_running:
            try:
                segment, start_time = await pipeline.transcription_queue.get()
                text, info = pipeline.transcriber.transcribe(segment)
                if text:
                    results["transcription"] = text
                    print(f"STT [fr]: {text}")
                    await pipeline.translation_queue.put((text, info.language, start_time))
                pipeline.transcription_queue.task_done()
            except Exception:
                break

    original_tts_loop = pipeline.tts_loop
    async def captured_tts_loop():
        while pipeline.is_running:
            try:
                text, lang, start_time = await pipeline.tts_queue.get()
                results["translation"] = text
                results["latency"] = time.time() - start_time
                print(f"TRAD [{lang}]: {text}")
                print(f"⏱️ Latence mesurée: {results['latency']:.2f}s")
                pipeline.tts_queue.task_done()
            except Exception:
                break

    pipeline.transcription_loop = captured_transcription_loop
    pipeline.tts_loop = captured_tts_loop

    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    await asyncio.sleep(2) # Laisser le temps au modèle de charger
    
    # 4. Injection de l'audio
    print("\nInjection de l'audio dans le pipeline...")
    results["start_time"] = time.time()
    chunk_size = int(sr * 0.032)
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i:i+chunk_size]
        await pipeline.add_audio_chunk(chunk)
    
    # Ajouter du silence pour fermer le segment VAD
    silence = np.zeros(int(sr * 1.5))
    for i in range(0, len(silence), chunk_size):
        await pipeline.add_audio_chunk(silence[i:i+chunk_size])

    print("Traitement en cours...")
    
    # Attendre que le résultat arrive ou timeout
    timeout = 120 if is_ci else 30
    start_wait = time.time()
    while not results["translation"] and (time.time() - start_wait) < timeout:
        await asyncio.sleep(0.5)
    
    # Bilan
    print("\n=== BILAN DU TEST ===")
    latency_threshold = 2.0 if not is_ci else 60.0 # Plus tolérant en CI sans GPU
    
    # Vérification Fidélité
    source_norm = text_source.lower().replace(",", "").replace(".", "").strip()
    stt_norm = results["transcription"].lower().replace(",", "").replace(".", "").strip()
    
    print(f"Texte Source: '{text_source}'")
    print(f"Texte STT   : '{results['transcription']}'")
    
    if stt_norm == source_norm:
        print("✅ FIDÉLITÉ: 100% (Match parfait)")
    else:
        # On accepte de légères variations (ponctuation, etc.) mais ici on vise le 100% demandé
        import difflib
        ratio = difflib.SequenceMatcher(None, source_norm, stt_norm).ratio()
        print(f"⚠️ FIDÉLITÉ: {ratio*100:.1f}%")
        if ratio < 0.9:
            print("❌ ÉCHEC: Fidélité insuffisante.")
    
    if results["latency"] > 0:
        if results["latency"] < latency_threshold:
            print(f"✅ LATENCE: {results['latency']:.2f}s (Critère < {latency_threshold}s respecté)")
        else:
            print(f"❌ LATENCE: {results['latency']:.2f}s (Critère < {latency_threshold}s dépassé)")
    else:
        print("❌ ÉCHEC: Aucune mesure de latence obtenue.")

    pipeline.stop()
    for t in tasks:
        t.cancel()
    
    fidelity_ok = stt_norm == source_norm
    latency_ok = results["latency"] < latency_threshold and results["latency"] > 0
    
    if fidelity_ok and latency_ok:
        print("\nRESULTAT GLOBAL: SUCCÈS ✅")
        assert True
    else:
        print("\nRESULTAT GLOBAL: ÉCHEC ❌")
        if not fidelity_ok:
            print(f"Détail Fidélité: Attendu '{source_norm}', Reçu '{stt_norm}'")
        assert fidelity_ok
        assert latency_ok

if __name__ == "__main__":
    # Si lancé directement, on utilise pytest pour bénéficier des plugins
    import sys
    sys.exit(pytest.main([__file__, "-s"]))
