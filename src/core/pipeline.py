import asyncio
import numpy as np
from src.core.vad import VADDetector
from src.stt.transcriber import Transcriber

class AsyncPipeline:
    def __init__(self, vad_threshold=0.5, model_size="large-v3"):
        self.vad = VADDetector(threshold=vad_threshold)
        self.transcriber = Transcriber(model_size=model_size)
        self.audio_queue = asyncio.Queue()
        self.transcription_queue = asyncio.Queue()
        self.is_running = False
        
        # Accumulateur de segments audio
        self.current_segment = []
        self.silence_chunks = 0
        self.MAX_SILENCE_CHUNKS = 25  # Environ 800ms de silence avant de couper (25 * 32ms)

    async def add_audio_chunk(self, chunk: np.ndarray):
        """Ajoute un chunk audio (16kHz) au pipeline."""
        await self.audio_queue.put(chunk)

    async def process_audio_loop(self):
        """Boucle de traitement VAD et découpage en segments."""
        self.is_running = True
        while self.is_running:
            try:
                chunk = await self.audio_queue.get()
                is_speech = self.vad.is_speech(chunk)
                
                if is_speech:
                    if not self.current_segment:
                        # On peut optionnellement ajouter un petit buffer de pré-roll ici
                        pass
                    self.current_segment.append(chunk)
                    self.silence_chunks = 0
                else:
                    if self.current_segment:
                        self.silence_chunks += 1
                        self.current_segment.append(chunk)
                        
                        if self.silence_chunks >= self.MAX_SILENCE_CHUNKS:
                            # Fin de segment détectée
                            # On retire le silence excédentaire de la fin avant l'envoi
                            actual_segment = self.current_segment[:-self.MAX_SILENCE_CHUNKS]
                            if actual_segment:
                                full_segment = np.concatenate(actual_segment)
                                await self.transcription_queue.put(full_segment)
                            self.current_segment = []
                            self.silence_chunks = 0
                
                self.audio_queue.task_done()
            except Exception as e:
                print(f"Error in process_audio_loop: {e}")
                await asyncio.sleep(0.1)

    async def transcription_loop(self):
        """Boucle de transcription des segments validés."""
        while self.is_running:
            try:
                segment = await self.transcription_queue.get()
                text, info = self.transcriber.transcribe(segment)
                if text:
                    print(f"[{info.language}] {text}")
                self.transcription_queue.task_done()
            except Exception as e:
                print(f"Error in transcription_loop: {e}")
                await asyncio.sleep(0.1)

    def stop(self):
        self.is_running = False
