import pytest
import os
from src.core.translator import Translator

@pytest.fixture
def translator():
    return Translator(device="cpu")  # CPU pour les tests CI/CD

@pytest.mark.skipif(os.environ.get('CI') == 'true', reason="Skip heavy model loading in CI")
def test_translation_fr_to_en(translator):
    text = "Bonjour, comment ça va ?"
    translation = translator.translate(text, source_lang="fr", target_lang="en")
    assert "hello" in translation.lower() or "how are you" in translation.lower()

@pytest.mark.skipif(os.environ.get('CI') == 'true', reason="Skip heavy model loading in CI")
def test_translation_en_to_fr(translator):
    text = "Hello, how are you?"
    translation = translator.translate(text, source_lang="en", target_lang="fr")
    assert "bonjour" in translation.lower() or "comment allez-vous" in translation.lower()
