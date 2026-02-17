"""
Pipeline étendu pour Google Meet avec micro virtuel.
"""
import asyncio
import numpy as np
import time
import logging
from typing import Optional

from src.core.pipeline import AsyncPipeline
from src.core.virtual_mic import VirtualMicrophone

logger = logging.getLogger(__name__)

class MeetPipeline(AsyncPipeline):
    """
    Pipeline étendu pour Google Meet avec micro virtuel.
    
    Hérite du pipeline de base et ajoute :
    - Gestion du micro virtuel pour Google Meet
    - Injection audio dans le micro virtuel
    - Contrôles pour réunion
    """
    
    def __init__(self, vad_threshold=0.5, model_size="large-v3", device="auto", 
                 input_sample_rate=16000, virtual_mic_name="vox-transync-mic"):
        """
        Initialise le pipeline Google Meet.
        
        Args:
            virtual_mic_name: Nom du micro virtuel à créer
        """
        super().__init__(vad_threshold, model_size, device, input_sample_rate)
        
        self.virtual_mic_name = virtual_mic_name
        self.virtual_mic: Optional[VirtualMicrophone] = None
        self.use_virtual_mic = False
        self.translation_mode = "fr-en"  # Par défaut: français vers anglais
        
    async def start(self, use_virtual_mic: bool = True):
        """
        Démarre le pipeline avec option micro virtuel.
        
        Args:
            use_virtual_mic: Si True, crée et utilise le micro virtuel
        """
        self.use_virtual_mic = use_virtual_mic
        
        if use_virtual_mic:
            logger.info("Configuration du micro virtuel pour Google Meet...")
            self.virtual_mic = VirtualMicrophone(self.virtual_mic_name)
            
            if not self.virtual_mic.create_virtual_sink():
                logger.error("Échec création micro virtuel, utilisation sortie par défaut")
                self.use_virtual_mic = False
            else:
                self.virtual_mic.start_playback()
                logger.info("Micro virtuel configuré et prêt")
                logger.info(self.virtual_mic.get_setup_instructions())
        
        # Démarrer les boucles parent
        await super().start()
        
    async def stop(self):
        """Arrête le pipeline et nettoie le micro virtuel."""
        # Arrêter le pipeline parent
        self.is_running = False
        
        # Nettoyer le micro virtuel
        if self.virtual_mic and self.use_virtual_mic:
            self.virtual_mic.stop_playback_thread()
            self.virtual_mic.destroy_virtual_sink()
            logger.info("Micro virtuel nettoyé")
        
        logger.info("Pipeline Google Meet arrêté")
    
    async def tts_loop(self):
        """Boucle de synthèse vocale étendue avec micro virtuel."""
        logger.info("Starting TTS loop (Google Meet mode)...")
        while self.is_running:
            try:
                text, lang, start_time = await self.tts_queue.get()
                
                # Mapping pour Kokoro basé sur la langue
                if lang == "en":
                    voice = "af_sarah"
                    kk_lang = "en-us"
                else:  # français
                    voice = "ff_siwis"
                    kk_lang = "fr-fr"
                
                # Générer l'audio TTS
                samples, sample_rate = self.tts.generate(text, voice=voice, lang=kk_lang)
                
                if samples is not None:
                    end_time = time.time()
                    latency = end_time - start_time
                    logger.info(f"E2E Latency: {latency:.2f}s")
                    
                    # Jouer l'audio via micro virtuel ou sortie par défaut
                    if self.use_virtual_mic and self.virtual_mic:
                        self.virtual_mic.play_audio(samples, sample_rate)
                        logger.debug(f"Audio injecté dans micro virtuel: {len(samples)} samples")
                    else:
                        self.tts.play(samples, sample_rate)
                        logger.debug(f"Audio joué sur sortie par défaut: {len(samples)} samples")
                
                self.tts_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in tts_loop: {e}")
                await asyncio.sleep(0.5)
    
    def set_translation_mode(self, mode: str):
        """
        Définit le mode de traduction.
        
        Args:
            mode: "fr-en" (français vers anglais) ou "en-fr" (anglais vers français)
        """
        valid_modes = ["fr-en", "en-fr"]
        if mode not in valid_modes:
            logger.warning(f"Mode invalide: {mode}. Utilisation: {valid_modes}")
            return
        
        self.translation_mode = mode
        logger.info(f"Mode de traduction défini: {mode}")
    
    async def translation_loop(self):
        """Boucle de traduction étendue avec gestion de mode."""
        logger.info("Starting translation loop (Google Meet mode)...")
        while self.is_running:
            try:
                text, source_lang, start_time = await self.translation_queue.get()
                
                # Déterminer la langue cible basée sur le mode
                if self.translation_mode == "fr-en":
                    # Seulement traduire si source est français
                    if source_lang == "fr":
                        target_lang = "en"
                        translated = self.translator.translate(text, source_lang, target_lang)
                        logger.info(f"TRAD [{target_lang}]: {translated}")
                        await self.tts_queue.put((translated, target_lang, start_time))
                    else:
                        # Ignorer l'anglais en mode fr-en
                        logger.debug(f"Ignoré (mode fr-en): {text}")
                
                elif self.translation_mode == "en-fr":
                    # Seulement traduire si source est anglais
                    if source_lang == "en":
                        target_lang = "fr"
                        translated = self.translator.translate(text, source_lang, target_lang)
                        logger.info(f"TRAD [{target_lang}]: {translated}")
                        await self.tts_queue.put((translated, target_lang, start_time))
                    else:
                        # Ignorer le français en mode en-fr
                        logger.debug(f"Ignoré (mode en-fr): {text}")
                
                else:
                    # Mode bidirectionnel (hérité)
                    target_lang = "en" if source_lang == "fr" else "fr"
                    translated = self.translator.translate(text, source_lang, target_lang)
                    logger.info(f"TRAD [{target_lang}]: {translated}")
                    await self.tts_queue.put((translated, target_lang, start_time))
                
                self.translation_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in translation_loop: {e}")
                await asyncio.sleep(0.5)
    
    def get_status(self) -> dict:
        """
        Retourne l'état actuel du pipeline.
        
        Returns:
            Dictionnaire avec statut
        """
        status = {
            "running": self.is_running,
            "use_virtual_mic": self.use_virtual_mic,
            "translation_mode": self.translation_mode,
            "virtual_mic_name": self.virtual_mic_name if self.virtual_mic else None,
            "audio_queue_size": self.audio_queue.qsize(),
            "transcription_queue_size": self.transcription_queue.qsize(),
            "translation_queue_size": self.translation_queue.qsize(),
            "tts_queue_size": self.tts_queue.qsize(),
        }
        return status


