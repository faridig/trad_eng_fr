import asyncio
import numpy as np
import time
import logging
import torch
import torchaudio.transforms as T
from src.core.vad import VADDetector
from src.stt.transcriber import Transcriber
from src.core.translator import Translator
from src.core.tts import TTS

# Configuration du logger pour éviter la pollution de la console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncPipeline:
    def __init__(self, vad_threshold=0.5, model_size="large-v3", device="auto", input_sample_rate=16000):
        self.vad = VADDetector(threshold=vad_threshold)
        self.transcriber = Transcriber(model_size=model_size)
        self.translator = Translator(device=device)
        self.tts = TTS(device=device)
        
        self.input_sample_rate = input_sample_rate
        self.target_sample_rate = 16000
        self.resampler = None
        if self.input_sample_rate != self.target_sample_rate:
            self.resampler = T.Resample(self.input_sample_rate, self.target_sample_rate)
        
        self.audio_queue = asyncio.Queue()
        self.transcription_queue = asyncio.Queue()
        self.translation_queue = asyncio.Queue()
        self.tts_queue = asyncio.Queue()
        
        self.is_running = False
        self._last_error_msg = None
        
        # Accumulateur de segments audio
        self.current_segment = []
        self.silence_chunks = 0
        self.MAX_SILENCE_CHUNKS = 25  # Environ 800ms de silence (25 * 32ms)

    async def add_audio_chunk(self, chunk: np.ndarray):
        """Ajoute un chunk audio au pipeline. Normalisation mono automatique."""
        if not self.is_running:
            return

        try:
            # Normalisation mono immédiate
            if chunk.ndim > 1:
                chunk = chunk.mean(axis=-1)
            
            # Resampling si nécessaire
            if self.resampler is not None:
                tensor_chunk = torch.from_numpy(chunk.astype(np.float32)).unsqueeze(0)
                chunk = self.resampler(tensor_chunk).squeeze(0).numpy()
            
            await self.audio_queue.put(chunk)
        except Exception as e:
            msg = f"Error adding audio chunk: {e}"
            if msg != self._last_error_msg:
                logger.error(msg)
                self._last_error_msg = msg

    async def process_audio_loop(self):
        """Boucle de traitement VAD et découpage en segments."""
        self.is_running = True
        logger.info("Starting audio processing loop...")
        while self.is_running:
            try:
                chunk = await self.audio_queue.get()
                is_speech = self.vad.is_speech(chunk)
                
                if is_speech:
                    self.current_segment.append(chunk)
                    self.silence_chunks = 0
                else:
                    if self.current_segment:
                        self.silence_chunks += 1
                        self.current_segment.append(chunk)
                        
                        if self.silence_chunks >= self.MAX_SILENCE_CHUNKS:
                            # Fin de segment détectée
                            actual_segment = self.current_segment[:-self.MAX_SILENCE_CHUNKS]
                            if actual_segment:
                                full_segment = np.concatenate(actual_segment)
                                start_time = time.time()
                                await self.transcription_queue.put((full_segment, start_time))
                            self.current_segment = []
                            self.silence_chunks = 0
                
                self.audio_queue.task_done()
            except Exception as e:
                msg = f"Error in process_audio_loop: {e}"
                if msg != self._last_error_msg:
                    logger.error(msg)
                    self._last_error_msg = msg
                await asyncio.sleep(0.5) # Ralentir en cas d'erreur persistante

    async def transcription_loop(self):
        """Boucle de transcription."""
        logger.info("Starting transcription loop...")
        while self.is_running:
            try:
                segment, start_time = await self.transcription_queue.get()
                text, info = self.transcriber.transcribe(segment)
                if text:
                    logger.info(f"STT [{info.language}]: {text}")
                    await self.translation_queue.put((text, info.language, start_time))
                self.transcription_queue.task_done()
            except Exception as e:
                logger.error(f"Error in transcription_loop: {e}")
                await asyncio.sleep(0.5)

    async def translation_loop(self):
        """Boucle de traduction."""
        logger.info("Starting translation loop...")
        while self.is_running:
            try:
                text, source_lang, start_time = await self.translation_queue.get()
                target_lang = "en" if source_lang == "fr" else "fr"
                
                translation = self.translator.translate(text, source_lang, target_lang)
                if translation:
                    logger.info(f"TRAD [{target_lang}]: {translation}")
                    await self.tts_queue.put((translation, target_lang, start_time))
                self.translation_queue.task_done()
            except Exception as e:
                logger.error(f"Error in translation_loop: {e}")
                await asyncio.sleep(0.5)

    async def tts_loop(self):
        """Boucle de synthèse vocale et lecture."""
        logger.info("Starting TTS loop...")
        while self.is_running:
            try:
                text, lang, start_time = await self.tts_queue.get()
                
                # Mapping pour Kokoro
                voice = "af_sarah"
                kk_lang = "en-us" if lang == "en" else "fr-fr"
                
                samples, sample_rate = self.tts.generate(text, voice=voice, lang=kk_lang)
                if samples is not None:
                    end_time = time.time()
                    latency = end_time - start_time
                    logger.info(f"E2E Latency: {latency:.2f}s")
                    self.tts.play(samples, sample_rate)
                
                self.tts_queue.task_done()
            except Exception as e:
                logger.error(f"Error in tts_loop: {e}")
                await asyncio.sleep(0.5)

    async def start(self):
        """Lance toutes les boucles du pipeline."""
        tasks = [
            asyncio.create_task(self.process_audio_loop()),
            asyncio.create_task(self.transcription_loop()),
            asyncio.create_task(self.translation_loop()),
            asyncio.create_task(self.tts_loop())
        ]
        await asyncio.gather(*tasks)

    def stop(self):
        self.is_running = False
