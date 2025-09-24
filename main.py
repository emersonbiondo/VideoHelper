import argparse
import logging
import sys
from pathlib import Path
from typing import Callable, Optional
import shlex

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

def get_input_path(input_arg: str) -> Optional[Path]:
    """
    Determines if the input is a local file.
    [PT-BR] Determina se a entrada é um arquivo local.
    
    Args:
        input_arg (str): The input string (URL or file path).
    
    Returns:
        Optional[Path]: Path to the local file, or None if the input is a URL.
    """
    try:
        input_path = Path(input_arg)
        if input_path.exists():
            return input_path
    except:
        pass
    return None

def process_single_input(action: str, input_arg: str, processor: VideoProcessor, **kwargs):
    """
    Handles a single input (URL or local file) for a given action.
    [PT-BR] Lida com uma única entrada (URL ou arquivo local) para uma dada ação.
    """
    logger.info(f"⚙️ [EN] Processing input: {input_arg} - [PT-BR] Processando entrada: {input_arg}")
    
    try:
        if action == "video":
            processor.download_video(input_arg, kwargs.get('resolution'))
        
        elif action == "audio":
            if get_input_path(input_arg):
                processor.extract_audio_from_local_file(Path(input_arg))
            else:
                processor.download_audio(input_arg)
        
        elif action == "subtitles":
            processor.download_subtitles(input_arg, kwargs.get('language'))
        
        elif action == "transcribe":
            audio_path = None
            if get_input_path(input_arg):
                audio_path = get_input_path(input_arg)
            else:
                audio_path = processor.download_audio(input_arg)

            transcribed_text = processor.transcribe(audio_path)
            txt_path = audio_path.with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcribed_text)
            logger.info(f"📝 [EN] Transcription saved to: {txt_path} - [PT-BR] Transcrição salva em: {txt_path}")
        
        elif action == "srt":
            input_path = get_input_path(input_arg)
            if input_path and input_path.suffix.lower() == ".vtt":
                processor.convert_vtt_to_srt(input_path)
            else:
                if input_path:
                    audio_path = input_path
                else:
                    audio_path = processor.download_audio(input_arg)
                processor.generate_srt(audio_path)

        logger.info(f"✅ [EN] Processing finished for: {input_arg} - [PT-BR] Processamento concluído para: {input_arg}")
    
    except (DownloadError, TranscriptionError, FileNotFoundError) as e:
        logger.error(f"❌ [EN] An error occurred while processing '{input_arg}': {e} - [PT-BR] Um erro ocorreu ao processar '{input_arg}': {e}")
    except Exception as e:
        logger.error(f"❌ [EN] An unexpected error occurred while processing '{input_arg}': {e} - [PT-BR] Um erro inesperado ocorreu ao processar '{input_arg}': {e}")

def main():
    config = load_config()
    processor = VideoProcessor(config)

    parser = argparse.ArgumentParser(description="Video and audio processing tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # `video` command
    video_parser = subparsers.add_parser("video", help="Downloads a video from a URL.")
    video_parser.add_argument("input", help="URL of the video to download.")
    video_parser.add_argument("--resolution", default=config.default_video_resolution, help="Video resolution (e.g., '1080p').")

    # `audio` command
    audio_parser = subparsers.add_parser("audio", help="Downloads audio from a URL or extracts it from a local video file.")
    audio_parser.add_argument("input", help="URL of the video or path to the local video file.")

    # `subtitles` command
    subtitles_parser = subparsers.add_parser("subtitles", help="Downloads subtitles from a URL.")
    subtitles_parser.add_argument("input", help="URL of the video.")
    subtitles_parser.add_argument("--language", default=config.subtitle_language, help="Subtitle language (e.g., 'pt').")
    
    # `transcribe` command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribes audio from a URL or local file to a text (.txt) file.")
    transcribe_parser.add_argument("input", help="URL of the video or path to the audio file.")
    
    # `srt` command
    srt_parser = subparsers.add_parser("srt", help="Generates an SRT file from a URL or local file, or converts a VTT file to SRT.")
    srt_parser.add_argument("input", help="URL of the video, path to a local audio/video file, or path to a VTT subtitle file.")

    # `auto` command
    auto_parser = subparsers.add_parser("auto", help="Executes multiple commands from a text file.")
    auto_parser.add_argument("file_path", help="Path to the text file containing commands.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "auto":
            auto_file_path = Path(args.file_path)
            if not auto_file_path.exists() or auto_file_path.suffix.lower() != ".txt":
                logger.error(f"❌ [EN] Action 'auto' requires a valid .txt file path. - [PT-BR] Ação 'auto' requer um caminho de arquivo .txt válido.")
                sys.exit(1)
            
            with open(auto_file_path, "r", encoding="utf-8") as f:
                commands = [line.strip() for line in f if line.strip()]
            if not commands:
                logger.error("❌ [EN] The command file is empty. - [PT-BR] O arquivo de comandos está vazio.")
                sys.exit(1)
            
            for command_line in commands:
                command_parts = shlex.split(command_line)
                command_name = command_parts[0]
                command_args = parser.parse_args([command_name] + command_parts[1:])
                process_single_input(command_name, command_args.input, processor, **vars(command_args))
        
        else:
            process_single_input(args.command, args.input, processor, **vars(args))
    
    except Exception as e:
        logger.error(f"❌ [EN] An unexpected error occurred: {e} - [PT-BR] Um erro inesperado ocorreu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()