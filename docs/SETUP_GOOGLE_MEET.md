# Configuration Google Meet pour VoxTransync

Ce guide explique comment configurer VoxTransync pour une utilisation avec Google Meet.

## Prérequis

- **Système d'exploitation** : Pop!_OS (ou autre distribution Linux avec PipeWire/PulseAudio)
- **Casque audio avec micro** : Recommandé pour éviter les boucles de feedback
- **VoxTransync** : Version avec support Google Meet (Sprint 3+)

## 1. Installation des Dépendances

Assurez-vous d'avoir les dépendances audio nécessaires :

```bash
# Sur Pop!_OS / Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y pulseaudio-utils pipewire-pulse

# Vérifier que pactl est disponible
pactl --version
```

## 2. Configuration du Micro Virtuel

VoxTransync crée automatiquement un micro virtuel lors du démarrage en mode Google Meet.

### 2.1 Démarrer VoxTransync en mode Google Meet

```python
from src.core.pipeline_meet import MeetPipeline
import asyncio

async def main():
    # Créer le pipeline Google Meet
    pipeline = MeetPipeline()
    
    # Démarrer avec micro virtuel
    await pipeline.start(use_virtual_mic=True)
    
    # Le micro virtuel 'vox-transync-mic' est maintenant créé
    print("Micro virtuel configuré. Suivez les instructions ci-dessous pour Google Meet.")

asyncio.run(main())
```

### 2.2 Vérification manuelle du micro virtuel

Vous pouvez vérifier que le micro virtuel a été créé :

```bash
# Lister les sources audio disponibles
pactl list sources short | grep vox-transync

# Résultat attendu :
# 99	vox-transync-mic.monitor	module-null-sink
```

## 3. Configuration Google Meet

### 3.1 Étape par étape

1. **Ouvrir Google Meet** dans votre navigateur
2. **Rejoindre ou démarrer une réunion**
3. **Cliquer sur les trois points (⋮)** en bas à droite
4. **Sélectionner "Paramètres"**
5. **Aller dans l'onglet "Audio"**
6. **Dans la section "Microphone"**, sélectionner :
   ```
   vox-transync-mic.monitor
   ```
7. **Tester le microphone** avec le bouton "Test le microphone"
8. **Fermer les paramètres**

### 3.2 Capture d'écran de configuration

```
Google Meet → ⋮ → Paramètres → Audio → Microphone
↓
Sélectionner : vox-transync-mic.monitor
↓
Tester le microphone
```

## 4. Utilisation pendant une réunion

### 4.1 Modes de traduction

VoxTransync supporte deux modes de traduction :

1. **FR → EN** : Traduit le français vers l'anglais
   - Parlez en français → Les interlocuteurs entendent l'anglais
   - L'anglais n'est pas traduit

2. **EN → FR** : Traduit l'anglais vers le français
   - Les interlocuteurs parlent anglais → Vous entendez le français
   - Le français n'est pas traduit

### 4.2 Changer le mode de traduction

```python
# En mode FR → EN (par défaut)
pipeline.set_translation_mode("fr-en")

# En mode EN → FR
pipeline.set_translation_mode("en-fr")
```

### 4.3 Monitoring de l'état

```python
# Obtenir l'état du pipeline
status = pipeline.get_status()
print(f"Mode: {status['translation_mode']}")
print(f"Micro virtuel: {'Activé' if status['use_virtual_mic'] else 'Désactivé'}")
print(f"File d'attente audio: {status['audio_queue_size']}")
```

## 5. Dépannage

### 5.1 Problème : Micro virtuel non détecté

**Symptômes** :
- `vox-transync-mic.monitor` n'apparaît pas dans la liste des micros
- Erreur "Failed to create virtual sink" dans les logs

**Solutions** :
1. Vérifier que PipeWire/PulseAudio est en cours d'exécution :
   ```bash
   systemctl --user status pipewire-pulse
   ```
2. Redémarrer les services audio :
   ```bash
   systemctl --user restart pipewire pipewire-pulse
   ```
3. Vérifier les permissions audio :
   ```bash
   groups | grep audio
   ```
   Si vous n'êtes pas dans le groupe audio :
   ```bash
   sudo usermod -a -G audio $USER
   # Déconnexion/reconnexion nécessaire
   ```

