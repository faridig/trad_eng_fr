import os
import pytest
from poc_audio import find_devices, record_simultaneous

def test_devices_found():
    """Vérifie que les périphériques requis sont détectés."""
    micro, system = find_devices()
    assert micro is not None, "Microphone non trouvé"
    assert system is not None, "Loopback système non trouvé"

def test_recordings_integrity():
    """Vérifie la création et l'intégrité (taille > 0) des fichiers audio."""
    micro, system = find_devices()
    if not micro or not system:
        pytest.skip("Périphériques audio non disponibles pour le test d'enregistrement")
        
    # Nettoyage préalable
    for f in ["test_micro.wav", "test_system.wav"]:
        if os.path.exists(f): os.remove(f)
    
    # Exécution de l'enregistrement (1s pour le test)
    record_simultaneous(micro, system, duration=1)
    
    # Assertions sur les fichiers produits
    for f in ["test_micro.wav", "test_system.wav"]:
        assert os.path.exists(f), f"Le fichier {f} n'a pas été créé"
        assert os.path.getsize(f) > 1000, f"Le fichier {f} est vide ou trop petit"
