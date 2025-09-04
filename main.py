import argparse
import logging
import sys
import mimetypes
from pathlib import Path
from rich.console import Console

# Adicione o diretório pai ao PYTHONPATH para que os módulos internos possam ser importados
# Add the parent directory to the PYTHONPATH so internal modules can be imported
sys.path.insert(0, str(Path(__file__).parent))

from video_helper.config import settings
from video_helper.core import VideoProcessor
from video_helper.local_processor import LocalFileProcessor
from video_helper.transcriber import WhisperTranscriber
from video_helper.exceptions import DownloadError, TranscriptionError

# Configure o logger para a aplicação
# Configure the application logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
console = Console()

def run():
    """Main function to parse arguments and execute the video helper actions."""
    parser = argparse.ArgumentParser(
        description="A utility to download YouTube videos, audio, subtitles, or transcribe audio."
    )
    
    # Argumentos posicionais: a ordem importa
    # Positional arguments: order matters
    parser.add_argument(
        "action",
        choices=["video", "audio", "subtitles", "transcribe", "srt"],
        help="[EN] Action to perform: 'video', 'audio', 'subtitles', 'transcribe', or 'srt' - [PT-BR] Ação a ser executada: 'video', 'audio', 'subtitles', 'transcribe' ou 'srt'"
    )
    parser.add_argument(
        "input", 
        help="[EN] URL of the YouTube video, a local file path (e.g., video.mp4), or a path to a list file (e.g., list.txt) - [PT-BR] URL do vídeo do YouTube, um caminho de arquivo local (ex: video.mp4), ou um caminho para um arquivo de lista (ex: lista.txt)"
    )

    # Argumentos opcionais com flags
    # Optional arguments with flags
    parser.add_argument(
        "--resolution",
        default=settings.default_video_resolution, 
        help=f"[EN] Video resolution to download (e.g., '1080p', '720p', '480p'). Only for action 'video'. - [PT-BR] Resolução do vídeo para download (ex: '1080p', '720p', '480p'). Somente para a ação 'video'. Padrão: {settings.default_video_resolution}"
    )
    parser.add_argument(
        "--language",
        default=settings.subtitle_language, 
        help=f"[EN] Subtitle language (default: {settings.subtitle_language}). Only for actions 'subtitles' or 'transcribe'. - [PT-BR] Idioma da legenda (padrão: {settings.subtitle_language}). Somente para as ações 'subtitles' ou 'transcribe'."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="[EN] Force audio transcription even if subtitles are found. Only for action 'transcribe'. - [PT-BR] Força a transcrição do áudio mesmo que legendas sejam encontradas. Somente para a ação 'transcribe'."
    )
    
    args = parser.parse_args()
    
    # Prepara a lista de entradas a serem processadas com base na extensão
    # Prepares the list of inputs to be processed based on the file extension
    inputs_to_process = []
    
    input_path = Path(args.input)
    if input_path.is_file() and input_path.suffix.lower() == ".txt":
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                inputs_to_process = [line.strip() for line in f if line.strip()]
            if not inputs_to_process:
                console.print("❌ [red][EN] The input list file is empty or could not be read. - [PT-BR] O arquivo de lista de entrada está vazio ou não pôde ser lido.[/red]")
                sys.exit(1)
        except FileNotFoundError:
            console.print(f"❌ [red][EN] The list file '{args.input}' was not found. - [PT-BR] O arquivo de lista '{args.input}' não foi encontrado.[/red]")
            sys.exit(1)
    else:
        inputs_to_process.append(args.input)

    # Processa cada entrada na lista
    # Process each input in the list
    for current_input in inputs_to_process:
        is_url = current_input.startswith(('http://', 'https://'))
        input_path = Path(current_input)
        
        console.print(f"\n[cyan]⚙️ [EN] Processing input: {current_input} - [PT-BR] Processando entrada: {current_input}[/cyan]\n")

        try:
            if args.action == "video":
                if not is_url:
                    console.print("❌ [red][EN] Action 'video' only supports YouTube URLs. - [PT-BR] Ação 'video' suporta apenas URLs do YouTube.[/red]")
                    continue
                processor = VideoProcessor(settings)
                file_path = processor.download_video(current_input, args.resolution)
                console.print(f"🎥 [green][EN] Video file saved at: {file_path} - [PT-BR] Arquivo de vídeo salvo em: {file_path}[/green]")
            
            elif args.action == "audio":
                if is_url:
                    processor = VideoProcessor(settings)
                    file_path = processor.download_audio(current_input)
                else:
                    local_processor = LocalFileProcessor(settings)
                    file_path = local_processor.extract_audio(input_path)
                console.print(f"🎧 [green][EN] Audio file saved at: {file_path} - [PT-BR] Arquivo de áudio salvo em: {file_path}[/green]")
            
            elif args.action == "subtitles":
                if not is_url:
                    console.print("❌ [red][EN] Action 'subtitles' only supports YouTube URLs. - [PT-BR] Ação 'subtitles' suporta apenas URLs do YouTube.[/red]")
                    continue
                processor = VideoProcessor(settings)
                file_path = processor.download_subtitles(current_input, args.language)
                if file_path:
                    console.print(f"📜 [green][EN] Subtitle file saved at: {file_path} - [PT-BR] Arquivo de legenda salvo em: {file_path}[/green]")
                else:
                    console.print(f"⚠️ [yellow][EN] No subtitles found for the specified language. - [PT-BR] Nenhuma legenda encontrada para o idioma especificado.[/yellow]")
            
            elif args.action in ["transcribe", "srt"]:
                transcriber = WhisperTranscriber(settings)
                
                # Nova lógica da ação SRT
                if args.action == "srt":
                    if not is_url and input_path.suffix.lower() == ".vtt":
                        srt_path = transcriber.convert_vtt_to_srt(input_path)
                        console.print(f"📜 [green][EN] Converted VTT to SRT: {srt_path} - [PT-BR] VTT convertido para SRT: {srt_path}[/green]")
                        continue
                    # Se não for um VTT, segue para a lógica de transcrição normal
                
                audio_path = None
                if is_url:
                    processor = VideoProcessor(settings)
                    transcription_language = args.language if args.language != settings.subtitle_language else settings.transcription_language
                    
                    if args.action == "transcribe" and not args.force:
                        console.print(f"🟡 [yellow][EN] First, trying to download subtitles for URL: {current_input} in '{transcription_language}'... - [PT-BR] Primeiro, tentando baixar legendas para a URL: {current_input} em '{transcription_language}'...[/yellow]")
                        subtitle_path = processor.download_subtitles(current_input, transcription_language)
                        if subtitle_path:
                            console.print(f"✅ [green][EN] Subtitles were found and saved at: {subtitle_path} - [PT-BR] Legendas foram encontradas e salvas em: {subtitle_path}[/green]")
                            continue

                    console.print(f"⚠️ [yellow][EN] No subtitles found or transcription was forced. Proceeding with audio transcription... - [PT-BR] Nenhuma legenda encontrada ou a transcrição foi forçada. Prosseguindo com a transcrição do áudio...[/yellow]")
                    audio_path = processor.download_audio(current_input)
                
                else: # Arquivo local
                    local_processor = LocalFileProcessor(settings)
                    mime_type, _ = mimetypes.guess_type(input_path)
                    
                    if mime_type and mime_type.startswith('audio/'):
                        console.print(f"🟡 [yellow][EN] Input is an audio file. Using it directly... - [PT-BR] A entrada é um arquivo de áudio. Usando-o diretamente...[/yellow]")
                        audio_path = input_path
                    else:
                        audio_path = local_processor.extract_audio(input_path)
                
                if args.action == "transcribe":
                    transcribed_text = transcriber.transcribe_audio(audio_path)
                    txt_path = audio_path.with_suffix(".txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(transcribed_text)
                    console.print(f"📝 [green][EN] Transcription saved to: {txt_path} - [PT-BR] Transcrição salva em: {txt_path}[/green]")
                elif args.action == "srt":
                    srt_path = transcriber.generate_srt_from_audio(audio_path)
                    console.print(f"📜 [green][EN] SRT file saved to: {srt_path} - [PT-BR] Arquivo SRT salvo em: {srt_path}[/green]")
            
        except (DownloadError, TranscriptionError, FileNotFoundError) as e:
            console.print(f"❌ [red][EN] An error occurred while processing '{current_input}': {e} - [PT-BR] Um erro ocorreu ao processar '{current_input}': {e}[/red]")
            continue
        except Exception as e:
            console.print(f"❌ [red][EN] An unexpected error occurred while processing '{current_input}': {e} - [PT-BR] Um erro inesperado ocorreu ao processar '{current_input}': {e}[/red]")
            continue

if __name__ == "__main__":
    run()