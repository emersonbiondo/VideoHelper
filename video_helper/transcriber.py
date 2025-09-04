import logging
import re
from pathlib import Path
import whisper
from .config import AppConfig
from .exceptions import TranscriptionError

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """
    Handles audio transcription and subtitle generation/conversion.
    The model is loaded once upon initialization for performance.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the transcriber and loads the Whisper model.

        Args:
            config (AppConfig): The application configuration object.
        """
        self._config = config
        logger.info(f"🟡 [EN] Loading Whisper model '{self._config.whisper_model}'... - [PT-BR] Carregando modelo Whisper '{self._config.whisper_model}'...")
        try:
            self._model = whisper.load_model(self._config.whisper_model)
            logger.info("✅ [EN] Whisper model loaded successfully. - [PT-BR] Modelo Whisper carregado com sucesso.")
        except Exception as e:
            raise TranscriptionError(f"[EN] Failed to load Whisper model: {e} - [PT-BR] Falha ao carregar modelo Whisper: {e}") from e

    def transcribe_audio(self, audio_path: Path) -> str:
        """
        Transcribes the audio file at the given path.

        Args:
            audio_path (Path): The path to the audio file (.mp3).

        Returns:
            str: The transcribed text.
        
        Raises:
            TranscriptionError: If transcription fails.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"[EN] Audio file not found at: {audio_path} - [PT-BR] Arquivo de áudio não encontrado em: {audio_path}")

        logger.info(f"🟡 [EN] Starting transcription for {audio_path.name}, this may take a while... - [PT-BR] Iniciando transcrição de {audio_path.name}, isso pode demorar...")
        
        try:
            result = self._model.transcribe(
                str(audio_path), 
                language=self._config.transcription_language
            )
            transcribed_text = result.get('text', '')
            logger.info("✅ [EN] Transcription completed successfully. - [PT-BR] Transcrição concluída com sucesso.")
            return transcribed_text
        except Exception as e:
            raise TranscriptionError(f"[EN] An error occurred during transcription: {e} - [PT-BR] Ocorreu um erro durante a transcrição: {e}") from e

    def generate_srt_from_audio(self, audio_path: Path) -> Path:
        """
        Transcribes the audio and generates an SRT subtitle file with timestamps.

        Args:
            audio_path (Path): The path to the audio file.

        Returns:
            Path: The path to the generated SRT file.
        
        Raises:
            TranscriptionError: If transcription or SRT generation fails.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"[EN] Audio file not found at: {audio_path} - [PT-BR] Arquivo de áudio não encontrado em: {audio_path}")

        logger.info(f"🟡 [EN] Starting SRT generation for {audio_path.name}... - [PT-BR] Iniciando geração de SRT para {audio_path.name}...")

        try:
            # Força o modelo a retornar segmentos de tempo
            result = self._model.transcribe(
                str(audio_path),
                language=self._config.transcription_language,
                word_timestamps=False,
            )

            srt_path = audio_path.with_suffix(".srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(result['segments']):
                    # Formata a hora para o padrão SRT (00:00:00,000)
                    start_time = self._format_timestamp(segment['start'])
                    end_time = self._format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")

            logger.info(f"✅ [EN] SRT subtitle file saved to: {srt_path} - [PT-BR] Arquivo de legenda SRT salvo em: {srt_path}")
            return srt_path
        
        except Exception as e:
            raise TranscriptionError(f"[EN] An error occurred during SRT generation: {e} - [PT-BR] Ocorreu um erro durante a geração do SRT: {e}") from e

    def convert_vtt_to_srt(self, vtt_path: Path) -> Path:
        """
        Converts a VTT subtitle file to SRT format.

        Args:
            vtt_path (Path): The path to the .vtt file.

        Returns:
            Path: The path to the generated .srt file.
        
        Raises:
            TranscriptionError: If the conversion fails.
        """
        if not vtt_path.exists():
            raise FileNotFoundError(f"[EN] VTT file not found at: {vtt_path} - [PT-BR] Arquivo VTT não encontrado em: {vtt_path}")
        
        logger.info(f"🟡 [EN] Converting VTT to SRT: {vtt_path.name} - [PT-BR] Convertendo VTT para SRT: {vtt_path.name}")
        
        try:
            srt_path = vtt_path.with_suffix(".srt")
            
            with open(vtt_path, 'r', encoding='utf-8') as infile:
                vtt_content = infile.read()
            
            # Remove a linha "WEBVTT" e outras informações de cabeçalho
            srt_content = re.sub(r'WEBVTT\s*', '', vtt_content, 1)
            # Remove notas e marcações de estilo
            srt_content = re.sub(r'<[^>]*>', '', srt_content)
            srt_content = re.sub(r'NOTE.*', '', srt_content)
            # Substitui o separador de milissegundos de ponto para vírgula
            srt_content = re.sub(r'(\d+)\.(\d+)', r'\1,\2', srt_content)
            
            # Formata os tempos e numera as legendas
            segments = re.split(r'(\n\d{2}:\d{2}:\d{2},\d{3})', srt_content)
            numbered_segments = []
            for i, segment in enumerate(segments[1:], 1):
                if i % 2 == 1: # Cabeçalho do tempo
                    time_line = re.sub(r'\n', '', segment).strip()
                    text = segments[i+1].strip()
                    numbered_segments.append(f"{i // 2 + 1}\n{time_line}\n{text}\n")
            
            # Junta os segmentos com uma linha em branco
            final_srt = "\n".join(numbered_segments)

            with open(srt_path, 'w', encoding='utf-8') as outfile:
                outfile.write(final_srt.strip())

            logger.info(f"✅ [EN] VTT converted to SRT successfully: {srt_path} - [PT-BR] VTT convertido para SRT com sucesso: {srt_path}")
            return srt_path
        
        except Exception as e:
            raise TranscriptionError(f"[EN] Failed to convert VTT to SRT: {e} - [PT-BR] Falha ao converter VTT para SRT: {e}") from e

    def _format_timestamp(self, seconds: float) -> str:
        """
        Formats a float in seconds to SRT timestamp format (HH:MM:SS,mmm).
        """
        milliseconds = int(seconds * 1000.0)
        hours = milliseconds // 3600000
        milliseconds %= 3600000
        minutes = milliseconds // 60000
        milliseconds %= 60000
        seconds = milliseconds // 1000
        milliseconds %= 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"