# SPRINT PLAN N°5 - Qualité & Performance (UX First)

**Sprint Goal** : Éliminer les hallucinations de silence, corriger le tronquage des phrases et optimiser la latence pour une expérience fluide en réunion.

---

## 🎯 CONTEXTE SPÉCIFIQUE
- **État actuel** : Connexion Google Meet robuste et CI stable.
- **Problèmes critiques** : Hallucinations ("Merci"), phrases coupées après "?", latence perceptible.
- **Objectif** : Stabilisation de la qualité de traduction et simplification du lancement.

---

## [PBI-008] BUG Filtrage des Hallucinations
**Priorité** : Haute | **Estimation** : S

**User Story** : "En tant qu'utilisateur en réunion, je ne veux pas que l'IA traduise des silences ou bruits de fond par 'Merci', afin d'éviter les interruptions inutiles."
**Dépendances** : Aucune
**Critères d'Acceptation (Gherkin)** :
- [ ] **Scenario 1** : Seuil de durée minimale
  - **GIVEN** Un segment audio capturé
  - **WHEN** La durée du segment est < 1.0 seconde
  - **THEN** Le segment est ignoré sans transcription ni traduction
- [ ] **Scenario 2** : Filtrage par mots-clés
  - **GIVEN** Une transcription contenant uniquement "Merci" ou "Thank you"
  - **WHEN** La confiance du segment (score VAD/Whisper) est faible
  - **THEN** Le segment est rejeté
- [ ] **Scenario 3** : Log de filtrage
  - **GIVEN** Un segment filtré
  - **WHEN** Le mode DEBUG est actif
  - **THEN** La console affiche "[VAD] Segment filtré (Hallucination suspectée)"

---

## [PBI-009] FEAT Segmentation Intelligente
**Priorité** : Haute | **Estimation** : M

**User Story** : "En tant qu'utilisateur posant des questions, je veux que l'intégralité de ma phrase soit traduite, même si elle contient un point d'interrogation au milieu."
**Dépendances** : Aucune
**Critères d'Acceptation (Gherkin)** :
- [ ] **Scenario 1** : Traduction multi-phrases
  - **GIVEN** Un segment audio contenant "How are you? I am fine."
  - **WHEN** Le moteur de traduction traite le texte
  - **THEN** La sortie TTS contient la traduction des DEUX phrases
- [ ] **Scenario 2** : Découpage par ponctuation
  - **GIVEN** Un texte source long
  - **WHEN** Le traducteur reçoit le bloc
  - **THEN** Le texte est découpé par `[.!?]` et chaque bloc est traduit séquentiellement avant synthèse
- [ ] **Scenario 3** : Préservation du ton
  - **GIVEN** Une question suivie d'une affirmation
  - **WHEN** La traduction est générée
  - **THEN** La ponctuation est respectée pour que le TTS garde l'intonation correcte

---

## [PBI-010] PERF Optimisation VAD (Latence)
**Priorité** : Moyenne | **Estimation** : S

**User Story** : "En tant qu'utilisateur, je veux que la traduction commence le plus vite possible après que j'ai fini de parler."
**Dépendances** : Aucune
**Critères d'Acceptation (Gherkin)** :
- [ ] **Scenario 1** : Réduction du timeout VAD
  - **GIVEN** Le paramètre `min_silence_duration_ms`
  - **WHEN** Sa valeur est passée de 800ms à 500ms
  - **THEN** Le pipeline détecte la fin de phrase 300ms plus tôt
- [ ] **Scenario 2** : Stabilité du déclenchement
  - **GIVEN** Une conversation normale
  - **WHEN** Le nouveau délai est appliqué
  - **THEN** Aucune phrase n'est coupée prématurément (sauf pauses anormalement longues)

---

## [PBI-011] UX Script de Lancement Unique
**Priorité** : Moyenne | **Estimation** : XS

**User Story** : "En tant que nouvel utilisateur, je veux lancer l'outil avec une seule commande simple pour éviter les erreurs de modules."
**Dépendances** : Aucune
**Critères d'Acceptation (Gherkin)** :
- [ ] **Scenario 1** : Fichier start.py
  - **GIVEN** La racine du projet
  - **WHEN** L'utilisateur lance `python start.py`
  - **THEN** L'application démarre correctement en gérant les PYTHONPATH nécessaires
- [ ] **Scenario 2** : Aide intégrée
  - **GIVEN** Commande `python start.py --help`
  - **WHEN** L'utilisateur l'exécute
  - **THEN** Les options principales (langues, modes) sont affichées

---

## 📊 GUIDE D'ESTIMATION APPLIQUÉ
- **XS** : Script simple (1 fichier).
- **S** : Logique simple (< 50 lignes).
- **M** : Logique métier standard (2-3 fichiers).

---

**Chef d'Orchestre, ce plan de Sprint 5 est-il validé pour exécution immédiate ?**
- **PBI-008 & 009** : Corrections critiques de qualité (Priorité absolue)
- **PBI-010** : Amélioration de la réactivité (Latence)
- **PBI-011** : Simplification de l'expérience utilisateur
