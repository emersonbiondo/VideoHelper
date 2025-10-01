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

class StreamDownloader:
    """
    Handles downloading content (video, audio, subtitles) from various online streams.
    [PT-BR] Lida com o download de conteúdo (vídeo, áudio, legendas) de vários fluxos online.
    Encapsulates all interactions with the yt-dlp library.
    [PT-BR] Encapsula todas as interações com a biblioteca yt-dlp.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the StreamDownloader with application settings.
        [PT-BR] Inicializa o StreamDownloader com as configurações da aplicação.

        Args:
            config (AppConfig): The application configuration object.
            [PT-BR] O objeto de configuração da aplicação.
        """
        self._config = config
        self._output_path_template = str(self._config.results_folder / '%(title)s.%(ext)s')

    def _get_base_ydl_opts(self) -> dict:
        """
        Generates the base yt-dlp options dictionary, including cookies if configured.
        [PT-BR] Gera o dicionário base de opções do yt-dlp, incluindo cookies se configurado.
        """
        base_opts = {
            'outtmpl': self._output_path_template,
            'quiet': not self._config.show_progress,
            'progress_hooks': [],
        }

        # Adiciona o arquivo de cookies se o caminho estiver configurado e o arquivo existir
        # [PT-BR] Adds the cookies file if the path is configured and the file exists
        if self._config.cookies_file_path and self._config.cookies_file_path.exists():
            base_opts['cookiefile'] = str(self._config.cookies_file_path)
            logger.info(f"🍪 [EN] Using cookies from: {self._config.cookies_file_path} - [PT-BR] Usando cookies de: {self._config.cookies_file_path}")
        else:
            logger.warning("⚠️ [EN] Cookies file not configured or not found. Downloads might be restricted. - [PT-BR] Arquivo de cookies não configurado ou não encontrado. Downloads podem ser restritos.")

        return base_opts

    def _progress_hook(self, d, progress_bar, task_id):
        """
        A progress hook to update the Rich progress bar.
        [PT-BR] Um hook de progresso para atualizar a barra de progresso do Rich.
        """
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes')
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if downloaded and total:
                progress_bar.update(task_id, completed=downloaded, total=total)
        elif d['status'] == 'finished':
            progress_bar.update(task_id, completed=d['total_bytes'])

    def download_video(self, url: str, resolution: str) -> Path:
        """
        Downloads a video from a given URL with a specific resolution.
        [PT-BR] Baixa um vídeo de uma URL dada com uma resolução específica.
        """
        ydl_opts = self._get_base_ydl_opts()
        
        # Adiciona opções específicas para o download de vídeo
        ydl_opts.update({
            'format': f'bestvideo[height<=?{resolution[:-1]}]+bestaudio/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        })

        def file_path_hook(d):
            nonlocal final_filepath
            if d['status'] == 'finished' and 'filepath' in d['info_dict']:
                final_filepath = Path(d['info_dict']['filepath'])
        
        final_filepath = None
        ydl_opts['progress_hooks'].append(file_path_hook)

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
                    task = progress.add_task(f"[EN] Downloading video at {resolution}... - [PT-BR] Baixando vídeo na resolução {resolution}...", total=None)
                    ydl_opts['progress_hooks'].append(lambda d: self._progress_hook(d, progress, task))
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            
            # Tenta obter o caminho final do arquivo de forma segura após o download/pós-processamento
            if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                final_filepath = Path(info['requested_downloads'][0]['filepath'])

            if not final_filepath or not final_filepath.exists():
                raise DownloadError("[EN] Video file path not found after download. - [PT-BR] Caminho do arquivo de vídeo não encontrado após o download.")
            
            logger.info(f"✅ [EN] Video downloaded successfully to: {final_filepath} - [PT-BR] Vídeo baixado com sucesso para: {final_filepath}")
            return final_filepath

        except Exception as e:
            raise DownloadError(f"[EN] Failed to download video: {e} - [PT-BR] Falha ao baixar vídeo: {e}") from e

    def download_audio(self, url: str) -> Path:
        """
        Downloads the audio stream from a video URL.
        [PT-BR] Baixa o fluxo de áudio de uma URL de vídeo.
        """
        ydl_opts = self._get_base_ydl_opts()

        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self._config.audio_quality,
            }],
        })

        def file_path_hook(d):
            nonlocal final_filepath
            if d['status'] == 'finished' and 'filepath' in d['info_dict']:
                final_filepath = Path(d['info_dict']['filepath'])

        final_filepath = None
        ydl_opts['progress_hooks'].append(file_path_hook)

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
                    task = progress.add_task("[EN] Downloading audio... - [PT-BR] Baixando áudio...", total=None)
                    ydl_opts['progress_hooks'].append(lambda d: self._progress_hook(d, progress, task))
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

            if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                final_filepath = Path(info['requested_downloads'][0]['filepath'])

            if not final_filepath or not final_filepath.exists():
                raise DownloadError("[EN] Audio file path not found after download. - [PT-BR] Caminho do arquivo de áudio não encontrado após o download.")
            
            logger.info(f"✅ [EN] Audio downloaded successfully to: {final_filepath} - [PT-BR] Áudio baixado com sucesso para: {final_filepath}")
            return final_filepath

        except Exception as e:
            raise DownloadError(f"[EN] Failed to download audio: {e} - [PT-BR] Falha ao baixar áudio: {e}") from e

    def download_subtitles(self, url: str, language: str) -> Optional[Path]:
        """
        Downloads the subtitles for a video URL in a specific language.
        [PT-BR] Baixa as legendas para uma URL de vídeo em um idioma específico.
        """
        ydl_opts = self._get_base_ydl_opts()

        ydl_opts.update({
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [language],
            'subtitlesformat': 'vtt',
            'quiet': True, # Overrides base quiet setting, as subtitles download is fast and simple
        })

        logger.info(f"🟡 [EN] Attempting to download subtitles for URL: {url} in '{language}' - [PT-BR] Tentando baixar legendas para a URL: {url} em '{language}'")

        subtitles_path = None
        def hook(d):
            nonlocal subtitles_path
            if d['status'] == 'finished' and d.get('info_dict', {}).get('ext') == 'vtt':
                subtitles_path = Path(d['filename'])

        ydl_opts['progress_hooks'].append(hook)

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