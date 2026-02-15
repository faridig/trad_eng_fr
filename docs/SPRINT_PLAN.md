# SPRINT PLAN N°2 - Traduction et Voix (The Final Bridge)

**Sprint Goal** : Connecter la transcription à la traduction locale et générer la voix de sortie avec Kokoro-82M.

---

## [PBI-003] Pipeline de Traduction (MarianMT)
**Priorité** : Haute | **Estimation** : M

**User Story** : "En tant qu'utilisateur, je veux que mon texte français soit traduit instantanément en anglais (et vice versa)."
**Critères d'Acceptation** :
- [ ] Intégration des modèles `Helsinki-NLP/opus-mt-fr-en` et `en-fr`.
- [ ] Inférence via `CTranslate2` pour une latence < 50ms.
- [ ] Support des caractères spéciaux et de la ponctuation.

---

## [PBI-002] Synthèse Vocale (Kokoro-82M)
**Priorité** : Haute | **Estimation** : M

**User Story** : "En tant qu'interlocuteur, je veux entendre la traduction avec une voix naturelle et fluide."
**Critères d'Acceptation** :
- [ ] Intégration de `Kokoro-82M` (via Python/ONNX/GPU).
- [ ] Génération de l'audio FR et EN.
- [ ] Streaming de l'audio vers la carte son (Haut-parleurs/Casque) pour test.

---

## [PBI-002-B] Orchestration Asynchrone (Main Loop)
**Priorité** : Haute | **Estimation** : L

**User Story** : "En tant que développeur, je veux que tout le pipeline (Capture -> STT -> Trad -> TTS -> Play) s'exécute sans blocage."
**Critères d'Acceptation** :
- [ ] Mise en place de la boucle `asyncio` finale.
- [ ] Gestion des files d'attente pour chaque étape.
- [ ] Mesure de la latence "End-to-End" (Objectif < 2s).
