#!/bin/bash
set -e

# Abre terminal automaticamente se executado pelo KDE/Alt+F2
if [ ! -t 0 ]; then
    for term in konsole gnome-terminal x-terminal-emulator xterm; do
        if command -v "$term" &>/dev/null; then
            exec "$term" -e bash "$0" "$@"
            exit
        fi
    done
    echo "ERRO: Baixe o script primeiro e execute num terminal:"
    echo "  curl -sL https://github.com/pep287/cachy/raw/main/build_linux.sh -o build_linux.sh"
    echo "  bash build_linux.sh"
    exit 1
fi

echo "========================================"
echo " Compilando Cachy (Linux)"
echo "========================================"
echo

REPO_URL="https://github.com/pep287/cachy"
BUILD_DIR=""
STANDALONE=false
PRECISA_SUDO=false

# Se o cachy.py não estiver aqui, baixa do repositório
if [ ! -f cachy.py ]; then
    STANDALONE=true
    BUILD_DIR="/tmp/cachy-build-$$"
    echo "[0/6] Baixando código do repositório..."
    rm -rf "$BUILD_DIR"
    if command -v git &>/dev/null; then
        git clone --depth=1 "$REPO_URL" "$BUILD_DIR"
    else
        curl -sL "$REPO_URL/archive/refs/heads/main.tar.gz" -o /tmp/cachy-repo.tar.gz
        mkdir -p "$BUILD_DIR"
        tar -xf /tmp/cachy-repo.tar.gz -C "$BUILD_DIR" --strip-components=1
        rm /tmp/cachy-repo.tar.gz
    fi
    cd "$BUILD_DIR"
else
    echo "[0/6] Usando arquivos locais..."
    BUILD_DIR="$(pwd)"
fi

PYTHON=python3

# Verifica Python
if ! command -v $PYTHON &>/dev/null; then
    echo "ERRO: Python 3 não encontrado. Instale com seu gerenciador de pacotes."
    exit 1
fi

# Cria ambiente virtual limpo (sem --system-site-packages)
echo "[1/6] Criando ambiente virtual..."
rm -rf "$BUILD_DIR/venv"
$PYTHON -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"

# Instala dependências Python
echo "[2/6] Instalando dependências Python..."
pip install --upgrade pip -q

# Tenta instalar PyQt6 via pip (funciona se Qt6 já estiver no sistema)
echo "[2b/6] Instalando PyQt6..."
if ! pip install PyQt6 -q 2>/dev/null; then
    echo "PyQt6 via pip falhou. Tentando pacote do sistema..."
    PRECISA_SUDO=true
    if command -v apt &>/dev/null; then
        sudo apt install -y python3-pyqt6 python3-pip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-pyqt6 python-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pyqt6 python3-pip
    else
        echo "ERRO: Não foi possível instalar PyQt6."
        echo "Instale python3-pyqt6 + python3-pip manualmente."
        exit 1
    fi
    # Recria venv com acesso ao PyQt6 do sistema
    rm -rf "$BUILD_DIR/venv"
    $PYTHON -m venv "$BUILD_DIR/venv" --system-site-packages
    source "$BUILD_DIR/venv/bin/activate"
fi

# Instala demais dependências
pip install yt-dlp pyinstaller cairosvg pillow -q

# Gera ícone PNG a partir do SVG
echo "[3/6] Gerando ícone..."
if [ -f cachy_icon.svg ]; then
    $PYTHON -c "
import cairosvg
cairosvg.svg2png(url='cachy_icon.svg', write_to='cachy_icon.png',
                 output_width=256, output_height=256)
print('Ícone gerado')
" 2>/dev/null || echo "AVISO: cairosvg falhou, pulando ícone."
elif [ -f cachy_icon.ico ]; then
    echo "Convertendo .ico para .png..."
    $PYTHON -c "
from PIL import Image
img = Image.open('cachy_icon.ico')
img = img.resize((256, 256), Image.LANCZOS)
img.save('cachy_icon.png')
" 2>/dev/null || true
fi

echo "[4/6] Verificando FFmpeg..."
FFMPEG_OK=false
if command -v ffmpeg &>/dev/null && command -v ffprobe &>/dev/null; then
    echo "  FFmpeg encontrado no sistema. Será usado em tempo de execução."
    FFMPEG_OK=true
else
    echo "  FFmpeg não encontrado no sistema. Baixando versão estática..."
    FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    curl -sL "$FFMPEG_URL" -o /tmp/ffmpeg.tar.xz
    tar -xf /tmp/ffmpeg.tar.xz --wildcards "*/bin/ffmpeg" "*/bin/ffprobe" --strip-components=2
    rm /tmp/ffmpeg.tar.xz
    chmod +x ffmpeg ffprobe
fi

# Compila com PyInstaller
echo "[5/6] Compilando com PyInstaller (pode levar vários minutos)..."
rm -rf "$BUILD_DIR/build" "$BUILD_DIR/dist_cachy" "$BUILD_DIR"/*.spec

PYINST_ARGS=(
    --name "Cachy"
    --windowed
    --onedir
    --noconfirm
    --distpath "$BUILD_DIR/dist_cachy"
)

# Só embala o FFmpeg se baixamos o estático
if [ "$FFMPEG_OK" = false ]; then
    PYINST_ARGS+=(--add-binary "ffmpeg:." --add-binary "ffprobe:.")
fi

pyinstaller "${PYINST_ARGS[@]}" "$BUILD_DIR/cachy.py"

# Verifica se gerou
if [ ! -f "$BUILD_DIR/dist_cachy/Cachy/Cachy" ]; then
    echo "ERRO: Executável não encontrado."
    exit 1
fi

# Empacota resultado
echo "[6/6] Criando pacote..."
OUTPUT_DIR="$HOME/Cachy-Linux"
mkdir -p "$OUTPUT_DIR"
cp -r "$BUILD_DIR/dist_cachy/Cachy"/* "$OUTPUT_DIR/"
if [ -f cachy_icon.png ]; then
    cp cachy_icon.png "$OUTPUT_DIR/"
fi

# .desktop
cat > "$OUTPUT_DIR/cachy.desktop" << 'DESKTOP'
[Desktop Entry]
Name=Cachy
Comment=Baixador de vídeos e músicas do YouTube
Exec=INSTALL_DIR/Cachy
Icon=INSTALL_DIR/cachy_icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Network;
DESKTOP

# Script de instalação
cat > "$OUTPUT_DIR/install.sh" << 'INSTALL'
#!/bin/bash
DEST="$HOME/.local/share/cachy"
mkdir -p "$DEST"
cp -r "$(dirname "$0")"/* "$DEST/"
chmod +x "$DEST/Cachy"
sed -i "s|INSTALL_DIR|$DEST|g" "$DEST/cachy.desktop"
mkdir -p "$HOME/.local/share/applications"
cp "$DEST/cachy.desktop" "$HOME/.local/share/applications/"
echo "Cachy instalado!"
INSTALL
chmod +x "$OUTPUT_DIR/install.sh"

# Limpa se for standalone
if [ "$STANDALONE" = true ]; then
    rm -rf "$BUILD_DIR"
fi

echo
echo "========================================"
echo " Concluído!"
echo " Pasta: $OUTPUT_DIR"
echo " Tamanho: $(du -sh "$OUTPUT_DIR" | cut -f1)"
echo
echo " Para testar: $OUTPUT_DIR/Cachy"
echo " Para instalar: $OUTPUT_DIR/install.sh"
echo "========================================"
