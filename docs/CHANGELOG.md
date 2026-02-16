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

## 💡 LEÇONS APPRISES (SPRINT 2)
- **Robustesse Audio** : Ne jamais assumer le format d'entrée. L'intégration de `torchaudio.transforms.Resample` et d'une normalisation mono automatique est indispensable pour un pipeline "Real-World".
- **Gestion du Silence Technique** : Le module `logging` combiné à un mécanisme anti-flood (vérification du dernier message d'erreur) est vital pour éviter la saturation des disques et du processeur lors de boucles infinies asynchrones.
- **Compatibilité NumPy 2.0** : L'utilisation de bibliothèques ML legacy (comme `kokoro-onnx`) nécessite parfois des monkey-patches sur `np.load` pour restaurer le support de `allow_pickle=True` (à manipuler avec précaution pour la sécurité).
- **Orchestration Asynchrone** : Le découplage par `asyncio.Queue` permet d'absorber les pics de charge (ex: une phrase longue à traduire) sans bloquer la capture audio.
- **Latence et Réseau** : Les tokenizers de Transformers effectuent des vérifications réseau par défaut. Pour un pipeline temps réel, il est crucial de pré-charger les modèles ou d'utiliser `HF_HUB_OFFLINE=1` pour garantir une latence stable sous les 2 secondes.
