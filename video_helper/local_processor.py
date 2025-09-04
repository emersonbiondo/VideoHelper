import logging
from pathlib import Path
import ffmpeg
from .config import AppConfig
from .exceptions import DownloadError, TranscriptionError

logger = logging.getLogger(__name__)

class LocalFileProcessor:
    """
    Handles processing of local video files.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the processor with application settings.

        Args:
            config (AppConfig): The application configuration object.
        """
        self._config = config
    
    def extract_audio(self, file_path: Path) -> Path:
        """
        Extracts audio from a local video file and saves it as an MP3.

        Args:
            file_path (Path): The path to the local video file.

        Returns:
            Path: The path to the extracted audio file.
        
        Raises:
            DownloadError: If the file is not found or extraction fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"[EN] Local video file not found at: {file_path} - [PT-BR] Arquivo de vídeo local não encontrado em: {file_path}")

        try:
            self._config.results_folder.mkdir(parents=True, exist_ok=True)
            output_path = self._config.results_folder / f"{file_path.stem}.mp3"
            
            logger.info(f"🟡 [EN] Starting audio extraction from local file: {file_path.name} - [PT-BR] Iniciando extração de áudio do arquivo local: {file_path.name}")
            
            (
                ffmpeg
                .input(str(file_path))
                .output(str(output_path), acodec='libmp3lame', audio_bitrate=self._config.audio_quality)
                .run() # <--- Opções de captura removidas
            )

            if not output_path.exists():
                raise DownloadError(f"[EN] Extracted audio file not found at: {output_path} - [PT-BR] Arquivo de áudio extraído não encontrado em: {output_path}")

            logger.info(f"✅ [EN] Audio extracted successfully to: {output_path} - [PT-BR] Áudio extraído com sucesso para: {output_path}")
            return output_path
        
        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf8') if e.stderr else ""
            raise DownloadError(f"[EN] FFmpeg error during audio extraction: {error_message} - [PT-BR] Erro do FFmpeg durante a extração de áudio: {error_message}")
        except Exception as e:
            raise DownloadError(f"[EN] An unexpected error occurred during audio extraction: {e} - [PT-BR] Ocorreu um erro inesperado durante a extração de áudio: {e}")