"""
Tests for the VirtualMicrophone class using pulsectl.
"""
import pytest
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
        mock_pulse.module_load.side_effect = [101, 102, 103] # sink, source, loopback
        
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
        with patch.object(vmic, '_refresh_sounddevice') as mock_refresh:
            result = vmic.create_virtual_sink()
        
        assert result is True
        assert vmic.is_created is True
        assert 101 in vmic._module_indices
        assert 102 in vmic._module_indices
        
        # Verify pulsectl calls
        assert mock_pulse.module_load.call_count >= 2
        mock_pulse.sink_mute.assert_called()
        mock_pulse.source_mute.assert_called()

    @patch('pulsectl.Pulse')
    def test_create_virtual_sink_failure(self, mock_pulse_class):
        """Test failed creation of virtual sink."""
        mock_pulse = mock_pulse_class.return_value.__enter__.return_value
        mock_pulse.module_load.side_effect = Exception("Pulse failure")
        
        vmic = VirtualMicrophone("test-mic")
        result = vmic.create_virtual_sink()
        
        assert result is False
        assert not vmic.is_created

    @patch('pulsectl.Pulse')
    def test_destroy_virtual_sink_success(self, mock_pulse_class):
        """Test successful destruction of virtual sink."""
        mock_pulse = mock_pulse_class.return_value.__enter__.return_value
        
        vmic = VirtualMicrophone("test-mic")
        vmic.is_created = True
        vmic._module_indices = [101, 102]
        
        result = vmic.destroy_virtual_sink()
        
        assert result is True
        assert not vmic.is_created
        assert vmic._module_indices == []
        assert mock_pulse.module_unload.call_count == 2

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
        
        # Test without sink created
        instructions = vmic.get_setup_instructions()
        assert "non configuré" in instructions
        
        # Test with sink created
        vmic.is_created = True
        instructions = vmic.get_setup_instructions()
        assert "test-mic" in instructions
        assert "GOOGLE MEET" in instructions.upper()
