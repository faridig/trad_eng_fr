# SPRINT PLAN N°0 - Audio Proof of Concept (PoC)

**Sprint Goal** : Valider techniquement la capture simultanée du micro et du son système (Loopback) sur Pop!_OS.

---

## [PBI-000-A] Setup Environnement Audio
**Priorité** : Haute | **Estimation** : S

**User Story** : "En tant que Lead-Dev, je veux installer PipeWire et les outils audio pour commencer les tests de capture."
**Critères d'Acceptation** :
- [ ] Environnement Python 3.10+ prêt.
- [ ] Bibliothèques `sounddevice` et `pydub` (ou `pyaudio`) installées.
- [ ] Liste des devices PipeWire accessible via script.

---

## [PBI-000-B] Capture Audio Multi-Source (PoC Brute)
**Priorité** : Critique | **Estimation** : S

**User Story** : "En tant qu'utilisateur, je veux prouver que le système peut enregistrer mon micro et le son de mes haut-parleurs séparément."
**Critères d'Acceptation** :
- [ ] Script `poc_audio.py` créé.
- [ ] Enregistre 5s du Micro -> `test_micro.wav`.
- [ ] Enregistre 5s du Son Système (YouTube/Zoom) -> `test_system.wav`.
- [ ] Succès si les deux fichiers sont audibles et distincts.
