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
| **PBI-000** | **Sprint 0 : PoC Audio** | Validation de la capture Micro + Système sur PipeWire. | ✅ DONE (Sprint 0) | CRITIQUE |
| **PBI-001** | **Moteur de Transcription (STT)** | Intégration Faster-Whisper large-v3 et VAD (Silero) optimisée. | ✅ DONE (Sprint 1) | HAUTE |
| **PBI-002** | **Moteur de Synthèse (TTS)** | Intégration Kokoro-82M et Main Loop asynchrone. | ✅ DONE (Sprint 2) | HAUTE |
| **PBI-003** | **Logique de Traduction** | Pipeline de traduction MarianMT via CTranslate2. | ✅ DONE (Sprint 2) | MOYENNE |
| **PBI-004** | **Interface de Contrôle Minimal pour Réunion** | UI avec contrôles Start/Stop/Pause, monitoring visuel et gestion des langues. | À FAIRE | HAUTE |
| **PBI-005** | **Sécurité Audio Léger (AEC Optionnel)** | Détection de feedback simple et limitation de volume automatique. | À FAIRE | MOYENNE |
| **PBI-006** | **Routage Micro Virtuel pour Google Meet** | Injection de la traduction dans le flux Micro pour Google Meet. | ✅ DONE (Sprint 4) | HAUTE |
| **PBI-007** | **Correction CI #7 - Tests GPU sur CPU** | Fix des tests unitaires échouant sur CI sans GPU. | ✅ DONE (Sprint 4) | CRITIQUE |
| **PBI-008** | **Filtrage des Hallucinations** | Correction du "syndrome Merci" lors des silences. | À FAIRE (Sprint 5) | HAUTE |
| **PBI-009** | **Segmentation Intelligente** | Correction du tronquage des phrases. | À FAIRE (Sprint 5) | HAUTE |
| **PBI-010** | **Optimisation VAD (Latence)** | Réduction du délai de fin de phrase à 500ms. | À FAIRE (Sprint 5) | MOYENNE |
| **PBI-011** | **Script de Lancement Unique** | Création de `start.py` pour simplifier l'usage. | À FAIRE (Sprint 5) | MOYENNE |

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

## 🐛 BUGS IDENTIFIÉS (À CORRIGER)
- **BUG-001** : SoundDevice ne détecte pas le sink virtuel PipeWire créé (`_find_sounddevice_device_id()`) ✅ **FIXED**
- **BUG-002** : Tests unitaires `MeetPipeline` échouent à cause de problèmes de mocking ✅ **FIXED**
- **BUG-003** : Pollution console avec logs DEBUG des bibliothèques externes (httpcore, httpx) ⚠️ **EN COURS**

## 🔧 AMÉLIORATIONS (BACKLOG)
- **IMPROV-001** : Script de démarrage avec option `--quick-setup` pour micro virtuel seul
- **IMPROV-002** : Guide dépannage navigateur pour Google Meet (redémarrage, permissions)
- **IMPROV-003** : Support noms simples pour micro virtuel (ex: "vox-mic" au lieu de "vox-transync-mic")
- **IMPROV-004** : Monitoring état source (.monitor) et recréation si nécessaire

## 🎯 PROCHAIN SPRINT (Sprint 5)
| ID | Titre | Description | Priorité |
| :--- | :--- | :--- | :--- |
| **PBI-008** | **Filtrage des Hallucinations** | Correction du "syndrome Merci" lors des silences. | HAUTE |
| **PBI-009** | **Segmentation Intelligente** | Correction du tronquage des phrases (points d'interrogation). | HAUTE |
| **PBI-010** | **Optimisation VAD (Latence)** | Réduction du délai de fin de phrase à 500ms. | MOYENNE |
| **PBI-011** | **Script de Lancement Unique** | Création de `start.py` pour simplifier l'usage. | MOYENNE |

## 🏛️ JOURNAL DES DÉCISIONS
- **2026-02-15** : Choix de Pop!_OS comme OS cible. Abandon de VB-Audio au profit de PipeWire (natif Linux).
- **2026-02-15** : Validation via context7. Passage à Kokoro-82M pour le TTS.
- **2026-02-15** : PIVOT STT : Abandon de `distil-large-v3` pour `large-v3` afin d'éliminer les hallucinations de traduction.
- **2026-02-15** : AJUSTEMENT UX : Augmentation du délai de pause VAD à 800ms pour respecter la prosodie française.
- **2026-02-15** : TECHNIQUE : Implémentation d'un Trimming actif sur les segments VAD pour supprimer le bruit résiduel.
- **2026-02-17** : **CLÔTURE SPRINT 4** : CI réparée et redirection audio Meet automatique validée via `pulsectl`.
- **2026-02-17** : **CRITICAL FEEDBACK** : Nécessité de filtrer les hallucinations de silence ("Merci") et corriger la segmentation des phrases.

---
*Dernière mise à jour : 17/02/2026 - Clôture Sprint 4*
