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

## 💡 LEÇONS APPRISES
- **Synchronisation FFmpeg/PulseAudio** : La capture simultanée de plusieurs flux PulseAudio via une seule instance FFmpeg nécessite impérativement de définir `-thread_queue_size` (min 1024) pour éviter les blocages de threads et les délais de synchronisation.
- **Contrôle de Durée** : Pour garantir un arrêt précis dans un contexte multi-flux, l'argument de durée `-t` doit être placé avant chaque entrée (`-i`).
- **Robustesse Python** : L'ajout d'un `timeout` dans `subprocess.run` est une sécurité indispensable pour prévenir les blocages indéfinis en cas de défaillance du serveur audio (ex: PipeWire crash).
- **Silence Technique** : L'utilisation de `-loglevel error` permet de maintenir une console propre et exploitable, conforme aux standards de qualité du projet.
