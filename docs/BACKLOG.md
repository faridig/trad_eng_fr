# Product Backlog - VoxTransync Local

# ⚙️ CONFIGURATION TECHNIQUE
- **Langage** : Python 3.10+
- **OS** : Pop!_OS (Linux)
- **Audio Routing** : PipeWire / PulseAudio (pactl load-module module-null-sink)
- **Transcription (STT)** : Faster-Whisper (Modèle Medium sur CUDA)
- **Synthèse Vocale (TTS)** : MeloTTS ou Piper (Optimisé GPU)
- **Traduction** : Helsinki-NLP MarianMT (via Transformers/CTranslate2)
- **VRAM Cible** : ~5GB / 8GB (NVIDIA RTX)
- **RAM Système** : 16GB (Pop!_OS)

## Vision du Produit
Un traducteur vocal bidirectionnel local capable d'intercepter les flux audio système (ex: Zoom, YouTube) et micro, de les traduire et de les rediffuser via un microphone virtuel ou les haut-parleurs, avec une latence minimale.

## Sprints & Priorités

| ID | Titre | Description | État | Priorité |
| :--- | :--- | :--- | :--- | :--- |
| **PBI-000** | **Sprint 0 : PoC Audio** | Validation de la capture Micro + Système sur PipeWire. | EN COURS | CRITIQUE |
| **PBI-001** | **Moteur de Transcription (STT)** | Intégration Faster-Whisper et VAD (Silero). | À FAIRE | HAUTE |
| **PBI-002** | **Moteur de Synthèse (TTS)** | Intégration MeloTTS/Piper et Main Loop asynchrone. | À FAIRE | HAUTE |
| **PBI-003** | **Logique de Traduction** | Pipeline de traduction entre STT et TTS (Local/API). | À FAIRE | MOYENNE |
| **PBI-004** | **Interface de Contrôle Dual-Pane** | UI basée sur Transync AI : split-pane FR/EN, monitoring audio et logs temps-réel. | À FAIRE | MOYENNE |
| **PBI-005** | **Gestion de l'Écho (AEC)** | Isolation du son HP pour éviter les boucles de traduction. | À FAIRE | CRITIQUE |
| **PBI-006** | **Routage Micro Virtuel** | Injection de la traduction dans le flux Micro pour Zoom. | À FAIRE | HAUTE |

---

## ✅ DEFINITION OF DONE (DoD)
- Code commenté et typé (Python Type Hints).
- Latence "Speech-to-Speech" < 2 secondes (Cible : 1.2s).
- Pas de fuite de mémoire sur les buffers audio.
- Documentation d'installation pour le Virtual Cable.

---

## 🏛️ JOURNAL DES DÉCISIONS
- **2026-02-15** : Choix de Pop!_OS comme OS cible. Abandon de VB-Audio au profit de PipeWire (natif Linux).
- **2026-02-15** : Sélection de Faster-Whisper (STT) et MeloTTS (TTS) pour maximiser l'usage du GPU NVIDIA 8Go.
- **2026-02-15** : Interface cible type "Dual-Pane" (inspirée de Transync AI) pour la bidirectionnalité.
- **2026-02-15** : Priorisation d'une configuration avec casque pour éliminer l'écho acoustique.

---
*Dernière mise à jour : 15/02/2026*
