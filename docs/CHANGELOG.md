# Changelog - VoxTransync Local

## [Unreleased] - 2026-02-15
### Added
- Sprint 1 terminé : Pipeline de transcription opérationnel.
- Intégration de Faster-Whisper avec le modèle `large-v3`.
- Implémentation de Silero VAD avec Trimming de silence intégré.

### Changed
- Modèle STT : `distil-large-v3` -> `large-v3` (pour corriger les hallucinations linguistiques).
- Paramètres VAD : `min_silence_duration_ms` porté à 800ms.

## 💡 LEÇONS APPRISES
- **Distillation vs Fidélité** : Les modèles distillés (distil-whisper) ont tendance à forcer la sortie vers la langue de pré-entraînement majoritaire (Anglais) lors de segments courts ou bruités. Le modèle complet est indispensable pour une traduction bidirectionnelle fiable.
- **Trimming Audio** : La transcription gagne en vitesse et en précision si on retire les quelques millisecondes de silence que la VAD laisse parfois en début/fin de segment.
- **Rythme Humain** : 480ms de silence est trop court pour la parole naturelle ; cela coupe les phrases lors des pauses respiratoires. 800ms est le "sweet spot" pour la fluidité.
- **Bridge Sync/Async** : Utilisation de `asyncio.run_coroutine_threadsafe` pour la thread-safety entre les callbacks audio et la boucle asynchrone.
