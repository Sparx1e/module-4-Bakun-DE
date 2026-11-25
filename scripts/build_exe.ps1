# Сборка исполняемого файла PyInstaller.
# Результат: dist\FormaDessert\FormaDessert.exe
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name FormaDessert `
    --icon "resources\app.ico" `
    --add-data "resources;resources" `
    --paths . `
    "main.py"

Write-Host "Готово: dist\FormaDessert\FormaDessert.exe"
