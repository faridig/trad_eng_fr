"""
Module de gestion du micro virtuel pour Google Meet.
Utilise PipeWire/PulseAudio pour créer un sink virtuel et injecter l'audio traduit.
"""
import subprocess
import time
import logging
import threading
import queue
import numpy as np
import sounddevice as sd
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class VirtualMicrophone:
    """
    Gère la création et l'utilisation d'un micro virtuel pour Google Meet.
    
    Crée un sink virtuel via PipeWire/PulseAudio qui peut être sélectionné
    comme micro dans Google Meet. L'audio TTS y est injecté.
    """
    
    def __init__(self, sink_name: str = "vox-transync-mic"):
        """
        Initialise le micro virtuel.
        
        Args:
            sink_name: Nom du sink virtuel à créer
        """
        self.sink_name = sink_name
        self.sink_index: Optional[int] = None
        self.source_name: Optional[str] = None
        self.source_index: Optional[int] = None
        self.is_created = False
        self.audio_queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback = threading.Event()
        self.sample_rate = 48000  # Fréquence standard pour Google Meet
        
    def create_virtual_sink(self) -> bool:
        """
        Crée un sink virtuel et sa source associée.
        
        Returns:
            True si la création a réussi, False sinon
        """
        try:
            logger.info(f"Création du sink virtuel '{self.sink_name}'...")
            
            # Créer un null-sink (sink virtuel)
            # module-null-sink crée à la fois un sink et une source
            cmd = [
                "pactl", "load-module", "module-null-sink",
                f"sink_name={self.sink_name}",
                f"sink_properties=device.description={self.sink_name}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            module_index = result.stdout.strip()
            
            if not module_index.isdigit():
                logger.error(f"Échec création sink: {result.stderr}")
                return False
                
            logger.info(f"Sink virtuel créé (module index: {module_index})")
            
            # Récupérer les informations du sink créé
            time.sleep(0.5)  # Laisser le temps à PulseAudio
            
            # Trouver l'index du sink
            sinks_cmd = ["pactl", "list", "sinks", "short"]
            sinks_result = subprocess.run(sinks_cmd, capture_output=True, text=True, check=True)
            
            for line in sinks_result.stdout.strip().split('\n'):
                if line and self.sink_name in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        self.sink_index = int(parts[0])
                        logger.info(f"Sink index: {self.sink_index}")
                        break
            
            # Trouver la source associée (nom conventionnel: <sink_name>.monitor)
            self.source_name = f"{self.sink_name}.monitor"
            
            sources_cmd = ["pactl", "list", "sources", "short"]
            sources_result = subprocess.run(sources_cmd, capture_output=True, text=True, check=True)
            
            for line in sources_result.stdout.strip().split('\n'):
                if line and self.source_name in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        self.source_index = int(parts[0])
                        logger.info(f"Source index: {self.source_index}")
                        break
            
            # Créer un loopback pour monitoring (optionnel)
            # Cela permet d'entendre ce qui est envoyé au micro virtuel
            loopback_cmd = [
                "pactl", "load-module", "module-loopback",
                f"source={self.source_name}",
                "latency_msec=10"
            ]
            
            subprocess.run(loopback_cmd, capture_output=True, text=True)
            logger.info("Loopback de monitoring créé")
            
            self.is_created = True
            logger.info(f"Micro virtuel '{self.sink_name}' créé avec succès")
            logger.info(f"Source disponible: {self.source_name}")
            logger.info("Configurez Google Meet pour utiliser cette source comme micro")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur création sink virtuel: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return False
    
    def destroy_virtual_sink(self) -> bool:
        """
        Supprime le sink virtuel créé.
        
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            if not self.is_created:
                logger.warning("Aucun sink virtuel à supprimer")
                return True
            
            logger.info(f"Suppression du sink virtuel '{self.sink_name}'...")
            
            # Trouver et décharger tous les modules associés
            modules_cmd = ["pactl", "list", "modules", "short"]
            modules_result = subprocess.run(modules_cmd, capture_output=True, text=True, check=True)
            
            modules_to_unload = []
            for line in modules_result.stdout.strip().split('\n'):
                if line and self.sink_name in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        modules_to_unload.append(parts[0])
            
            # Décharger les modules
            for module_id in modules_to_unload:
                unload_cmd = ["pactl", "unload-module", module_id]
                subprocess.run(unload_cmd, capture_output=True, text=True)
                logger.debug(f"Module {module_id} déchargé")
            
            self.is_created = False
            self.sink_index = None
            self.source_index = None
            logger.info("Sink virtuel supprimé avec succès")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur suppression sink: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return False
    
    def start_playback(self):
        """Démarre le thread de playback audio."""
        if self.playback_thread and self.playback_thread.is_alive():
            logger.warning("Playback déjà en cours")
            return
        
        self.stop_playback.clear()
        self.playback_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True
        )
        self.playback_thread.start()
        logger.info("Thread de playback démarré")
    
    def stop_playback_thread(self):
        """Arrête le thread de playback audio."""
        self.stop_playback.set()
        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)
            logger.info("Thread de playback arrêté")
    
    def _playback_loop(self):
        """Boucle de playback qui lit l'audio de la queue et le joue."""
        logger.debug("Démarrage boucle de playback")
        
        try:
            # Configurer sounddevice pour utiliser le sink virtuel
            # Note: sounddevice utilise par défaut la sortie par défaut
            # Pour utiliser notre sink, il faut trouver le device_id correspondant
            device_id = self._find_sounddevice_device_id()
            
            while not self.stop_playback.is_set():
                try:
                    # Récupérer l'audio de la queue avec timeout
                    audio_data, sample_rate = self.audio_queue.get(timeout=0.1)
                    
                    if audio_data is not None:
                        # Jouer l'audio
                        if device_id is not None:
                            sd.play(audio_data, sample_rate, device=device_id)
                        else:
                            sd.play(audio_data, sample_rate)
                        
                        # Attendre la fin de la lecture
                        sd.wait()
                        
                except queue.Empty:
                    # Queue vide, continuer
                    continue
                except Exception as e:
                    logger.error(f"Erreur playback audio: {e}")
                    
        except Exception as e:
            logger.error(f"Erreur boucle playback: {e}")
        
        logger.debug("Fin boucle de playback")
    
    def _find_sounddevice_device_id(self) -> Optional[int]:
        """
        Trouve l'ID du device sounddevice correspondant au sink virtuel.
        
        Returns:
            ID du device ou None si non trouvé
        """
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if self.sink_name in device['name'] and device['max_output_channels'] > 0:
                    logger.info(f"Device sounddevice trouvé: {device['name']} (id: {i})")
                    return i
        except Exception as e:
            logger.warning(f"Impossible de trouver device sounddevice: {e}")
        
        logger.warning(f"Device sounddevice pour '{self.sink_name}' non trouvé, utilisation par défaut")
        return None
    
    def play_audio(self, audio_data: np.ndarray, sample_rate: int):
        """
        Ajoute l'audio à la queue de playback.
        
        Args:
            audio_data: Données audio numpy
            sample_rate: Fréquence d'échantillonnage
        """
        if not self.is_created:
            logger.warning("Micro virtuel non créé, création automatique...")
            if not self.create_virtual_sink():
                logger.error("Impossible de créer micro virtuel, audio ignoré")
                return
        
        # S'assurer que l'audio est au bon format
        if audio_data.ndim > 1:
            audio_data = audio_data.squeeze()
        
        # Resample si nécessaire (Google Meet attend 48kHz)
        if sample_rate != self.sample_rate:
            # Conversion simple (pour MVP)
            import scipy.signal as signal
            if len(audio_data) > 0:
                num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)
                sample_rate = self.sample_rate
        
        # Ajouter à la queue
        self.audio_queue.put((audio_data, sample_rate))
        logger.debug(f"Audio ajouté à la queue: {len(audio_data)} samples @ {sample_rate}Hz")
    
    def get_setup_instructions(self) -> str:
        """
        Retourne les instructions de configuration pour Google Meet.
        
        Returns:
            Instructions formatées
        """
        if not self.is_created or not self.source_name:
            return "Micro virtuel non configuré. Exécutez create_virtual_sink() d'abord."
        
        instructions = f"""
        === CONFIGURATION GOOGLE MEET ===
        
        1. Ouvrez Google Meet
        2. Cliquez sur les trois points (⋮) → Paramètres
        3. Allez dans l'onglet "Audio"
        4. Dans "Microphone", sélectionnez: "{self.source_name}"
        5. Testez le micro avec le bouton "Test le microphone"
        6. La traduction sera maintenant audible dans Google Meet
        
        Note: Le micro virtuel est: {self.source_name}
        """
        return instructions
    
    def __enter__(self):
        """Context manager entry."""
        self.create_virtual_sink()
        self.start_playback()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_playback_thread()
        self.destroy_virtual_sink()


def test_virtual_microphone():
    """Test du micro virtuel."""
    import time
    
    print("=== TEST MICRO VIRTUEL ===")
    
    with VirtualMicrophone() as vmic:
        print("Micro virtuel créé")
        print(vmic.get_setup_instructions())
        
        # Générer un bip de test
        duration = 1.0  # secondes
        t = np.linspace(0, duration, int(vmic.sample_rate * duration), False)
        test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        print("Envoi d'un bip test (440 Hz, 1 seconde)...")
        vmic.play_audio(test_audio, vmic.sample_rate)
        
        # Attendre la fin de la lecture
        time.sleep(2)
        
        print("Test terminé")
    
    print("Micro virtuel nettoyé")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_virtual_microphone()