### 5.2 Problème : Pas d'audio dans Google Meet

**Symptômes** :
- Le micro virtuel est sélectionné
- Le test de microphone fonctionne
- Mais la traduction n'est pas audible

**Solutions** :
1. Vérifier que VoxTransync est en cours d'exécution
2. Vérifier les logs pour des erreurs :
   ```bash
   # Exécuter VoxTransync avec logging détaillé
   python -m src.core.pipeline_meet 2>&1 | grep -i error
   ```
3. Tester le pipeline localement d'abord :
   ```python
   # Tester sans Google Meet
   await pipeline.start(use_virtual_mic=False)
   # Parler pour vérifier que la traduction fonctionne
   ```

### 5.3 Problème : Latence élevée

**Objectif** : < 2 secondes end-to-end

**Optimisations** :
1. Utiliser le modèle `tiny` ou `base` pour Faster-Whisper :
   ```python
   pipeline = MeetPipeline(model_size="base")
   ```
2. Réduire la sensibilité du VAD :
   ```python
   pipeline = MeetPipeline(vad_threshold=0.3)
   ```
3. Vérifier les performances système

## 6. Configuration Avancée

### 6.1 Utilisation sans interface graphique

```python
import asyncio
from src.core.pipeline_meet import MeetPipeline

class GoogleMeetTranslator:
    def __init__(self):
        self.pipeline = MeetPipeline()
    
    async def start(self):
        """Démarrer la traduction pour Google Meet."""
        print("Démarrage du traducteur Google Meet...")
        await self.pipeline.start(use_virtual_mic=True)
        
        # Afficher les instructions
        if self.pipeline.virtual_mic:
            print(self.pipeline.virtual_mic.get_setup_instructions())
    
    async def stop(self):
        """Arrêter la traduction."""
        await self.pipeline.stop()
        print("Traducteur arrêté.")
    
    def set_mode(self, mode: str):
        """Changer le mode de traduction."""
        self.pipeline.set_translation_mode(mode)
        print(f"Mode défini: {mode}")

# Utilisation
async def main():
    translator = GoogleMeetTranslator()
    await translator.start()
    
    # Changer de mode pendant l'exécution
    translator.set_mode("en-fr")
    
    # Garder le programme en cours d'exécution
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await translator.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Monitoring des performances

```python
import time
from src.core.pipeline_meet import MeetPipeline

async def monitor_performance(pipeline: MeetPipeline, interval: int = 10):
    """Monitorer les performances du pipeline."""
    while pipeline.is_running:
        status = pipeline.get_status()
        
        print(f"\n=== Performance Report ===")
        print(f"Taille file audio: {status['audio_queue_size']}")
        print(f"Taille file transcription: {status['transcription_queue_size']}")
        print(f"Taille file traduction: {status['translation_queue_size']}")
        print(f"Taille file TTS: {status['tts_queue_size']}")
        print(f"Mode: {status['translation_mode']}")
        
        await asyncio.sleep(interval)
```

## 7. Bonnes Pratiques

### 7.1 Pour une réunion efficace

1. **Test avant la réunion** : Configurer et tester avant la réunion importante
2. **Casque obligatoire** : Évite les boucles de feedback
3. **Mode approprié** : FR→EN si vous parlez français, EN→FR si vous écoutez anglais
4. **Pauses** : Arrêter la traduction pendant les longs silences

### 7.2 Pour le développeur

1. **Logs détaillés** : Activer le logging DEBUG pour le dépannage
2. **Tests unitaires** : Exécuter les tests avant le déploiement
3. **CI/CD** : Vérifier que la CI passe avant de merger

## 8. Limitations connues

1. **PipeWire requis** : Nécessite PipeWire ou PulseAudio
2. **Latence** : 1-2 secondes selon le matériel
3. **Un seul micro virtuel** : Une instance à la fois
4. **Linux uniquement** : Pour le moment

## 9. Support

Pour les problèmes non résolus par ce guide :

1. Consulter les logs : `tail -f vox_transync.log`
2. Vérifier les issues GitHub
3. Contacter l'équipe de développement

---

**Dernière mise à jour** : 16/02/2026  
**Version** : Sprint 3 - Google Meet Ready