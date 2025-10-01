import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Define o caminho para o arquivo de configuração
# [PT-BR] Define o caminho para o arquivo de configuração
CONFIG_FILE_PATH = Path("./config.json")

@dataclass
class AppConfig:
    """
    Application configuration settings.
    [PT-BR] Configurações da aplicação.
    """
    results_folder: Path
    subtitle_language: str
    transcription_language: str
    default_video_resolution: str
    whisper_model: str
    audio_quality: str
    show_progress: bool
    cookies_file_path: Optional[Path] = None

def load_config() -> AppConfig:
    # ... (código de load_config mantido, mas com a lógica de Path/None para cookies)
    # A lógica de carregamento precisa garantir que 'null' no JSON se torne None em Python
    if not CONFIG_FILE_PATH.exists():
        raise FileNotFoundError(f"[EN] Configuration file not found at: {CONFIG_FILE_PATH} - [PT-BR] Arquivo de configuração não encontrado em: {CONFIG_FILE_PATH}")
    
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Converte o caminho para um objeto Path
        config_data['results_folder'] = Path(config_data.get("results_folder", "./results"))
        
        # Trata o campo de cookies (converte string para Path ou mantém None/null)
        cookies_path_str = config_data.get("cookies_file_path")
        if cookies_path_str and cookies_path_str.strip().lower() != "null":
             config_data['cookies_file_path'] = Path(cookies_path_str)
        else:
             config_data['cookies_file_path'] = None

        config_data['results_folder'].mkdir(parents=True, exist_ok=True)
        
        return AppConfig(**config_data)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"[EN] Invalid JSON in configuration file: {e} - [PT-BR] JSON inválido no arquivo de configuração: {e}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"[EN] Failed to load application configuration: {e} - [PT-BR] Falha ao carregar a configuração da aplicação: {e}")

settings = load_config()