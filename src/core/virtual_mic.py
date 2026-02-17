"""
Module de gestion du micro virtuel pour Google Meet.
Utilise pulsectl pour créer un sink virtuel et injecter l'audio traduit.
"""
import time
import logging
import threading
import queue
import numpy as np
import sounddevice as sd
import pulsectl
from typing import Optional, List

logger = logging.getLogger(__name__)

class VirtualMicrophone:
    """
    Gère la création et l'utilisation d'un micro virtuel pour Google Meet.
    
    Crée un sink virtuel via PulseAudio qui peut être sélectionné
    comme micro dans Google Meet. L'audio TTS y est injecté.
    """
    
    def __init__(self, sink_name: str = "vox-transync-mic"):
        """
        Initialise le micro virtuel.
        
        Args:
            sink_name: Nom de la source virtuelle à créer (sera utilisé par Google Meet)
        """
        self.sink_name = sink_name
        self.source_name = sink_name  # Pour compatibilité
        self.output_sink_name = f"{sink_name}-output"
        self.is_created = False
        self.audio_queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback = threading.Event()
        self.sample_rate = 48000
        
        # Indices des modules PulseAudio pour le nettoyage
        self._module_indices: List[int] = []
        
    def create_virtual_sink(self) -> bool:
        """
        Crée un sink virtuel et une source pour Google Meet via pulsectl.
        """
        logger.info("Préparation de l'environnement audio avec pulsectl...")
        self.destroy_virtual_sink()
        time.sleep(0.5)

        try:
            with pulsectl.Pulse('vox-transync-setup') as pulse:
                # 1. Créer le Null Sink (Sortie TTS)
                logger.info(f"Chargement du module-null-sink: {self.output_sink_name}")
                sink_args = (
                    f"sink_name={self.output_sink_name} "
                    f"rate={self.sample_rate} "
                    "format=s16le "
                    f"sink_properties=device.description={self.output_sink_name}"
                )
                sink_idx = pulse.module_load('module-null-sink', sink_args)
                self._module_indices.append(sink_idx)
                
                # 2. Créer la Remap Source (Micro pour Meet)
                logger.info(f"Chargement du module-remap-source: {self.sink_name}")
                source_props = (
                    "device.description=\"Vox Transync Microphone\" "
                    "device.class=\"audio.input\" "
                    "device.icon_name=\"audio-input-microphone\" "
                    "device.form_factor=\"microphone\" "
                    "media.role=\"communication\""
                )
                source_args = (
                    f"source_name={self.sink_name} "
                    f"master={self.output_sink_name}.monitor "
                    f"source_properties='{source_props}'"
                )
                source_idx = pulse.module_load('module-remap-source', source_args)
                self._module_indices.append(source_idx)

                # 3. Forcer Volume et Unmute
                time.sleep(0.2)
                for sink in pulse.sink_list():
                    if sink.name == self.output_sink_name:
                        pulse.sink_mute(sink.index, mute=False)
                        pulse.volume_set_all_chans(sink, 1.0)
                
                for source in pulse.source_list():
                    if source.name == self.sink_name:
                        pulse.source_mute(source.index, mute=False)
                        pulse.volume_set_all_chans(source, 1.0)

                # 4. Loopback pour monitoring (optionnel)
                try:
                    loopback_idx = pulse.module_load('module-loopback', f"source={self.output_sink_name}.monitor latency_msec=10")
                    self._module_indices.append(loopback_idx)
                except Exception as e:
                    logger.warning(f"Échec création loopback monitoring: {e}")

            self.is_created = True
            logger.info("Architecture audio pulsectl créée avec succès.")
            
            # 5. Rafraîchissement SoundDevice (Correction bug 'Device not found')
            self._refresh_sounddevice()
            
            return True

        except Exception as e:
            logger.error(f"Erreur pulsectl lors de la création du micro virtuel: {e}")
            self.destroy_virtual_sink()
            return False

    def _refresh_sounddevice(self):
        """Rafraîchit de manière robuste la liste des périphériques sounddevice."""
        logger.info("Rafraîchissement de la liste des périphériques sounddevice...")
        try:
            # Attendre que PulseAudio propage les nouveaux devices au niveau ALSA
            time.sleep(1.0)
            sd._terminate()
            sd._initialize()
            
            # Vérification de la présence
            devices = sd.query_devices()
            found = any(self.output_sink_name in d['name'] for d in devices if d['max_output_channels'] > 0)
            if found:
                logger.info(f"✅ Device '{self.output_sink_name}' détecté par sounddevice.")
            else:
                logger.warning(f"⚠️ Device '{self.output_sink_name}' toujours invisible pour sounddevice après rafraîchissement.")
                # Tentative désespérée : un deuxième rafraîchissement après une pause
                time.sleep(1.0)
                sd._terminate()
                sd._initialize()
        except Exception as e:
            logger.error(f"Erreur critique lors du rafraîchissement sounddevice: {e}")

    def destroy_virtual_sink(self) -> bool:
        """Supprime les modules PulseAudio créés."""
        try:
            with pulsectl.Pulse('vox-transync-cleanup') as pulse:
                # 1. Décharger via les indices sauvegardés
                if self._module_indices:
                    for idx in reversed(self._module_indices):
                        try:
                            pulse.module_unload(idx)
                        except:
                            pass
                    self._module_indices = []

                # 2. Nettoyage préventif par nom (au cas où les indices soient perdus)
                for mod in pulse.module_list():
                    if 'vox-transync' in str(mod.argument):
                        try:
                            pulse.module_unload(mod.index)
                        except:
                            pass
            
            self.is_created = False
            return True
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage audio: {e}")
            return False

    def start_playback(self):
        """Démarre le thread de playback audio."""
        if self.playback_thread and self.playback_thread.is_alive():
            return
        
        self.stop_playback.clear()
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
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
        device_id = self._find_sounddevice_device_id()
        
        while not self.stop_playback.is_set():
            try:
                item = self.audio_queue.get(timeout=0.1)
                audio_data, sample_rate = item
                
                if audio_data is not None:
                    if device_id is not None:
                        sd.play(audio_data, sample_rate, device=device_id)
                    else:
                        sd.play(audio_data, sample_rate)
                    sd.wait()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erreur playback: {e}")

    def _find_sounddevice_device_id(self) -> Optional[int]:
        """Trouve l'ID sounddevice correspondant au sink de sortie."""
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if self.output_sink_name in device['name'] and device['max_output_channels'] > 0:
                    return i
        except:
            pass
        return None

    def play_audio(self, audio_data: np.ndarray, sample_rate: int):
        """Ajoute l'audio à la queue de playback."""
        if not self.is_created:
            if not self.create_virtual_sink():
                return
        
        if audio_data.ndim > 1:
            audio_data = audio_data.squeeze()
        
        self.audio_queue.put((audio_data, sample_rate))

    def get_setup_instructions(self) -> str:
        """Retourne les instructions de configuration."""
        if not self.is_created:
            return "Micro virtuel non configuré."
        
        return f"""
        === CONFIGURATION GOOGLE MEET ===
        1. Sélectionnez le micro: "Vox Transync Microphone" (ou {self.sink_name})
        2. Vérifiez que la sortie audio est votre haut-parleur habituel.
        """

    def __enter__(self):
        self.create_virtual_sink()
        self.start_playback()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_playback_thread()
        self.destroy_virtual_sink()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== TEST MICRO VIRTUEL (Architecture pulsectl) ===")
    vmic = VirtualMicrophone()
    if vmic.create_virtual_sink():
        print("✅ Micro virtuel créé avec succès.")
        # Générer un court silence/bip pour tester sounddevice
        duration = 0.5
        t = np.linspace(0, duration, int(vmic.sample_rate * duration), False)
        test_audio = 0.1 * np.sin(2 * np.pi * 440 * t)
        vmic.start_playback()
        vmic.play_audio(test_audio, vmic.sample_rate)
        time.sleep(1)
        vmic.stop_playback_thread()
        vmic.destroy_virtual_sink()
        print("✅ Test terminé et micro nettoyé.")
    else:
        print("❌ Échec de la création du micro virtuel.")
