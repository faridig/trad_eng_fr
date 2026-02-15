import os
import ctranslate2
import transformers
from typing import Literal

class Translator:
    """
    Traducteur utilisant MarianMT via CTranslate2 pour une performance optimale.
    """
    MODELS = {
        ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
        ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    }

    def __init__(self, device="auto", model_dir="models/translate"):
        self.device = device
        self.model_dir = model_dir
        self.translators = {}
        self.tokenizers = {}
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _get_model_paths(self, source_lang: str, target_lang: str):
        model_name = self.MODELS.get((source_lang, target_lang))
        if not model_name:
            raise ValueError(f"Traduction de {source_lang} vers {target_lang} non supportée.")
        
        safe_name = model_name.replace("/", "_")
        ct2_model_path = os.path.join(self.model_dir, f"{safe_name}_ct2")
        return model_name, ct2_model_path

    def _load_model(self, source_lang: str, target_lang: str):
        key = (source_lang, target_lang)
        if key in self.translators:
            return

        model_name, ct2_model_path = self._get_model_paths(source_lang, target_lang)

        # Vérifier si le modèle converti existe
        if not os.path.exists(ct2_model_path):
            self._convert_model(model_name, ct2_model_path)

        # Charger le traducteur CTranslate2
        self.translators[key] = ctranslate2.Translator(ct2_model_path, device=self.device)
        
        # Charger le tokenizer (Transformers)
        self.tokenizers[key] = transformers.AutoTokenizer.from_pretrained(model_name)

    def _convert_model(self, model_name: str, output_dir: str):
        """Convertit un modèle MarianMT vers le format CTranslate2."""
        print(f"Conversion du modèle {model_name} vers {output_dir}...")
        converter = ctranslate2.converters.TransformersConverter(model_name)
        converter.convert(output_dir, force=True)

    def translate(self, text: str, source_lang: Literal["fr", "en"], target_lang: Literal["fr", "en"]) -> str:
        """
        Traduit le texte source vers la langue cible.
        """
        if not text.strip():
            return ""

        self._load_model(source_lang, target_lang)
        key = (source_lang, target_lang)
        
        tokenizer = self.tokenizers[key]
        translator = self.translators[key]

        # Tokenization
        source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        
        # Inférence
        results = translator.translate_batch([source_tokens])
        target_tokens = results[0].hypotheses[0]
        
        # Detokenization
        translation = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens), skip_special_tokens=True)
        return translation
