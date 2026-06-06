@echo off
chcp 65001 >nul
title Build Cachy

echo ========================================
echo  Compilando Cachy
echo ========================================
echo.

:: Verifica Python 3.12 primeiro, senao usa o python padrao
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py -3.12
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERRO: Python nao encontrado. Instale Python 3.12 em https://python.org
        pause
        exit /b 1
    )
    set PYTHON=python
    echo AVISO: Python 3.12 nao encontrado, usando versao padrao.
    echo.
)

:: Cria ambiente virtual
echo [1/5] Criando ambiente virtual...
if exist venv rmdir /s /q venv
%PYTHON% -m venv venv
if errorlevel 1 (
    echo ERRO: Falha ao criar ambiente virtual.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: Instala dependencias
echo [2/5] Instalando dependencias...
python -m pip install --upgrade pip -q
python -m pip install PyQt6 yt-dlp pyinstaller -q
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

:: Gera icone .ico a partir do SVG
echo [2b/5] Gerando icone...
python -m pip install cairosvg pillow -q
python -c "import cairosvg; cairosvg.svg2png(url='cachy_icon.svg', write_to='cachy_icon.png', output_width=256, output_height=256)"
python -c "from PIL import Image; img = Image.open('cachy_icon.png'); img.save('cachy_icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

:: Baixa FFmpeg se nao existir
echo [3/5] Verificando FFmpeg...
if not exist ffmpeg.exe (
    echo Baixando FFmpeg...
    python -c "import urllib.request, zipfile, os, shutil; urllib.request.urlretrieve('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', 'ffmpeg.zip'); z=zipfile.ZipFile('ffmpeg.zip'); [z.extract(m, 'ffmpeg_tmp') for m in z.namelist() if m.endswith(('ffmpeg.exe','ffprobe.exe'))]; z.close(); [shutil.move(p, '.') for r,d,files in os.walk('ffmpeg_tmp') for f in files for p in [os.path.join(r,f)] if f in ('ffmpeg.exe','ffprobe.exe')]; shutil.rmtree('ffmpeg_tmp'); os.remove('ffmpeg.zip'); print('FFmpeg baixado.')"
    if errorlevel 1 (
        echo AVISO: Nao foi possivel baixar o FFmpeg automaticamente.
        echo Baixe manualmente em https://ffmpeg.org e coloque ffmpeg.exe aqui.
    )
) else (
    echo FFmpeg ja presente.
)

:: Compila com PyInstaller
echo [4/5] Compilando com PyInstaller...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Cachy.spec del Cachy.spec

pyinstaller ^
    --name "Cachy" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --icon "cachy_icon.ico" ^
    --add-binary "ffmpeg.exe;." ^
    --add-binary "ffprobe.exe;." ^
    cachy.py

if errorlevel 1 (
    echo.
    echo ERRO: Falha na compilacao. Veja o log acima.
    pause
    exit /b 1
)

:: Gera instalador com Inno Setup
echo [5/5] Gerando instalador...

set INNO=
for %%P in (
    "C:\Users\pepeu\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist %%P set INNO=%%P
)

if defined INNO (
    %INNO% installer\cachy_setup.iss
    if errorlevel 1 (
        echo AVISO: Falha ao gerar instalador.
    ) else (
        echo Instalador gerado em installer\Cachy_Setup.exe
    )
) else (
    echo AVISO: Inno Setup nao encontrado. Instale em https://jrsoftware.org/isinfo.php
    echo O executavel esta disponivel em dist\Cachy\Cachy.exe
)

echo.
echo ========================================
echo  Concluido!
echo  Instalador: installer\Cachy_Setup.exe
echo ========================================
echo.
pause >nul
