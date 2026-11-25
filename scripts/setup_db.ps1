# Подготовка базы данных «ФормаДесерт».
# Запуск из корня проекта:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_db.ps1
param(
    [string]$PgHost = "localhost",
    [int]$Port = 5432,
    [string]$User = "postgres",
    [string]$Database = "formadessert"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$sqlFile = Join-Path $projectRoot "db\database.sql"

$psql = (Get-Command psql -ErrorAction SilentlyContinue).Source
$createdb = (Get-Command createdb -ErrorAction SilentlyContinue).Source
if (-not $psql) {
    $defaultBin = "C:\Program Files\PostgreSQL\18\bin"
    if (Test-Path (Join-Path $defaultBin "psql.exe")) {
        $psql = Join-Path $defaultBin "psql.exe"
        $createdb = Join-Path $defaultBin "createdb.exe"
    }
}
if (-not $psql) {
    throw "Не найден psql.exe. Добавьте каталог bin PostgreSQL в PATH."
}

if (-not $env:PGPASSWORD) {
    $secure = Read-Host "Пароль пользователя $User" -AsSecureString
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )
}

$exists = & $psql -h $PgHost -p $Port -U $User -tAc "SELECT 1 FROM pg_database WHERE datname = '$Database'"
if ($exists -ne "1") {
    Write-Host "Создаётся база данных $Database..."
    & $createdb -h $PgHost -p $Port -U $User $Database
}

Write-Host "Загружается структура и данные из $sqlFile..."
& $psql -h $PgHost -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -f $sqlFile
if ($LASTEXITCODE -ne 0) {
    throw "Не удалось выполнить SQL-скрипт."
}

Write-Host "Готово. Проверка количества записей:"
& $psql -h $PgHost -p $Port -U $User -d $Database -c @"
SELECT (SELECT COUNT(*) FROM products) AS products,
       (SELECT COUNT(*) FROM stock_items) AS stock_items,
       (SELECT COUNT(*) FROM users) AS users,
       (SELECT COUNT(*) FROM orders) AS orders,
       (SELECT COUNT(*) FROM order_items) AS order_items;
"@
