import pulsectl
import pytest
from tests.conftest import skip_if_ci, skip_if_no_pulseaudio

@skip_if_ci("Test nécessite un environnement avec PulseAudio")
@skip_if_no_pulseaudio("Test nécessite PulseAudio")
def test_pulse_connection():
    """Vérifie que pulsectl peut se connecter au serveur audio."""
    try:
        with pulsectl.Pulse('test-connection') as pulse:
            assert pulse.connected is True
    except Exception as e:
        pytest.fail(f"Could not connect to PulseAudio/PipeWire: {e}")

@skip_if_ci("Test nécessite un environnement avec PulseAudio")
@skip_if_no_pulseaudio("Test nécessite PulseAudio")
def test_sources_available():
    """Vérifie qu'au moins une source audio est détectée."""
    with pulsectl.Pulse('test-sources') as pulse:
        sources = pulse.source_list()
        assert len(sources) > 0
