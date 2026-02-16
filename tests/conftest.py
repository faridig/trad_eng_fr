"""
Configuration des tests pytest.
"""
import os
import pytest

# Décorateur pour skip les tests audio en CI
def skip_if_ci(reason="Test nécessite un environnement avec audio"):
    """Décorateur pour skip les tests qui nécessitent audio en CI."""
    def decorator(func):
        return pytest.mark.skipif(
            os.environ.get('CI') == 'true',
            reason=f"{reason} (environnement CI détecté)"
        )(func)
    return decorator

# Décorateur pour skip si PulseAudio n'est pas disponible
def skip_if_no_pulseaudio(reason="Test nécessite PulseAudio"):
    """Décorateur pour skip les tests qui nécessitent PulseAudio."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                import pulsectl
                with pulsectl.Pulse('test-connection', connect=False) as pulse:
                    # Essayer de se connecter
                    pulse.connect()
                    if not pulse.connected:
                        pytest.skip(f"{reason}: PulseAudio non connecté")
            except Exception:
                pytest.skip(f"{reason}: PulseAudio non disponible")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Fixture pour détecter l'environnement CI
@pytest.fixture
def is_ci():
    """Retourne True si on est en environnement CI."""
    return os.environ.get('CI') == 'true'