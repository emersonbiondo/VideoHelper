# Documentação da API

Esta documentação fornece uma visão geral técnica das classes e métodos que compõem a aplicação VideoHelper.

## Estrutura de Classes

A arquitetura do projeto é baseada no princípio de **Programação Orientada a Objetos (POO)**, com a lógica de negócios distribuída em classes com responsabilidades bem definidas.

### `AppConfig`

-   **Localização:** `video_helper/config.py`
-   **Descrição:** Uma classe de dataclass que armazena todas as configurações da aplicação, lidas a partir do arquivo `config.json`. Ela centraliza as preferências, como a pasta de destino, qualidade de áudio e modelos de transcrição, facilitando a customização sem alterar o código-fonte.
-   **Métodos Notáveis:**
    -   `load_config()`: Função que lê e valida o `config.json`, retornando uma instância de `AppConfig`.

### `YouTubeDownloader`

-   **Localização:** `video_helper/downloader.py`
-   **Descrição:** Encapsula toda a lógica de interação com a biblioteca `yt-dlp`. Esta classe é responsável exclusivamente pelo download de conteúdo a partir de URLs do YouTube.
-   **Métodos Notáveis:**
    -   `download_video(url: str, resolution: str) -> Path`: Baixa um vídeo em uma resolução específica.
    -   `download_audio(url: str) -> Path`: Baixa o áudio de um vídeo.
    -   `download_subtitles(url: str, language: str) -> Optional[Path]`: Baixa legendas de um vídeo.
    -   `_progress_hook(...)`: Método interno que gerencia a barra de progresso do `rich` durante os downloads.

### `LocalFileProcessor`

-   **Localização:** `video_helper/local_processor.py`
-   **Descrição:** Lida com o processamento de arquivos de mídia locais. Utiliza a biblioteca `ffmpeg-python` para realizar operações como a extração de áudio de arquivos de vídeo.
-   **Métodos Notáveis:**
    -   `extract_audio(file_path: Path) -> Path`: Extrai o áudio de um arquivo de vídeo local.

### `WhisperTranscriber`

-   **Localização:** `video_helper/transcriber.py`
-   **Descrição:** Gerencia todas as operações de transcrição e geração de legendas. Carrega o modelo Whisper apenas uma vez para otimizar o desempenho.
-   **Métodos Notáveis:**
    -   `transcribe_audio(audio_path: Path) -> str`: Transcreve o áudio de um arquivo e retorna o texto.
    -   `generate_srt_from_audio(audio_path: Path) -> Path`: Transcreve o áudio e gera um arquivo de legenda no formato `.srt`.
    -   `convert_vtt_to_srt(vtt_path: Path) -> Path`: Converte um arquivo de legenda `.vtt` para `.srt`.

### `VideoProcessor`

-   **Localização:** `video_helper/core.py`
-   **Descrição:** Atua como um orquestrador ou "fachada" para a lógica de negócios. Ele centraliza as chamadas para as classes `YouTubeDownloader`, `LocalFileProcessor` e `WhisperTranscriber`, simplificando a interface para o script principal (`main.py`).

### `Exceptions`

-   **Localização:** `video_helper/exceptions.py`
-   **Descrição:** Define exceções personalizadas como `DownloadError` e `TranscriptionError` para um tratamento de erros mais semântico e claro em toda a aplicação.

## Fluxo de Trabalho

O script principal (`main.py`) é o ponto de entrada da aplicação. Ele recebe os argumentos do usuário e, dependendo da ação e do tipo de entrada (URL, arquivo local, ou arquivo de lista), ele instancia as classes apropriadas (`VideoProcessor`, `LocalFileProcessor`, `WhisperTranscriber`) e chama os métodos correspondentes para executar a tarefa.