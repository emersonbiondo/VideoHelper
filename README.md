# VideoHelper

Uma ferramenta de linha de comando poderosa e versátil, projetada para auxiliar criadores de conteúdo na **produção e edição de legendas** para seus próprios vídeos.

## 🎯 Objetivo

O **VideoHelper** foi criado para simplificar o fluxo de trabalho de criadores de conteúdo. Em vez de usar várias ferramentas, você pode gerenciar o processo completo de legendagem a partir do terminal, desde a extração do áudio até a geração de legendas com marcações de tempo precisas, garantindo que o seu conteúdo seja acessível e de alta qualidade.

## 🌟 Funcionalidades

O **VideoHelper** oferece uma gama completa de ações, permitindo o processamento de URLs, arquivos de vídeo e áudio locais, e até mesmo listas de entradas a partir de arquivos de texto.

* **Download de Mídia:** Baixe vídeos em resoluções específicas, áudios e legendas de vídeos.
* **Extração de Áudio:** Extraia áudio de arquivos de vídeo locais (MP4, MOV, etc.).
* **Transcrição de Áudio:** Transcreva áudio para texto plano (`.txt`) ou para legendas com marcações de tempo (`.srt`) usando o modelo Whisper.
* **Conversão de Legendas:** Converta arquivos de legenda no formato `.vtt` para o formato padrão `.srt`.
* **Processamento em Lote:** Processe múltiplas URLs ou arquivos de uma só vez, fornecendo uma lista em um arquivo de texto.

## 🚀 Instalação

Antes de usar o **VideoHelper**, você precisa garantir que todas as dependências estejam instaladas.

1.  **Clone o repositório ou baixe os arquivos do projeto.**
2.  **Instale as dependências Python** listadas no arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Instale o FFmpeg:** O FFmpeg é um requisito fundamental para o download e a conversão de áudio/vídeo. Siga as instruções no [site oficial do FFmpeg](https://ffmpeg.org/download.html) para instalá-lo no seu sistema operacional e certifique-se de que ele está no seu PATH.

## 📖 Como Usar

A sintaxe de uso do **VideoHelper** é simples e intuitiva, seguindo o padrão `python main.py <ação> <entrada>`. A entrada pode ser uma URL do YouTube, um caminho de arquivo local ou um arquivo de lista de texto.

### Ações Disponíveis

| Ação       | Descrição                                                              | Exemplo de Uso                                                                  |
|------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `video`    | Baixa um vídeo do YouTube em uma resolução específica.                 | `python main.py video https://youtu.be/meu_video`                               |
| `audio`    | Baixa o áudio de uma URL ou extrai o áudio de um arquivo local.        | `python main.py audio https://youtu.be/meu_audio`                               |
| `subtitles`| Baixa legendas de um vídeo do YouTube.                                 | `python main.py subtitles https://youtu.be/minha_legenda`                      |
| `transcribe`| Transcreve áudio para texto plano (`.txt`).                            | `python main.py transcribe https://youtu.be/meu_audio`                          |
| `srt`      | Gera uma legenda com marcações de tempo (`.srt`) a partir de áudio ou converte um `.vtt` local. | `python main.py srt https://youtu.be/minha_legenda`                              |

### Exemplos Detalhados

* **Baixar um vídeo em 720p:**
    ```bash
    python main.py video [https://www.youtube.com/watch?v=meu_video](https://www.youtube.com/watch?v=meu_video) --resolution 720p
    ```

* **Transcrever o áudio de um arquivo de vídeo local:**
    ```bash
    python main.py transcribe "caminho/para/meu_video.mp4"
    ```

* **Processar uma lista de links e arquivos:**
    (Crie um arquivo `lista.txt` com um link ou caminho por linha.)
    ```txt
    # Conteúdo de lista.txt
    [https://www.youtube.com/watch?v=video1](https://www.youtube.com/watch?v=video1)
    /caminho/para/video2.mp4
    /caminho/para/audio3.mp3
    ```
    (Em seguida, execute o comando, passando o arquivo de lista como entrada.)
    ```bash
    python main.py transcribe lista.txt
    ```

* **Converter uma legenda VTT baixada para SRT:**
    ```bash
    python main.py srt resultados/legenda_baixada.vtt
    ```