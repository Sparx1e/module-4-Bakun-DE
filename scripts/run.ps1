# Запуск приложения «ФормаДесерт» из исходного кода.
# Параметры подключения берутся из переменных среды или файла .env.
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
python -m app.main
