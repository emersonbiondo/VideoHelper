import logging
from pathlib import Path
from typing import Optional

from .config import AppConfig
from .stream_downloader import StreamDownloader
from .local_processor import LocalFileProcessor
from .transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    A facade or orchestrator class that simplifies interactions with various
    components of the application (downloaders, local file processors, transcribers).
    [PT-BR] Uma classe de fachada ou orquestradora que simplifica interações com vários
    componentes da aplicação (baixadores, processadores de arquivos locais, transcribers).
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the processor with application settings and creates
        instances of the dependent services.
        [PT-BR] Inicializa o processador com as configurações da aplicação e cria
        instâncias dos serviços dependentes.

        Args:
            config (AppConfig): The application configuration object.
            [PT-BR] O objeto de configuração da aplicação.
        """
        self._config = config
        self._downloader = StreamDownloader(config)
        self._local_processor = LocalFileProcessor(config)
        self._transcriber = WhisperTranscriber(config)

    def download_video(self, url: str, resolution: str) -> Path:
        """
        Downloads a video from a given URL with a specific resolution.
        [PT-BR] Baixa um vídeo de uma URL dada com uma resolução específica.
        """
        return self._downloader.download_video(url, resolution)

    def download_audio(self, url: str) -> Path:
        """
        Downloads the audio stream from a video URL.
        [PT-BR] Baixa o fluxo de áudio de uma URL de vídeo.
        """
        return self._downloader.download_audio(url)

    def download_subtitles(self, url: str, language: str) -> Optional[Path]:
        """
        Downloads the subtitles for a video URL in a specific language.
        [PT-BR] Baixa as legendas para uma URL de vídeo em um idioma específico.
        """
        return self._downloader.download_subtitles(url, language)

    def extract_audio_from_local_file(self, file_path: Path) -> Path:
        """
        Extracts audio from a local video file.
        [PT-BR] Extrai áudio de um arquivo de vídeo local.
        """
        return self._local_processor.extract_audio(file_path)
    
    def transcribe(self, audio_path: Path) -> str:
        """
        Transcribes the given audio file using Whisper.
        [PT-BR] Transcreve o arquivo de áudio fornecido usando o Whisper.
        """
        return self._transcriber.transcribe_audio(audio_path)

    def generate_srt(self, audio_path: Path) -> Path:
        """
        Generates an SRT file from an audio file.
        [PT-BR] Gera um arquivo SRT a partir de um arquivo de áudio.
        """
        return self._transcriber.generate_srt_from_audio(audio_path)
    
    def convert_vtt_to_srt(self, vtt_path: Path) -> Path:
        """
        Converts a VTT subtitle file to SRT format.
        [PT-BR] Converte um arquivo de legenda VTT para o formato SRT.
        """
        return self._transcriber.convert_vtt_to_srt(vtt_path)