"""
Tests for the VirtualMicrophone class using pulsectl and pactl.
"""
import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import threading
import queue

from src.core.virtual_mic import VirtualMicrophone


class TestVirtualMicrophone:
    """Test suite for VirtualMicrophone class."""
    
    def test_initialization(self):
        """Test that VirtualMicrophone initializes correctly."""
        vmic = VirtualMicrophone("test-mic")
        
        assert vmic.sink_name == "test-mic"
        assert vmic.source_name == "test-mic"
        assert vmic.output_sink_name == "test-mic-output"
        assert not vmic.is_created
        assert vmic.sample_rate == 48000
        assert isinstance(vmic.audio_queue, queue.Queue)
        assert vmic.playback_thread is None
        assert not vmic.stop_playback.is_set()
    
    @patch('pulsectl.Pulse')
    @patch('sounddevice._terminate')
    @patch('sounddevice._initialize')
    def test_create_virtual_sink_success(self, mock_sd_init, mock_sd_term, mock_pulse_class):
        """Test successful creation of virtual sink with pulsectl."""
        # Setup mock Pulse client
        mock_pulse = mock_pulse_class.return_value.__enter__.return_value
        mock_pulse.module_load.side_effect = [101, 102]
        
        # Mock sink and source lists for volume setting
        mock_sink = Mock()
        mock_sink.name = "test-mic-output"
        mock_sink.index = 1
        mock_pulse.sink_list.return_value = [mock_sink]
        
        mock_source = Mock()
        mock_source.name = "test-mic"
        mock_source.index = 2
        mock_pulse.source_list.return_value = [mock_source]
        
        vmic = VirtualMicrophone("test-mic")
        with patch.object(vmic, 'destroy_virtual_sink'):
            result = vmic.create_virtual_sink()
        
        assert result is True
        assert vmic.is_created is True
        
        # Verify pulsectl calls
        assert mock_pulse.module_load.call_count >= 2

    @patch('pulsectl.Pulse')
    @patch('src.core.virtual_mic.subprocess.run')
    def test_destroy_virtual_sink_success(self, mock_run, mock_pulse_class):
        """Test successful destruction of virtual sink (Aggressive cleaning)."""
        vmic = VirtualMicrophone("test-mic")
        vmic.is_created = True
        
        # Mock pactl list modules short
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "42  module-null-sink  sink_name=vox-test\n99  module-remap-source  source_name=vox-mic"
        mock_run.side_effect = [mock_result, Mock(), Mock()] # list, unload 42, unload 99
        
        result = vmic.destroy_virtual_sink()
        
        assert result is True
        assert not vmic.is_created
        assert mock_run.call_count >= 1

    @patch('sounddevice.query_devices')
    def test_find_sounddevice_device_id_found(self, mock_query_devices):
        """Test finding sounddevice device ID when device exists."""
        vmic = VirtualMicrophone("test-mic")
        
        mock_devices = [
            {'name': 'Default', 'max_output_channels': 2},
            {'name': 'test-mic-output', 'max_output_channels': 2},
            {'name': 'Other Device', 'max_output_channels': 2}
        ]
        mock_query_devices.return_value = mock_devices
        
        device_id = vmic._find_sounddevice_device_id()
        assert device_id == 1

    def test_get_setup_instructions(self):
        """Test getting setup instructions."""
        vmic = VirtualMicrophone("test-mic")
        
        # Test basic
        instructions = vmic.get_setup_instructions()
        assert "test-mic" in instructions
        assert "Google Meet" in instructions

    @patch('src.core.virtual_mic.subprocess.run')
    @patch('os.getpid')
    def test_force_redirect_stream(self, mock_getpid, mock_run):
        """Test the brute force redirection logic."""
        mock_getpid.return_value = 1234
        vmic = VirtualMicrophone("test-mic")
        
        # Mock pactl list sink-inputs
        mock_list = Mock()
        mock_list.returncode = 0
        mock_list.stdout = """Entrée de la destination #500
        application.process.id = "1234"
        """
        mock_run.side_effect = [mock_list, Mock()] # list, then move
        
        vmic._force_redirect_stream()
        
        # Verify move-sink-input was called with ID 500
        move_call = mock_run.call_args_list[1]
        assert "move-sink-input" in move_call[0][0]
        assert "500" in move_call[0][0]
        assert vmic.output_sink_name in move_call[0][0]
