# Product Backlog - VoxTransync Local

# ⚙️ CONFIGURATION TECHNIQUE
- **Langage** : Python 3.10+
- **OS** : Pop!_OS (Linux)
- **Audio Routing** : PipeWire / PulseAudio (pactl load-module module-null-sink)
- **Transcription (STT)** : Faster-Whisper (Modèle large-v3 complet sur CUDA)
- **Synthèse Vocale (TTS)** : Kokoro-82M (Modèle SOTA ultra-léger et naturel)
- **Traduction** : MarianMT via CTranslate2 (Inférence ultra-rapide)
- **VRAM Cible** : ~5.5GB / 8GB (Ajusté après pivot large-v3)
- **RAM Système** : 16GB (Pop!_OS)

## Vision du Produit
Un traducteur vocal bidirectionnel local capable d'intercepter les flux audio système (ex: Zoom, YouTube) et micro, de les traduire et de les rediffuser via un microphone virtuel ou les haut-parleurs, avec une latence minimale.

## Sprints & Priorités

| ID | Titre | Description | État | Priorité |
| :--- | :--- | :--- | :--- | :--- |
| **PBI-000** | **Sprint 0 : PoC Audio** | Validation de la capture Micro + Système sur PipeWire. | DONE | CRITIQUE |
| **PBI-001** | **Moteur de Transcription (STT)** | Intégration Faster-Whisper et VAD (Silero) optimisée. | DONE | HAUTE |
| **PBI-002** | **Moteur de Synthèse (TTS)** | Intégration Kokoro-82M et Main Loop asynchrone. | À FAIRE | HAUTE |
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
- **2026-02-15** : Validation via context7. Passage à Kokoro-82M pour le TTS.
- **2026-02-15** : PIVOT STT : Abandon de `distil-large-v3` pour `large-v3` afin d'éliminer les hallucinations de traduction.
- **2026-02-15** : AJUSTEMENT UX : Augmentation du délai de pause VAD à 800ms pour respecter la prosodie française.
- **2026-02-15** : TECHNIQUE : Implémentation d'un Trimming actif sur les segments VAD pour supprimer le bruit résiduel.

---
*Dernière mise à jour : 15/02/2026*
