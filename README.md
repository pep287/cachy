# Cachy

Baixador de vídeos e músicas do YouTube com interface moderna.

## Funcionalidades

- Download de vídeos em MP4, WebM, MKV
- Download de áudio em MP3, M4A, Opus, WAV
- Enriquecimento automático de metadados via Deezer e iTunes
- Suporte a playlists
- Tema claro e escuro
- FFmpeg embutido no executável

## Como compilar (Windows)

### Requisitos

- [Python 3.12](https://python.org)
- [Git](https://git-scm.com)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) — opcional, para gerar o instalador

### Build

```bat
git clone https://github.com/pep287/cachy
cd cachy
build_windows.bat
```

O script faz tudo automaticamente:
1. Cria o ambiente virtual
2. Instala as dependências (PyQt6, yt-dlp, PyInstaller)
3. Baixa o FFmpeg
4. Compila o executável
5. Gera o instalador em `installer\Cachy_Setup.exe`

## Releases

Você também pode baixar o executável pré-compilado na página de [Releases](https://github.com/pep287/cachy/releases).

## Como compilar (Linux)

### Requisitos

- Python 3
- curl ou git
- PyQt6 (instalado automaticamente se possível)

### Build (automático)

Baixe apenas o script e execute — ele baixa o código do repositório automaticamente:

```bash
curl -sL https://github.com/pep287/cachy/raw/main/build_linux.sh | bash
```

Ou se já clonou o repositório:

```bash
git clone https://github.com/pep287/cachy
cd cachy
chmod +x build_linux.sh
./build_linux.sh
```

O script faz tudo automaticamente:
1. Baixa o código do repositório (se necessário)
2. Instala o PyQt6 via pacote do sistema
3. Cria ambiente virtual e instala dependências
4. Gera o ícone a partir do SVG
5. Baixa o FFmpeg estático
6. Compila o executável em `~/Cachy-Linux/Cachy`

Para instalar no sistema (cria atalho no menu):

```bash
~/Cachy-Linux/install.sh
```

## Dependências

- [PyQt6](https://pypi.org/project/PyQt6/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org)
