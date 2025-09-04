import logging
from pathlib import Path
from typing import Optional
from yt_dlp import YoutubeDL
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
from .config import AppConfig
from .exceptions import DownloadError

logger = logging.getLogger(__name__)
console = Console()

class YouTubeDownloader:
    """
    Handles downloading subtitles, audio, and video from YouTube videos.
    Encapsulates all interactions with the yt-dlp library.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the YouTubeDownloader with application settings.

        Args:
            config (AppConfig): The application configuration object.
        """
        self._config = config
        self._output_path_template = str(self._config.results_folder / '%(title)s.%(ext)s')

    def _progress_hook(self, d, progress_bar, task_id):
        """
        A progress hook to update the Rich progress bar.
        
        Args:
            d (dict): The progress dictionary from yt-dlp.
            progress_bar (Progress): The Rich Progress object.
            task_id (object): The task ID for the progress bar.
        """
        if d['status'] == 'downloading':
            # `downloaded_bytes` and `total_bytes` are not always available
            downloaded = d.get('downloaded_bytes')
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if downloaded and total:
                progress_bar.update(task_id, completed=downloaded, total=total)
        elif d['status'] == 'finished':
            progress_bar.update(task_id, completed=d['total_bytes'])

    def download_video(self, url: str, resolution: str) -> Path:
        """
        Downloads a video at a specific resolution.
        
        Args:
            url (str): The URL of the YouTube video.
            resolution (str): The desired resolution (e.g., '1080p', '720p', '480p').
            
        Returns:
            Path: The path to the downloaded video file.
            
        Raises:
            DownloadError: If the download fails or the requested resolution is not found.
        """
        ydl_opts = {
            'format': f'bestvideo[ext=mp4][height={resolution[:-1]}]+bestaudio[ext=m4a]/best',
            'outtmpl': self._output_path_template,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
            'quiet': not self._config.show_progress,
        }

        try:
            self._config.results_folder.mkdir(exist_ok=True)
            if self._config.show_progress:
                with Progress(
                    TextColumn("[EN] Downloading... [PT-BR] Baixando..."),
                    BarColumn(),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task(f"[EN] Downloading video at {resolution}...", total=None)
                    ydl_opts['progress_hooks'] = [lambda d: self._progress_hook(d, progress, task)]
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            
            final_filepath = Path(info['requested_downloads'][0]['filepath'])
            
            if not final_filepath.exists():
                raise DownloadError("[EN] Video file path not found after download. - [PT-BR] Caminho do arquivo de vídeo não encontrado após o download.")
            
            logger.info(f"✅ [EN] Video downloaded successfully to: {final_filepath} - [PT-BR] Vídeo baixado com sucesso para: {final_filepath}")
            return final_filepath

        except Exception as e:
            raise DownloadError(f"[EN] Failed to download video: {e} - [PT-BR] Falha ao baixar vídeo: {e}") from e

    def download_audio(self, url: str) -> Path:
        """
        Downloads the best quality audio from a YouTube URL and converts it to MP3.
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': self._output_path_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self._config.audio_quality,
            }],
            'quiet': not self._config.show_progress,
        }

        try:
            self._config.results_folder.mkdir(exist_ok=True)
            if self._config.show_progress:
                with Progress(
                    TextColumn("[EN] Downloading... [PT-BR] Baixando..."),
                    BarColumn(),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[EN] Downloading audio...", total=None)
                    ydl_opts['progress_hooks'] = [lambda d: self._progress_hook(d, progress, task)]
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

            final_filepath = Path(info['requested_downloads'][0]['filepath'])
            
            if not final_filepath.exists():
                raise DownloadError("[EN] Audio file path not found after download. - [PT-BR] Caminho do arquivo de áudio não encontrado após o download.")
            
            logger.info(f"✅ [EN] Audio downloaded successfully to: {final_filepath} - [PT-BR] Áudio baixado com sucesso para: {final_filepath}")
            return final_filepath

        except Exception as e:
            raise DownloadError(f"[EN] Failed to download audio: {e} - [PT-BR] Falha ao baixar áudio: {e}") from e

    def download_subtitles(self, url: str, language: str) -> Optional[Path]:
        """
        Attempts to download official or automatic subtitles for a given URL.
        """
        logger.info(f"🟡 [EN] Attempting to download subtitles for URL: {url} in '{language}' - [PT-BR] Tentando baixar legendas para a URL: {url} em '{language}'")

        subtitles_path = None
        def hook(d):
            nonlocal subtitles_path
            if d['status'] == 'finished' and d.get('info_dict', {}).get('ext') == 'vtt':
                subtitles_path = Path(d['filename'])

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [language],
            'subtitlesformat': 'vtt',
            'outtmpl': self._output_path_template,
            'progress_hooks': [hook],
            'quiet': True,
        }

        try:
            self._config.results_folder.mkdir(exist_ok=True)
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if subtitles_path and subtitles_path.exists():
                logger.info(f"✅ [EN] Subtitles downloaded successfully to: {subtitles_path} - [PT-BR] Legendas baixadas com sucesso para: {subtitles_path}")
                return subtitles_path
            else:
                logger.warning(f"⚠️ [EN] No subtitles found for language '{language}'. - [PT-BR] Nenhuma legenda encontrada para o idioma '{language}'.")
                return None

        except Exception as e:
            raise DownloadError(f"[EN] Failed to download subtitles: {e} - [PT-BR] Falha ao baixar legendas: {e}") from e