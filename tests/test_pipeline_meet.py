"""
Tests for the MeetPipeline class (Google Meet integration).
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from src.core.pipeline_meet import MeetPipeline


class TestMeetPipeline:
    """Test suite for MeetPipeline class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Fixture to mock all dependencies that load models."""
        # Patch the classes WHERE THEY ARE USED (in src.core.pipeline)
        # since src.core.pipeline uses "from src.core.vad import VADDetector"
        with patch('src.core.pipeline.VADDetector') as mock_vad, \
             patch('src.core.pipeline.Transcriber') as mock_transcriber, \
             patch('src.core.pipeline.Translator') as mock_translator, \
             patch('src.core.pipeline.TTS') as mock_tts:
            
            # Create mock instances
            mock_vad_instance = MagicMock()
            mock_vad.return_value = mock_vad_instance
            
            mock_transcriber_instance = MagicMock()
            mock_transcriber.return_value = mock_transcriber_instance
            
            mock_translator_instance = MagicMock()
            mock_translator.return_value = mock_translator_instance
            
            mock_tts_instance = MagicMock()
            mock_tts.return_value = mock_tts_instance
            
            yield {
                'vad': mock_vad_instance,
                'transcriber': mock_transcriber_instance,
                'translator': mock_translator_instance,
                'tts': mock_tts_instance
            }
    
    @pytest.fixture
    def pipeline(self, mock_dependencies):
        """Fixture to create a MeetPipeline instance with mocked dependencies."""
        return MeetPipeline()
    
    @pytest.mark.asyncio
    async def test_initialization(self, pipeline):
        """Test that MeetPipeline initializes correctly."""
        assert pipeline.virtual_mic_name == "vox-transync-mic"
        assert pipeline.virtual_mic is None
        assert pipeline.use_virtual_mic is False
        assert pipeline.translation_mode == "fr-en"
    
    @pytest.mark.asyncio
    @patch('src.core.pipeline_meet.VirtualMicrophone')
    async def test_start_with_virtual_mic_success(self, mock_virtual_mic_class, pipeline):
        """Test starting pipeline with virtual microphone successfully."""
        # Mock virtual microphone
        mock_vmic = Mock()
        mock_vmic.create_virtual_sink.return_value = True
        mock_virtual_mic_class.return_value = mock_vmic
        
        # Mock parent start method
        with patch.object(MeetPipeline, 'start', new_callable=AsyncMock) as mock_parent_start:
            await pipeline.start(use_virtual_mic=True)
            
            # Verify virtual mic was created
            mock_virtual_mic_class.assert_called_once_with("vox-transync-mic")
            mock_vmic.create_virtual_sink.assert_called_once()
            mock_vmic.start_playback.assert_called_once()
            
            # Verify parent start was called
            mock_parent_start.assert_called_once()
            
            # Verify state
            assert pipeline.use_virtual_mic is True
            assert pipeline.virtual_mic == mock_vmic
    
    @pytest.mark.asyncio
    @patch('src.core.pipeline_meet.VirtualMicrophone')
    async def test_start_with_virtual_mic_failure(self, mock_virtual_mic_class, pipeline):
        """Test starting pipeline with virtual microphone failure."""
        # Mock virtual microphone that fails to create
        mock_vmic = Mock()
        mock_vmic.create_virtual_sink.return_value = False
        mock_virtual_mic_class.return_value = mock_vmic
        
        # Mock parent start method
        with patch.object(MeetPipeline, 'start', new_callable=AsyncMock) as mock_parent_start:
            await pipeline.start(use_virtual_mic=True)
            
            # Verify virtual mic creation was attempted
            mock_virtual_mic_class.assert_called_once()
            mock_vmic.create_virtual_sink.assert_called_once()
            
            # Verify playback was NOT started
            mock_vmic.start_playback.assert_not_called()
            
            # Verify parent start was called
            mock_parent_start.assert_called_once()
            
            # Verify state (should fall back to no virtual mic)
            assert pipeline.use_virtual_mic is False
    
    @pytest.mark.asyncio
    async def test_start_without_virtual_mic(self, pipeline):
        """Test starting pipeline without virtual microphone."""
        # Mock parent start method
        with patch.object(MeetPipeline, 'start', new_callable=AsyncMock) as mock_parent_start:
            await pipeline.start(use_virtual_mic=False)
            
            # Verify parent start was called
            mock_parent_start.assert_called_once()
            
            # Verify state
            assert pipeline.use_virtual_mic is False
            assert pipeline.virtual_mic is None
    
    @pytest.mark.asyncio
    @patch('src.core.pipeline_meet.VirtualMicrophone')
    async def test_stop_with_virtual_mic(self, mock_virtual_mic_class, pipeline):
        """Test stopping pipeline with virtual microphone cleanup."""
        # Mock virtual microphone
        mock_vmic = Mock()
        mock_virtual_mic_class.return_value = mock_vmic
        
        pipeline.virtual_mic = mock_vmic
        pipeline.use_virtual_mic = True
        pipeline.is_running = True
        
        await pipeline.stop()
        
        # Verify virtual mic was cleaned up
        mock_vmic.stop_playback_thread.assert_called_once()
        mock_vmic.destroy_virtual_sink.assert_called_once()
        
        # Verify pipeline state
        assert pipeline.is_running is False
    
    @pytest.mark.asyncio
    async def test_stop_without_virtual_mic(self, pipeline):
        """Test stopping pipeline without virtual microphone."""
        pipeline.virtual_mic = None
        pipeline.use_virtual_mic = False
        pipeline.is_running = True
        
        await pipeline.stop()
        
        # Should not crash even without virtual mic
        assert pipeline.is_running is False
    
    def test_set_translation_mode_valid(self, pipeline):
        """Test setting valid translation modes."""
        # Test fr-en mode
        pipeline.set_translation_mode("fr-en")
        assert pipeline.translation_mode == "fr-en"
        
        # Test en-fr mode
        pipeline.set_translation_mode("en-fr")
        assert pipeline.translation_mode == "en-fr"
    
    def test_set_translation_mode_invalid(self, pipeline):
        """Test setting invalid translation mode."""
        # Store original mode
        original_mode = pipeline.translation_mode
        
        # Try to set invalid mode
        pipeline.set_translation_mode("invalid-mode")
        
        # Should keep original mode
        assert pipeline.translation_mode == original_mode
    
    @pytest.mark.asyncio
    async def test_translation_loop_fr_en_mode(self, pipeline):
        """Test translation loop in fr-en mode."""
        pipeline.translation_mode = "fr-en"
        pipeline.is_running = True
        
        # Mock translator
        pipeline.translator = Mock()
        pipeline.translator.translate.return_value = "Hello, this is a test"
        
        # Mock tts_queue
        pipeline.tts_queue = asyncio.Queue()
        
        # Add test items to translation queue
        await pipeline.translation_queue.put(("Bonjour, ceci est un test", "fr", 0.0))
        await pipeline.translation_queue.put(("Hello, this is English", "en", 0.0))
        
        # Run translation loop once for each item
        for _ in range(2):
            try:
                await pipeline.translation_loop()
            except asyncio.QueueEmpty:
                break
        
        # Verify only French was translated
        pipeline.translator.translate.assert_called_once()
        
        # Check tts_queue has one item (the translation)
        assert pipeline.tts_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_translation_loop_en_fr_mode(self, pipeline):
        """Test translation loop in en-fr mode."""
        pipeline.translation_mode = "en-fr"
        pipeline.is_running = True
        
        # Mock translator
        pipeline.translator = Mock()
        pipeline.translator.translate.return_value = "Bonjour, ceci est un test"
        
        # Mock tts_queue
        pipeline.tts_queue = asyncio.Queue()
        
        # Add test items to translation queue
        await pipeline.translation_queue.put(("Hello, this is English", "en", 0.0))
        await pipeline.translation_queue.put(("Bonjour, ceci est français", "fr", 0.0))
        
        # Run translation loop once for each item
        for _ in range(2):
            try:
                await pipeline.translation_loop()
            except asyncio.QueueEmpty:
                break
        
        # Verify only English was translated
        pipeline.translator.translate.assert_called_once()
        
        # Check tts_queue has one item (the translation)
        assert pipeline.tts_queue.qsize() == 1
    
    @pytest.mark.asyncio
    @patch('src.core.pipeline_meet.VirtualMicrophone')
    async def test_tts_loop_with_virtual_mic(self, mock_virtual_mic_class, pipeline):
        """Test TTS loop with virtual microphone."""
        # Mock virtual microphone
        mock_vmic = Mock()
        mock_virtual_mic_class.return_value = mock_vmic
        
        pipeline.use_virtual_mic = True
        pipeline.virtual_mic = mock_vmic
        pipeline.is_running = True
        
        # Mock TTS
        pipeline.tts = Mock()
        pipeline.tts.generate.return_value = (np.zeros(1000, dtype=np.float32), 48000)
        
        # Mock tts_queue
        pipeline.tts_queue = asyncio.Queue()
        await pipeline.tts_queue.put(("Test text", "en", 0.0))
        
        # Run tts loop once
        try:
            await pipeline.tts_loop()
        except asyncio.QueueEmpty:
            pass
        
        # Verify audio was sent to virtual mic
        mock_vmic.play_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tts_loop_without_virtual_mic(self, pipeline):
        """Test TTS loop without virtual microphone."""
        pipeline.use_virtual_mic = False
        pipeline.virtual_mic = None
        pipeline.is_running = True
        
        # Mock TTS
        pipeline.tts = Mock()
        pipeline.tts.generate.return_value = (np.zeros(1000, dtype=np.float32), 48000)
        pipeline.tts.play = Mock()
        
        # Mock tts_queue
        pipeline.tts_queue = asyncio.Queue()
        await pipeline.tts_queue.put(("Test text", "en", 0.0))
        
        # Run tts loop once
        try:
            await pipeline.tts_loop()
        except asyncio.QueueEmpty:
            pass
        
        # Verify audio was played via default TTS
        pipeline.tts.play.assert_called_once()
    
    def test_get_status(self, pipeline):
        """Test getting pipeline status."""
        pipeline.is_running = True
        pipeline.use_virtual_mic = True
        pipeline.translation_mode = "fr-en"
        pipeline.virtual_mic = Mock()
        pipeline.virtual_mic_name = "test-mic"
        
        # Mock queues
        pipeline.audio_queue = Mock(qsize=Mock(return_value=5))
        pipeline.transcription_queue = Mock(qsize=Mock(return_value=3))
        pipeline.translation_queue = Mock(qsize=Mock(return_value=2))
        pipeline.tts_queue = Mock(qsize=Mock(return_value=1))
        
        status = pipeline.get_status()
        
        assert status["running"] is True
        assert status["use_virtual_mic"] is True
        assert status["translation_mode"] == "fr-en"
        assert status["virtual_mic_name"] == "test-mic"
        assert status["audio_queue_size"] == 5
        assert status["transcription_queue_size"] == 3
        assert status["translation_queue_size"] == 2
        assert status["tts_queue_size"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])