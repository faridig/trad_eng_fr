import asyncio
import numpy as np
import time
from src.core.vad import VADDetector
from src.stt.transcriber import Transcriber
from src.core.translator import Translator
from src.core.tts import TTS

class AsyncPipeline:
    def __init__(self, vad_threshold=0.5, model_size="large-v3", device="auto"):
        self.vad = VADDetector(threshold=vad_threshold)
        self.transcriber = Transcriber(model_size=model_size)
        self.translator = Translator(device=device)
        self.tts = TTS(device=device)
        
        self.audio_queue = asyncio.Queue()
        self.transcription_queue = asyncio.Queue()
        self.translation_queue = asyncio.Queue()
        self.tts_queue = asyncio.Queue()
        
        self.is_running = False
        
        # Accumulateur de segments audio
        self.current_segment = []
        self.silence_chunks = 0
        self.MAX_SILENCE_CHUNKS = 25  # Environ 800ms de silence (25 * 32ms)

    async def add_audio_chunk(self, chunk: np.ndarray):
        """Ajoute un chunk audio (16kHz) au pipeline."""
        if self.is_running:
            await self.audio_queue.put(chunk)

    async def process_audio_loop(self):
        """Boucle de traitement VAD et découpage en segments."""
        self.is_running = True
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
                print(f"Error in process_audio_loop: {e}")
                await asyncio.sleep(0.1)

    async def transcription_loop(self):
        """Boucle de transcription."""
        while self.is_running:
            try:
                segment, start_time = await self.transcription_queue.get()
                text, info = self.transcriber.transcribe(segment)
                if text:
                    print(f"STT [{info.language}]: {text}")
                    await self.translation_queue.put((text, info.language, start_time))
                self.transcription_queue.task_done()
            except Exception as e:
                print(f"Error in transcription_loop: {e}")
                await asyncio.sleep(0.1)

    async def translation_loop(self):
        """Boucle de traduction."""
        while self.is_running:
            try:
                text, source_lang, start_time = await self.translation_queue.get()
                target_lang = "en" if source_lang == "fr" else "fr"
                
                translation = self.translator.translate(text, source_lang, target_lang)
                if translation:
                    print(f"TRAD [{target_lang}]: {translation}")
                    await self.tts_queue.put((translation, target_lang, start_time))
                self.translation_queue.task_done()
            except Exception as e:
                print(f"Error in translation_loop: {e}")
                await asyncio.sleep(0.1)

    async def tts_loop(self):
        """Boucle de synthèse vocale et lecture."""
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
                    print(f"TTS Latency: {latency:.2f}s")
                    self.tts.play(samples, sample_rate)
                
                self.tts_queue.task_done()
            except Exception as e:
                print(f"Error in tts_loop: {e}")
                await asyncio.sleep(0.1)

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
