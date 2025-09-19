import argparse
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

from video_helper.config import load_config
from video_helper.core import VideoProcessor
from video_helper.exceptions import DownloadError, TranscriptionError

# Configure basic logging to the console
# [PT-BR] Configura o logging básico para o console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def get_input_path(input_arg: str, processor: VideoProcessor) -> Optional[Path]:
    """
    Determines if the input is a URL or a local file and handles accordingly.
    [PT-BR] Determina se a entrada é uma URL ou um arquivo local e lida com isso.
    
    Args:
        input_arg (str): The input string (URL or file path).
        processor (VideoProcessor): The VideoProcessor instance.
    
    Returns:
        Optional[Path]: Path to the local file, or None if the input is a URL.
    """
    try:
        input_path = Path(input_arg)
        if input_path.exists():
            return input_path
    except:
        pass  # It's not a valid local path, so we assume it's a URL.
    return None

def process_single_input(action_func: Callable, input_arg: str, processor: VideoProcessor, **kwargs):
    """
    Handles a single input (URL or local file) for a given action.
    [PT-BR] Lida com uma única entrada (URL ou arquivo local) para uma dada ação.
    
    Args:
        action_func (Callable): The function to execute (e.g., download_video, transcribe).
        input_arg (str): The input string.
        processor (VideoProcessor): The VideoProcessor instance.
        **kwargs: Additional arguments for the action function.
    """
    logger.info(f"⚙️ [EN] Processing input: {input_arg} - [PT-BR] Processando entrada: {input_arg}")
    
    local_path = get_input_path(input_arg, processor)
    
    try:
        if local_path:
            logger.info(f"📁 [EN] Input identified as local file. - [PT-BR] Entrada identificada como arquivo local.")
            action_func(local_path, **kwargs)
        else:
            logger.info(f"🔗 [EN] Input identified as URL. - [PT-BR] Entrada identificada como URL.")
            action_func(input_arg, **kwargs)
        
        logger.info(f"✅ [EN] Processing finished for: {input_arg} - [PT-BR] Processamento concluído para: {input_arg}")

    except (DownloadError, TranscriptionError, FileNotFoundError) as e:
        logger.error(f"❌ [EN] An error occurred while processing '{input_arg}': {e} - [PT-BR] Um erro ocorreu ao processar '{input_arg}': {e}")
        # We do not re-raise the error here so that the 'auto' command can continue
        # [PT-BR] Não relançamos o erro aqui para que o comando 'auto' possa continuar

