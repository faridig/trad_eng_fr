# Changelog - VoxTransync Local

## [Sprint 4] - 2026-02-17
### Added
- PBI-007 : Correction définitive de la CI. Les tests unitaires sont isolés (Mocking) et passent sans GPU sur GitHub Actions.
- Robustesse Audio : Intégration de `pulsectl` et mécanisme de "Redirection de secours" (Plan B) pour un branchement 100% automatique vers Google Meet.
- Documentation : Guide de dépannage et instructions Google Meet intégrés directement dans la console.

### Changed
- Tests unitaires : Isolation complète via mocking des classes parentes et gestion des timeouts.

### Fixed
- Défaillances de branchement audio : Redirection automatique même en cas de crash des libs standards.

## [Sprint 3] - 2026-02-16
### Added
- Sprint 3 terminé : Google Meet Ready avec micro virtuel fonctionnel.
- PBI-006 : Routage Micro Virtuel pour Google Meet via PipeWire.
- Documentation `SETUP_GOOGLE_MEET.md` pour configuration utilisateur.
- Workflow CI temporaire pour contourner les tests GPU sur CPU.

### Changed
- Architecture micro virtuel : Correction des problèmes de détection SoundDevice.
- Tests unitaires : Refactoring pour contourner les problèmes de mocking asynchrone.
- CI : Workflow temporaire pour tests pertinents uniquement (ticket #7).

### Fixed
- BUG-001 : SoundDevice ne détecte pas le sink virtuel PipeWire.
- BUG-002 : Tests unitaires `MeetPipeline` échouent à cause de problèmes de mocking.

## [Sprint 2] - 2026-02-15
### Added
- Sprint 2 terminé : Pipeline de traduction complet opérationnel.
- PBI-002 : Moteur de Synthèse (TTS) Kokoro-82M intégré.
- PBI-003 : Logique de traduction MarianMT via CTranslate2.

### Changed
- Architecture : Pipeline asynchrone avec `asyncio.Queue` pour découplage.
- Robustesse audio : Normalisation automatique et resampling.

## [Sprint 1] - 2026-02-15
### Added
- Sprint 1 terminé : Pipeline de transcription opérationnel.
- PBI-001 : Intégration de Faster-Whisper avec le modèle `large-v3`.
- PBI-000 : PoC Audio avec capture Micro + Système sur PipeWire.

### Changed
- Modèle STT : `distil-large-v3` -> `large-v3` (pour corriger les hallucinations linguistiques).
- Paramètres VAD : `min_silence_duration_ms` porté à 800ms.

## 💡 LEÇONS APPRISES (SPRINT 4 - Robustesse CI & Audio)
- **Mocking Multi-Niveau (Isolation)** : Pour tester un pipeline hérité sans bloquer la CI, il est indispensable de mocker la classe parente (`AsyncPipeline.start`) tout en laissant la logique de la classe enfant (`MeetPipeline.start`) s'exécuter. Cela permet de vérifier l'orchestration spécifique (création du micro) sans déclencher les effets de bord lourds ou infinis du parent.
- **Side-Effects pour Sortie de Boucle** : Les boucles infinies asynchrones (`while is_running`) sont des nids à timeouts en CI. L'utilisation systématique de `side_effect` sur les méthodes mockées pour basculer les flags de contrôle (`is_running = False`) est la méthode la plus fiable pour garantir la terminaison des tests unitaires.
- **Sécurité Temporelle (Wait_for)** : Chaque exécution de boucle asynchrone dans un test doit être enveloppée dans un `asyncio.wait_for` avec un timeout strict (ex: 1.0s) pour éviter qu'un échec de logique ne bloque l'intégralité de la suite de tests.
- **Durcissement Audio Défensif** : La gestion des ressources système (PulseAudio) ne doit pas se fier uniquement aux flags internes (`is_created`). Une approche défensive utilisant des purges par pattern (`grep "vox"`) avant toute création garantit la stabilité même après un crash brutal de l'application.
- **Pollution Visuelle et Silence Technique** : Maintenir une sortie console propre est un critère de qualité à part entière. Un échec de test ne doit pas être noyé dans des logs non sollicités.

## 💡 LEÇONS APPRISES (SPRINT 3 - Google Meet)
- **Mocking Asynchrone Profond** : Pour tester un pipeline asynchrone complexe sans dépendances système (PulseAudio), il est crucial de mocker non seulement les appels externes, mais aussi la méthode `start` de la classe parente si elle lance des boucles infinies. L'utilisation de `patch('src.core.pipeline.AsyncPipeline.start', new_callable=AsyncMock)` a été déterminante.
- **Isolation des Tests Unitaires** : Les tests unitaires ne doivent jamais dépendre de l'état du système audio réel (qui varie selon la machine/CI). L'abstraction via `VirtualMicrophone` et son injection de dépendance (ou mocking) est la seule façon fiable de tester la logique métier du pipeline.
- **Nettoyage des Ressources** : Les tests doivent garantir que les ressources (threads, sinks) sont libérées même en cas d'échec, sinon les tests suivants échouent en cascade ("Device or resource busy").
- **PipeWire vs Navigateurs** : Même si `pactl` crée correctement un sink virtuel avec source `.monitor`, les navigateurs (Chrome/Edge) peuvent ne pas voir toutes les sources disponibles. Recommander aux utilisateurs de redémarrer le navigateur ou d'utiliser des noms plus simples.
- **SoundDevice Limitations** : La bibliothèque `sounddevice` ne trouve pas toujours automatiquement les devices PipeWire nouvellement créés. Il faut améliorer la détection ou utiliser une approche alternative pour le playback audio.
- **Tests Asynchrones Complexes** : Les tests unitaires de pipelines asynchrones avec mocking nécessitent une attention particulière aux appels `super()` et aux méthodes parentes. Les mocks doivent être placés au bon niveau d'abstraction.
- **Documentation Dépannage** : Une documentation technique complète n'est pas suffisante ; il faut aussi inclure un guide de dépannage pour les problèmes courants des utilisateurs finaux (navigateurs, permissions, redémarrages).
- **Performance vs UX** : Le chargement des modèles (30-60s) crée une mauvaise expérience utilisateur. Il faut séparer la configuration rapide (micro virtuel) du démarrage complet (modèles) pour une meilleure UX.

## 💡 LEÇONS APPRISES (SPRINT 2)
- **Robustesse Audio** : Ne jamais assumer le format d'entrée. L'intégration de `torchaudio.transforms.Resample` et d'une normalisation mono automatique est indispensable pour un pipeline "Real-World".
- **Gestion du Silence Technique** : Le module `logging` combiné à un mécanisme anti-flood (vérification du dernier message d'erreur) est vital pour éviter la saturation des disques et du processeur lors de boucles infinies asynchrones.
- **Compatibilité NumPy 2.0** : L'utilisation de bibliothèques ML legacy (comme `kokoro-onnx`) nécessite parfois des monkey-patches sur `np.load` pour restaurer le support de `allow_pickle=True` (à manipuler avec précaution pour la sécurité).
- **Orchestration Asynchrone** : Le découplage par `asyncio.Queue` permet d'absorber les pics de charge (ex: une phrase longue à traduire) sans bloquer la capture audio.
- **Latence et Réseau** : Les tokenizers de Transformers effectuent des vérifications réseau par défaut. Pour un pipeline temps réel, il est crucial de pré-charger les modèles ou d'utiliser `HF_HUB_OFFLINE=1` pour garantir une latence stable sous les 2 secondes.

## 💡 LEÇONS APPRISES (SPRINT 1)
- **Distillation vs Fidélité** : Les modèles distillés (distil-whisper) ont tendance à forcer la sortie vers la langue de pré-entraînement majoritaire (Anglais) lors de segments courts ou bruités. Le modèle complet est indispensable pour une traduction bidirectionnelle fiable.
- **Trimming Audio** : La transcription gagne en vitesse et en précision si on retire les quelques millisecondes de silence que la VAD laisse parfois en début/fin de segment.
- **Rythme Humain** : 480ms de silence est trop court pour la parole naturelle ; cela coupe les phrases lors des pauses respiratoires. 800ms est le "sweet spot" pour la fluidité.
- **Bridge Sync/Async** : Utilisation de `asyncio.run_coroutine_threadsafe` pour la thread-safety entre les callbacks audio et la boucle asynchrone.
