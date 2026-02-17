"""
Module de gestion du micro virtuel pour Google Meet.
Utilise pulsectl/pactl pour créer un sink virtuel et injecter l'audio traduit.
Inclut une logique de redirection de secours "Brute Force" via pactl.
"""
import os
import time
import logging
import threading
import queue
import subprocess
import numpy as np
import sounddevice as sd
import pulsectl
from typing import Optional, List

logger = logging.getLogger(__name__)

class VirtualMicrophone:
    """
    Gère la création et l'utilisation d'un micro virtuel pour Google Meet.
    """
    
    def __init__(self, sink_name: str = "vox-transync-mic"):
        self.sink_name = sink_name
        self.source_name = sink_name
        self.output_sink_name = f"{sink_name}-output"
        self.is_created = False
        self.audio_queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback = threading.Event()
        self.sample_rate = 48000
        self._module_indices: List[int] = []
        
    def create_virtual_sink(self) -> bool:
        """Crée l'architecture audio via pulsectl."""
        logger.info("Initialisation Brute Force de l'environnement audio...")
        self.destroy_virtual_sink() # Nettoyage agressif préalable
        time.sleep(0.5)

        try:
            with pulsectl.Pulse('vox-transync-setup') as pulse:
                # 1. Null Sink
                sink_args = f"sink_name={self.output_sink_name} rate={self.sample_rate} format=s16le sink_properties=device.description={self.output_sink_name}"
                sink_idx = pulse.module_load('module-null-sink', sink_args)
                self._module_indices.append(sink_idx)
                
                # 2. Remap Source
                source_props = "device.description=\"Vox Transync Microphone\" device.class=\"audio.input\" device.icon_name=\"audio-input-microphone\" device.form_factor=\"microphone\" media.role=\"communication\""
                source_args = f"source_name={self.sink_name} master={self.output_sink_name}.monitor source_properties='{source_props}'"
                source_idx = pulse.module_load('module-remap-source', source_args)
                self._module_indices.append(source_idx)

                # 3. Unmute & Volume
                time.sleep(0.2)
                for sink in pulse.sink_list():
                    if sink.name == self.output_sink_name:
                        pulse.sink_mute(sink.index, mute=False)
                        pulse.volume_set_all_chans(sink, 1.0)
                
                for source in pulse.source_list():
                    if source.name == self.sink_name:
                        pulse.source_mute(source.index, mute=False)
                        pulse.volume_set_all_chans(source, 1.0)

            self.is_created = True
            self._refresh_sounddevice()
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la création du micro: {e}")
            return False

    def _refresh_sounddevice(self):
        """Rafraîchit la liste des périphériques sounddevice."""
        try:
            time.sleep(0.5)
            sd._terminate()
            sd._initialize()
        except:
            pass

    def destroy_virtual_sink(self) -> bool:
        """Nettoyage Agressif : décharge tous les modules contenant 'vox'."""
        logger.info("Nettoyage Agressif des modules audio 'vox'...")
        try:
            # Récupérer la liste des modules via pactl (plus direct pour le nettoyage agressif)
            cmd = ["pactl", "list", "modules", "short"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if "vox" in line:
                        parts = line.split()
                        if parts:
                            mod_id = parts[0]
                            logger.info(f"Déchargement forcé du module {mod_id}")
                            subprocess.run(["pactl", "unload-module", mod_id], capture_output=True)
            
            self.is_created = False
            self._module_indices = []
            return True
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage agressif: {e}")
            return False

    def start_playback(self):
        if self.playback_thread and self.playback_thread.is_alive():
            return
        self.stop_playback.clear()
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        logger.info("Thread de playback démarré (Prêt pour Redirection de secours)")

    def _force_redirect_stream(self):
        """Redirection de secours : arrache le flux audio de Python et le branche sur le micro virtuel."""
        try:
            pid = os.getpid()
            # 1. Lister les sink-inputs
            cmd = ["pactl", "list", "sink-inputs"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return

            # Parsing simple pour trouver l'ID du flux de notre PID
            current_id = None
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith("Entrée de la destination #") or line.startswith("Sink Input #"):
                    current_id = line.split('#')[-1]
                
                if f"application.process.id = \"{pid}\"" in line or f"application.process.id = {pid}" in line:
                    if current_id:
                        logger.info(f"Flux audio détecté (ID: {current_id}). Tentative de redirection vers {self.output_sink_name}...")
                        subprocess.run(["pactl", "move-sink-input", current_id, self.output_sink_name], capture_output=True)
                        # On ne s'arrête pas au premier au cas où il y en aurait plusieurs
        except Exception as e:
            logger.debug(f"Erreur redirection: {e}")

    def _playback_loop(self):
        device_id = self._find_sounddevice_device_id()
        
        while not self.stop_playback.is_set():
            try:
                item = self.audio_queue.get(timeout=0.1)
                audio_data, sample_rate = item
                
                if audio_data is not None:
                    # Logique de Brute Force : si device non trouvé, joue sur défaut et redirige
                    if device_id is not None:
                        sd.play(audio_data, sample_rate, device=device_id)
                    else:
                        sd.play(audio_data, sample_rate) # Sortie par défaut
                    
                    # Redirection de secours immédiate
                    self._force_redirect_stream()
                    
                    sd.wait()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erreur playback: {e}")

    def _find_sounddevice_device_id(self) -> Optional[int]:
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if self.output_sink_name in device['name'] and device['max_output_channels'] > 0:
                    return i
        except:
            pass
        return None

    def play_audio(self, audio_data: np.ndarray, sample_rate: int):
        if not self.is_created:
            self.create_virtual_sink()
        
        if audio_data.ndim > 1:
            audio_data = audio_data.squeeze()
        self.audio_queue.put((audio_data, sample_rate))

    def get_setup_instructions(self) -> str:
        return f"Sélectionnez '{self.sink_name}' dans Google Meet."

    def stop_playback_thread(self):
        self.stop_playback.set()
        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)

    def __enter__(self):
        self.create_virtual_sink()
        self.start_playback()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_playback_thread()
        self.destroy_virtual_sink()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vmic = VirtualMicrophone()
    vmic.create_virtual_sink()
    vmic.start_playback()
    # Test avec 1s de bip
    t = np.linspace(0, 1, 48000, False)
    vmic.play_audio(0.1 * np.sin(2 * np.pi * 440 * t), 48000)
    time.sleep(2)
    vmic.destroy_virtual_sink()
