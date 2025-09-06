import argparse
import logging
import sys
import mimetypes
import shlex
from pathlib import Path
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent))

from video_helper.config import settings
from video_helper.core import VideoProcessor
from video_helper.local_processor import LocalFileProcessor
from video_helper.transcriber import WhisperTranscriber
from video_helper.exceptions import DownloadError, TranscriptionError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
console = Console()

def execute_action(action: str, current_input: str, args: argparse.Namespace):
    is_url = current_input.startswith(('http://', 'https://'))
    input_path = Path(current_input)
    
    console.print(f"\n[cyan]⚙️ [EN] Processing input: {current_input} - [PT-BR] Processando entrada: {current_input}[/cyan]\n")

    try:
        if action == "video":
            if not is_url:
                console.print("❌ [red][EN] Action 'video' only supports YouTube URLs. - [PT-BR] Ação 'video' suporta apenas URLs do YouTube.[/red]")
                return
            processor = VideoProcessor(settings)
            file_path = processor.download_video(current_input, args.resolution)
            console.print(f"🎥 [green][EN] Video file saved at: {file_path} - [PT-BR] Arquivo de vídeo salvo em: {file_path}[/green]")
        
        elif action == "audio":
            if is_url:
                processor = VideoProcessor(settings)
                file_path = processor.download_audio(current_input)
            else:
                local_processor = LocalFileProcessor(settings)
                file_path = local_processor.extract_audio(input_path)
            console.print(f"🎧 [green][EN] Audio file saved at: {file_path} - [PT-BR] Arquivo de áudio salvo em: {file_path}[/green]")
        
        elif action == "subtitles":
            if not is_url:
                console.print("❌ [red][EN] Action 'subtitles' only supports YouTube URLs. - [PT-BR] Ação 'subtitles' suporta apenas URLs do YouTube.[/red]")
                return
            processor = VideoProcessor(settings)
            file_path = processor.download_subtitles(current_input, args.language)
            if file_path:
                console.print(f"📜 [green][EN] Subtitle file saved at: {file_path} - [PT-BR] Arquivo de legenda salvo em: {file_path}[/green]")
            else:
                console.print(f"⚠️ [yellow][EN] No subtitles found for the specified language. - [PT-BR] Nenhuma legenda encontrada para o idioma especificado.[/yellow]")
        
        elif action in ["transcribe", "srt"]:
            transcriber = WhisperTranscriber(settings)
            
            if action == "srt":
                if not is_url and input_path.suffix.lower() == ".vtt":
                    srt_path = transcriber.convert_vtt_to_srt(input_path)
                    console.print(f"📜 [green][EN] Converted VTT to SRT: {srt_path} - [PT-BR] VTT convertido para SRT: {srt_path}[/green]")
                    return
            
            audio_path = None
            if is_url:
                processor = VideoProcessor(settings)
                transcription_language = args.language if args.language != settings.subtitle_language else settings.transcription_language
                
                if action == "transcribe" and not args.force:
                    console.print(f"🟡 [yellow][EN] First, trying to download subtitles for URL: {current_input} in '{transcription_language}'... - [PT-BR] Primeiro, tentando baixar legendas para a URL: {current_input} em '{transcription_language}'...[/yellow]")
                    subtitle_path = processor.download_subtitles(current_input, transcription_language)
                    if subtitle_path:
                        console.print(f"✅ [green][EN] Subtitles were found and saved at: {subtitle_path} - [PT-BR] Legendas foram encontradas e salvas em: {subtitle_path}[/green]")
                        return

                console.print(f"⚠️ [yellow][EN] No subtitles found or transcription was forced. Proceeding with audio transcription... - [PT-BR] Nenhuma legenda encontrada ou a transcrição foi forçada. Prosseguindo com a transcrição do áudio...[/yellow]")
                audio_path = processor.download_audio(current_input)
            
            else:
                local_processor = LocalFileProcessor(settings)
                mime_type, _ = mimetypes.guess_type(input_path)
                
                if mime_type and mime_type.startswith('audio/'):
                    console.print(f"🟡 [yellow][EN] Input is an audio file. Using it directly... - [PT-BR] A entrada é um arquivo de áudio. Usando-o diretamente...[/yellow]")
                    audio_path = input_path
                else:
                    audio_path = local_processor.extract_audio(input_path)
            
            if action == "transcribe":
                transcribed_text = transcriber.transcribe_audio(audio_path)
                txt_path = audio_path.with_suffix(".txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(transcribed_text)
                console.print(f"📝 [green][EN] Transcription saved to: {txt_path} - [PT-BR] Transcrição salva em: {txt_path}[/green]")
            elif action == "srt":
                srt_path = transcriber.generate_srt_from_audio(audio_path)
                console.print(f"📜 [green][EN] SRT file saved to: {srt_path} - [PT-BR] Arquivo SRT salvo em: {srt_path}[/green]")
        
    except (DownloadError, TranscriptionError, FileNotFoundError) as e:
        console.print(f"❌ [red][EN] An error occurred while processing '{current_input}': {e} - [PT-BR] Um erro ocorreu ao processar '{current_input}': {e}[/red]")
    except Exception as e:
        console.print(f"❌ [red][EN] An unexpected error occurred while processing '{current_input}': {e} - [PT-BR] Um erro inesperado ocorreu ao processar '{current_input}': {e}[/red]")

def run():
    parser = argparse.ArgumentParser(
        description="A utility to download YouTube videos, audio, subtitles, or transcribe audio."
    )
    
    parser.add_argument(
        "action",
        choices=["video", "audio", "subtitles", "transcribe", "srt", "auto"],
        help="[EN] Action to perform: 'video', 'audio', 'subtitles', 'transcribe', 'srt', or 'auto' - [PT-BR] Ação a ser executada: 'video', 'audio', 'subtitles', 'transcribe', 'srt' ou 'auto'"
    )
    parser.add_argument(
        "input", 
        help="[EN] URL of the YouTube video, a local file path, or a path to a list file - [PT-BR] URL do vídeo do YouTube, um caminho de arquivo local, ou um caminho para um arquivo de lista"
    )

    parser.add_argument(
        "--resolution",
        default=settings.default_video_resolution, 
        help=f"[EN] Video resolution to download (e.g., '1080p', '720p', '480p'). - [PT-BR] Resolução do vídeo para download (ex: '1080p', '720p', '480p'). Padrão: {settings.default_video_resolution}"
    )
    parser.add_argument(
        "--language",
        default=settings.subtitle_language, 
        help=f"[EN] Subtitle language (default: {settings.subtitle_language}). - [PT-BR] Idioma da legenda (padrão: {settings.subtitle_language})."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="[EN] Force audio transcription even if subtitles are found. - [PT-BR] Força a transcrição do áudio mesmo que legendas sejam encontradas."
    )
    
    args = parser.parse_args()

    if args.action == "auto":
        input_path = Path(args.input)
        if not input_path.is_file() or input_path.suffix.lower() != ".txt":
            console.print("❌ [red][EN] Action 'auto' requires a valid .txt file path. - [PT-BR] Ação 'auto' requer um caminho de arquivo .txt válido.[/red]")
            sys.exit(1)
        
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                commands = [line.strip() for line in f if line.strip()]
            if not commands:
                console.print("❌ [red][EN] The command file is empty. - [PT-BR] O arquivo de comandos está vazio.[/red]")
                sys.exit(1)
            
            for command_line in commands:
                try:
                    command_parts = shlex.split(command_line)
                    command_action = command_parts[0]
                    command_input = command_parts[1]
                    
                    auto_args = argparse.Namespace(
                        action=command_action,
                        input=command_input,
                        resolution=args.resolution,
                        language=args.language,
                        force=args.force
                    )
                    
                    execute_action(auto_args.action, auto_args.input, auto_args)
                
                except IndexError:
                    console.print(f"⚠️ [yellow][EN] Skipping invalid command format: '{command_line}'. - [PT-BR] Ignorando formato de comando inválido: '{command_line}'.[/yellow]")
                    continue
        except FileNotFoundError:
            console.print(f"❌ [red][EN] The command file '{args.input}' was not found. - [PT-BR] O arquivo de comando '{args.input}' não foi encontrado.[/red]")
            sys.exit(1)

    else:
        inputs_to_process = []
        if Path(args.input).is_file() and Path(args.input).suffix.lower() == ".txt":
            try:
                with open(Path(args.input), "r", encoding="utf-8") as f:
                    inputs_to_process = [line.strip() for line in f if line.strip()]
                if not inputs_to_process:
                    console.print("❌ [red][EN] The input list file is empty or could not be read. - [PT-BR] O arquivo de lista de entrada está vazio ou não pôde ser lido.[/red]")
                    sys.exit(1)
            except FileNotFoundError:
                console.print(f"❌ [red][EN] The list file '{args.input}' was not found. - [PT-BR] O arquivo de lista '{args.input}' não foi encontrado.[/red]")
                sys.exit(1)
        else:
            inputs_to_process.append(args.input)

        for current_input in inputs_to_process:
            execute_action(args.action, current_input, args)


if __name__ == "__main__":
    run()