import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Define o caminho para o arquivo de configuração
# Define the path to the configuration file
CONFIG_FILE_PATH = Path("./config.json")

@dataclass
class AppConfig:
    """
    Application configuration settings.
    Stores application-wide settings in a simple dataclass.
    """
    results_folder: Path
    subtitle_language: str
    transcription_language: str
    default_video_resolution: str
    whisper_model: str
    audio_quality: str
    show_progress: bool # <-- Novo campo

def load_config() -> AppConfig:
    """
    Loads configuration from the config.json file.

    Returns:
        AppConfig: The application configuration object.
    
    Raises:
        FileNotFoundError: If the config.json file is not found.
        json.JSONDecodeError: If the config.json file is invalid.
    """
    if not CONFIG_FILE_PATH.exists():
        raise FileNotFoundError(f"[EN] Configuration file not found at: {CONFIG_FILE_PATH} - [PT-BR] Arquivo de configuração não encontrado em: {CONFIG_FILE_PATH}")
    
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Converte o caminho para um objeto Path
        # Convert the path to a Path object
        config_data['results_folder'] = Path(config_data.get("results_folder", "./results"))
        
        # Garante que o diretório de resultados existe
        # Ensure the results folder exists
        config_data['results_folder'].mkdir(parents=True, exist_ok=True)
        
        return AppConfig(**config_data)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"[EN] Invalid JSON in configuration file: {e} - [PT-BR] JSON inválido no arquivo de configuração: {e}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"[EN] Failed to load application configuration: {e} - [PT-BR] Falha ao carregar a configuração da aplicação: {e}")

# Instancia a configuração ao carregar o módulo
# Instantiate the configuration upon module loading
settings = load_config()