async def demo_google_meet():
    """Démonstration du pipeline Google Meet."""
    import soundfile as sf
    import sounddevice as sd
    
    print("=== DÉMO GOOGLE MEET PIPELINE ===\n")
    
    # Créer le pipeline (Large-v3 sur GPU)
    pipeline = MeetPipeline(model_size="large-v3")
    
    print("1. Démarrage avec micro virtuel...")
    # On lance le pipeline en tâche de fond pour ne pas bloquer
    pipeline_task = asyncio.create_task(pipeline.start(use_virtual_mic=True))
    
    # On laisse le temps au pipeline de s'initialiser (création micro, chargement modèles)
    await asyncio.sleep(5)
    
    print("\n2. Statut initial:")
    status = pipeline.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n3. MODE LIVE ACTIVÉ (Parlez maintenant !)")
    print("   Le pipeline écoute votre micro réel.")
    print("   La traduction sera envoyée vers 'vox-transync-mic' (Google Meet).")
    print("   Pressez Ctrl+C pour arrêter.\n")

    # Définition du callback audio (Bridge Sync -> Async)
    loop = asyncio.get_running_loop()
    
    def audio_callback(indata, frames, time_info, status):
        """Callback appelé par sounddevice à chaque bloc audio."""
        if status:
            print(status)
        # Copie des données pour éviter les problèmes de mémoire partagée
        chunk = indata.copy()
        # Envoi dans la queue asynchrone de manière thread-safe
        asyncio.run_coroutine_threadsafe(pipeline.add_audio_chunk(chunk), loop)

    # Configuration du stream audio d'entrée (Micro Réel)
    # On utilise default=True pour prendre le micro système par défaut
    try:
        input_stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            blocksize=4096,  # ~250ms de latence
            callback=audio_callback,
            dtype='float32'
        )
        
        # Démarrage du flux audio
        with input_stream:
            print("   🎤 Capture microphone active. Parlez...")
            while True:
                # Afficher un feedback visuel simple toutes les secondes
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur...")
    except Exception as e:
        print(f"\n❌ Erreur audio: {e}")
    finally:
        print("\n4. Arrêt du pipeline...")
        await pipeline.stop()
    
    print("\n✅ Démo terminée")
    print("\nInstructions pour Google Meet:")
    print("1. Ouvrez Google Meet")
    print("2. Paramètres Audio → Microphone")
    print(f"3. Sélectionnez: 'vox-transync-mic.monitor'")
    print("4. Lancez VoxTransync en mode Google Meet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_google_meet())