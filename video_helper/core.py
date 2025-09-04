import logging
from pathlib import Path
from typing import Optional
from .config import AppConfig
from .downloader import YouTubeDownloader
from .transcriber import WhisperTranscriber
from .exceptions import DownloadError, TranscriptionError

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Orchestrates the process of downloading and transcribing video content.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the VideoProcessor with dependency injection.

        Args:
            config (AppConfig): The application configuration object.
        """
        self._config = config
        self._downloader = YouTubeDownloader(config)
        self._transcriber: Optional[WhisperTranscriber] = None
    
    def _get_transcriber(self) -> WhisperTranscriber:
        """
        Lazily loads the WhisperTranscriber instance.
        This follows a form of the Singleton pattern (for the transcriber instance)
        and ensures the model is only loaded if needed.
        """
        if self._transcriber is None:
            self._transcriber = WhisperTranscriber(self._config)
        return self._transcriber

    def download_video(self, url: str, resolution: str) -> Path:
        """
        Downloads a video at a specified resolution.
        
        Args:
            url (str): The URL of the YouTube video.
            resolution (str): The desired resolution (e.g., '1080p', '720p').
        
        Returns:
            Path: The path to the downloaded video file.
        """
        return self._downloader.download_video(url, resolution)

    def download_audio(self, url: str) -> Path:
        """
        Downloads the audio from a video.
        
        Args:
            url (str): The URL of the YouTube video.
            
        Returns:
            Path: The path to the downloaded audio file.
        """
        return self._downloader.download_audio(url)

    def download_subtitles(self, url: str, language: str) -> Optional[Path]:
        """
        Downloads the subtitles for a video.
        
        Args:
            url (str): The URL of the YouTube video.
            language (str): The desired language code.
            
        Returns:
            Optional[Path]: The path to the subtitles file, or None if not found.
        """
        return self._downloader.download_subtitles(url, language)

    def transcribe_audio(self, audio_path: Path) -> Path:
        """
        Transcribes the audio from a file. If subtitles are available, it uses them;
        otherwise, it performs a full transcription.

        Args:
            audio_path (Path): The path to the audio file.
        
        Returns:
            Path: The path to the transcribed text file.
        
        Raises:
            TranscriptionError: If transcription fails.
        """
        transcriber = self._get_transcriber()
        transcribed_text = transcriber.transcribe_audio(audio_path)

        # Save transcription to a .txt file
        txt_path = audio_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcribed_text)
        
        logger.info(f"📝 [EN] Transcription saved to: {txt_path} - [PT-BR] Transcrição salva em: {txt_path}")
        
        return txt_path