def main():
    """Main function to run the CLI application."""
    config = load_config()
    processor = VideoProcessor(config)

    parser = argparse.ArgumentParser(description="Video and audio processing tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ----- `video` command -----
    video_parser = subparsers.add_parser("video", help="Downloads a video from a URL.")
    video_parser.add_argument("input", help="URL of the video to download.")
    video_parser.add_argument("--resolution", default=config.default_video_resolution, help="Video resolution (e.g., '1080p').")

    # ----- `audio` command -----
    audio_parser = subparsers.add_parser("audio", help="Downloads audio from a URL or extracts it from a local video file.")
    audio_parser.add_argument("input", help="URL of the video or path to the local video file.")
    
    # ----- `subtitles` command -----
    subtitles_parser = subparsers.add_parser("subtitles", help="Downloads subtitles from a URL.")
    subtitles_parser.add_argument("input", help="URL of the video.")
    subtitles_parser.add_argument("--language", default=config.subtitle_language, help="Subtitle language (e.g., 'pt').")
    
    # ----- `transcribe` command -----
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribes audio from a URL or local file to a text (.txt) file.")
    transcribe_parser.add_argument("input", help="URL of the video or path to the audio file.")

    # ----- `srt` command -----
    srt_parser = subparsers.add_parser("srt", help="Generates an SRT file from a URL or local file, or converts a VTT file to SRT.")
    srt_parser.add_argument("input", help="URL of the video, path to a local audio/video file, or path to a VTT subtitle file.")

    # ----- `auto` command -----
    auto_parser = subparsers.add_parser("auto", help="Executes multiple commands from a text file.")
    auto_parser.add_argument("file_path", help="Path to the text file containing commands.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Use a dictionary to map commands to their respective functions and arguments
        # [PT-BR] Usa um dicionário para mapear comandos às suas funções e argumentos
        handlers = {
            "video": lambda: processor.download_video(args.input, args.resolution),
            "audio": lambda: (
                processor.download_audio(args.input) if not get_input_path(args.input, processor)
                else processor.extract_audio_from_local_file(get_input_path(args.input, processor))
            ),
            "subtitles": lambda: processor.download_subtitles(args.input, args.language),
            "transcribe": lambda: (
                processor.transcribe(processor.download_audio(args.input)) if not get_input_path(args.input, processor)
                else processor.transcribe(get_input_path(args.input, processor))
            ),
            "srt": lambda: (
                processor.convert_vtt_to_srt(get_input_path(args.input, processor)) if str(get_input_path(args.input, processor)).endswith(".vtt")
                else (
                    processor.generate_srt(processor.download_audio(args.input)) if not get_input_path(args.input, processor)
                    else processor.generate_srt(get_input_path(args.input, processor))
                )
            ),
            "auto": lambda: process_auto_file(args.file_path, processor)
        }
        
        # We process the 'auto' command differently since it needs to read a file
        # [PT-BR] Processamos o comando 'auto' de forma diferente, já que ele precisa ler um arquivo
        if args.command in handlers:
            if args.command != "auto":
                handlers[args.command]()
            else:
                process_auto_file(args.file_path, processor)
        
    except (DownloadError, TranscriptionError, FileNotFoundError) as e:
        logger.error(f"❌ [EN] An error occurred: {e} - [PT-BR] Um erro ocorreu: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ [EN] An unexpected error occurred: {e} - [PT-BR] Um erro inesperado ocorreu: {e}")
        sys.exit(1)

def process_auto_file(file_path: str, processor: VideoProcessor):
    """
    Reads a file with commands and executes them in sequence.
    [PT-BR] Lê um arquivo com comandos e os executa em sequência.
    """
    logger.info(f"📝 [EN] Starting batch processing from file: {file_path} - [PT-BR] Iniciando processamento em lote a partir do arquivo: {file_path}")
    
    auto_file_path = Path(file_path)
    if not auto_file_path.exists():
        raise FileNotFoundError(f"[EN] File not found: {file_path} - [PT-BR] Arquivo não encontrado: {file_path}")
    
    with open(auto_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            command = parts[0]
            input_arg = parts[1]
            extra_args = parts[2:]
            
            # Map command strings to a simple function handler
            # [PT-BR] Mapeia strings de comando para um manipulador de função simples
            handlers = {
                "video": lambda i: processor.download_video(i, extra_args[1] if len(extra_args) > 1 else processor._config.default_video_resolution),
                "audio": lambda i: (
                    processor.download_audio(i) if not get_input_path(i, processor)
                    else processor.extract_audio_from_local_file(get_input_path(i, processor))
                ),
                "subtitles": lambda i: processor.download_subtitles(i, extra_args[1] if len(extra_args) > 1 else processor._config.subtitle_language),
                "transcribe": lambda i: (
                    processor.transcribe(processor.download_audio(i)) if not get_input_path(i, processor)
                    else processor.transcribe(get_input_path(i, processor))
                ),
                "srt": lambda i: (
                    processor.convert_vtt_to_srt(get_input_path(i, processor)) if str(get_input_path(i, processor)).endswith(".vtt")
                    else (
                        processor.generate_srt(processor.download_audio(i)) if not get_input_path(i, processor)
                        else processor.generate_srt(get_input_path(i, processor))
                    )
                ),
            }

            if command in handlers:
                logger.info(f"▶️ [EN] Executing command '{command}' for '{input_arg}'... - [PT-BR] Executando comando '{command}' para '{input_arg}'...")
                handlers[command](input_arg)
            else:
                logger.warning(f"⚠️ [EN] Skipping unknown command on line {line_num}: '{command}' - [PT-BR] Ignorando comando desconhecido na linha {line_num}: '{command}'")

if __name__ == "__main__":
    main()