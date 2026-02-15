# Changelog - VoxTransync Local

## [Unreleased] - 2026-02-15
### Added
- Initialisation du projet "VoxTransync Local".
- Définition de la stack technique (Faster-Whisper, MeloTTS, MarianMT).
- Configuration spécifique pour Pop!_OS et PipeWire.
- Création du Backlog et du Sprint 0.
- Planification du Squelette Audio (Capture Loopback & Micro).
- Implémentation réussie du PoC Audio (Capture simultanée Micro + Système).
- Automatisation des tests d'intégrité audio.
- Pipeline asynchrone pour la transcription en temps réel.
- Intégration de Silero VAD pour la détection de parole.
- Intégration de Faster-Whisper (distil-large-v3) optimisé pour CUDA.
- Démo interactive pour le Sprint 1 (`demo_sprint1.py`).

## 💡 LEÇONS APPRISES
- **Synchronisation FFmpeg/PulseAudio** : La capture simultanée de plusieurs flux PulseAudio via une seule instance FFmpeg nécessite impérativement de définir `-thread_queue_size` (min 1024) pour éviter les blocages de threads et les délais de synchronisation.
- **Contrôle de Durée** : Pour garantir un arrêt précis dans un contexte multi-flux, l'argument de durée `-t` doit être placé avant chaque entrée (`-i`).
- **Robustesse Python** : L'ajout d'un `timeout` dans `subprocess.run` est une sécurité indispensable pour prévenir les blocages indéfinis en cas de défaillance du serveur audio (ex: PipeWire crash).
- **Silence Technique** : L'utilisation de `-loglevel error` permet de maintenir une console propre et exploitable, conforme aux standards de qualité du projet.
- **Bridge Sync/Async** : Pour intégrer des bibliothèques à callbacks synchrones (comme `sounddevice`) dans une architecture `asyncio`, l'utilisation de `asyncio.run_coroutine_threadsafe` est indispensable pour ne pas bloquer la boucle d'événements principale tout en garantissant la thread-safety.
- **Contraintes Silero VAD** : Le modèle Silero VAD est extrêmement sensible à la taille des chunks (strictement 512, 1024 ou 1536 samples à 16kHz). Un padding ou un découpage précis est nécessaire pour éviter des erreurs de dimension de tenseur en entrée.
- **Optimisation Whisper** : L'utilisation du modèle `distil-large-v3` avec Faster-Whisper en `float16` sur CUDA offre un excellent compromis entre latence (presque temps réel) et précision pour la transcription.
