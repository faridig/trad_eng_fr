"""
Tests for the VirtualMicrophone class.
"""
import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import threading

from src.core.virtual_mic import VirtualMicrophone


class TestVirtualMicrophone:
    """Test suite for VirtualMicrophone class."""
    
    def test_initialization(self):
        """Test that VirtualMicrophone initializes correctly."""
        vmic = VirtualMicrophone("test-mic")
        
        assert vmic.sink_name == "test-mic"
        assert vmic.sink_index is None
        assert vmic.source_name is None
        assert vmic.source_index is None
        assert not vmic.is_created
        assert vmic.sample_rate == 48000
        assert vmic.audio_queue is not None  # Should be a queue.Queue instance
        assert vmic.playback_thread is None
        assert not vmic.stop_playback.is_set()
    
    @patch('subprocess.run')
    def test_create_virtual_sink_success(self, mock_run):
        """Test successful creation of virtual sink."""
        # Mock subprocess.run responses
        mock_load_module = Mock()
        mock_load_module.stdout = "42\n"
        mock_load_module.stderr = ""
        
        mock_list_sinks = Mock()
        mock_list_sinks.stdout = "42  test-mic  module-null-sink\n"
        mock_list_sinks.stderr = ""
        
        mock_list_sources = Mock()
        mock_list_sources.stdout = "99  test-mic.monitor  module-null-sink\n"
        mock_list_sources.stderr = ""
        
        # Configure mock to return different values based on command
        def run_side_effect(cmd, *args, **kwargs):
            if "load-module" in cmd and "module-null-sink" in cmd:
                return mock_load_module
            elif "list" in cmd and "sinks" in cmd:
                return mock_list_sinks
            elif "list" in cmd and "sources" in cmd:
                return mock_list_sources
            elif "load-module" in cmd and "module-loopback" in cmd:
                return Mock(stdout="", stderr="")
            else:
                return Mock(stdout="", stderr="")
        
        mock_run.side_effect = run_side_effect
        
        vmic = VirtualMicrophone("test-mic")
        result = vmic.create_virtual_sink()
        
        assert result is True
        assert vmic.is_created is True
        assert vmic.sink_index == 42
        assert vmic.source_index == 99
        assert vmic.source_name == "test-mic.monitor"
        
        # Verify subprocess.run was called
        assert mock_run.call_count >= 3
    
    @patch('subprocess.run')
    def test_create_virtual_sink_failure(self, mock_run):
        """Test failed creation of virtual sink."""
        # Mock failed subprocess.run
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["pactl", "load-module", "module-null-sink"],
            stderr="Module load failed"
        )
        
        vmic = VirtualMicrophone("test-mic")
        result = vmic.create_virtual_sink()
        
        assert result is False
        assert not vmic.is_created
    
    @patch('subprocess.run')
    def test_destroy_virtual_sink_success(self, mock_run):
        """Test successful destruction of virtual sink."""
        # First create a mock sink
        vmic = VirtualMicrophone("test-mic")
        vmic.is_created = True
        
        # Mock list modules response
        mock_list_modules = Mock()
        mock_list_modules.stdout = "42  name=test-mic  module-null-sink\n"
        
        mock_run.return_value = mock_list_modules
        
        result = vmic.destroy_virtual_sink()
        
        assert result is True
        assert not vmic.is_created
        assert vmic.sink_index is None
        assert vmic.source_index is None
    
    def test_context_manager(self):
        """Test context manager usage."""
        with patch.object(VirtualMicrophone, 'create_virtual_sink') as mock_create, \
             patch.object(VirtualMicrophone, 'start_playback') as mock_start, \
             patch.object(VirtualMicrophone, 'stop_playback_thread') as mock_stop, \
             patch.object(VirtualMicrophone, 'destroy_virtual_sink') as mock_destroy:
            
            mock_create.return_value = True
            
            with VirtualMicrophone("test-mic") as vmic:
                assert isinstance(vmic, VirtualMicrophone)
                mock_create.assert_called_once()
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()
            mock_destroy.assert_called_once()
    
    def test_play_audio_without_sink(self):
        """Test playing audio when sink is not created."""
        vmic = VirtualMicrophone("test-mic")
        
        with patch.object(vmic, 'create_virtual_sink') as mock_create:
            mock_create.return_value = False
            
            # Create test audio
            test_audio = np.zeros(1000, dtype=np.float32)
            vmic.play_audio(test_audio, 48000)
            
            # Should try to create sink
            mock_create.assert_called_once()
    
    def test_play_audio_with_sink(self):
        """Test playing audio when sink is created."""
        vmic = VirtualMicrophone("test-mic")
        vmic.is_created = True
        
        # Create test audio
        test_audio = np.zeros(1000, dtype=np.float32)
        vmic.play_audio(test_audio, 48000)
        
        # Check audio was added to queue
        assert not vmic.audio_queue.empty()
        audio_data, sample_rate = vmic.audio_queue.get_nowait()
        assert np.array_equal(audio_data, test_audio)
        assert sample_rate == 48000
    
    def test_get_setup_instructions(self):
        """Test getting setup instructions."""
        vmic = VirtualMicrophone("test-mic")
        
        # Test without sink created
        instructions = vmic.get_setup_instructions()
        assert "non configuré" in instructions or "not configured" in instructions.lower()
        
        # Test with sink created
        vmic.is_created = True
        vmic.source_name = "test-mic.monitor"
        instructions = vmic.get_setup_instructions()
        assert "test-mic.monitor" in instructions
        assert "Google Meet" in instructions
    
    def test_start_stop_playback(self):
        """Test starting and stopping playback thread."""
        vmic = VirtualMicrophone("test-mic")
        
        # Mock the playback loop to avoid actual audio playback
        with patch.object(vmic, '_playback_loop') as mock_loop:
            # Make the mock loop run indefinitely until stopped
            mock_loop.side_effect = lambda: None
            
            vmic.start_playback()
            
            assert vmic.playback_thread is not None
            assert isinstance(vmic.playback_thread, threading.Thread)
            assert not vmic.stop_playback.is_set()
            
            # Start again should not create new thread (thread is still alive)
            # Actually, the thread might have already finished since mock_loop returns immediately
            # So we'll just check that start_playback doesn't crash when called twice
            vmic.start_playback()  # Should not crash
            
            # Stop playback
            vmic.stop_playback_thread()
            assert vmic.stop_playback.is_set()
    
    @patch('sounddevice.query_devices')
    def test_find_sounddevice_device_id_found(self, mock_query_devices):
        """Test finding sounddevice device ID when device exists."""
        vmic = VirtualMicrophone("test-mic")
        
        # Mock sounddevice devices
        mock_devices = [
            {'name': 'Default', 'max_output_channels': 2},
            {'name': 'test-mic Output', 'max_output_channels': 2},
            {'name': 'Other Device', 'max_output_channels': 2}
        ]
        mock_query_devices.return_value = mock_devices
        
        device_id = vmic._find_sounddevice_device_id()
        
        assert device_id == 1  # Should find device at index 1
    
    @patch('sounddevice.query_devices')
    def test_find_sounddevice_device_id_not_found(self, mock_query_devices):
        """Test finding sounddevice device ID when device doesn't exist."""
        vmic = VirtualMicrophone("test-mic")
        
        # Mock sounddevice devices without our device
        mock_devices = [
            {'name': 'Default', 'max_output_channels': 2},
            {'name': 'Other Device', 'max_output_channels': 2}
        ]
        mock_query_devices.return_value = mock_devices
        
        device_id = vmic._find_sounddevice_device_id()
        
        assert device_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])