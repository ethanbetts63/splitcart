# A PowerShell script to completely reset a Django project's database and migrations.

cd .\coding\splitcart\
.\venv\Scripts\Activate.ps1

$apps = @(
    "products",
    "companies",
    "data_management"
)

# --- EXECUTION ---
Write-Host "🚀 Starting Django Project Reset..." -ForegroundColor Yellow

# 1. Delete the SQLite Database file
Write-Host "🔥 Deleting database file (db.sqlite3)..." -ForegroundColor Cyan
try {
    Remove-Item -Path "db.sqlite3" -ErrorAction Stop
    Write-Host "  - Database file deleted successfully." -ForegroundColor Green
} catch {
    Write-Host "  - ERROR: Could not delete database file. It might be locked by another process." -ForegroundColor Red
    # Exit the script because subsequent steps will fail.
    exit 1
}

# 2. Delete old migration files from specified apps
Write-Host "🔥 Deleting old migration files..." -ForegroundColor Cyan
foreach ($app in $apps) {
    # Construct the path to the migrations folder for each app
    $migrationPath = Join-Path -Path $app -ChildPath "migrations"

    # Check if the migrations directory exists before trying to clean it
    if (Test-Path $migrationPath) {
        # Find and remove all files except for __init__.py
        Get-ChildItem -Path $migrationPath -File | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item -Force
        Write-Host "  - Cleaned migrations for '$app' app."
    } else {
        Write-Host "  - No migrations folder found for '$app', skipping." -ForegroundColor Gray
    }
}

# 3. Delete all __pycache__ directories to ensure a clean state
Write-Host "🔥 Deleting __pycache__ directories..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Make a new, unified migration plan for the whole project
Write-Host "✨ Creating a unified migration plan for the whole project..." -ForegroundColor Cyan
python manage.py makemigrations

# 5. Apply migrations to the database
Write-Host "✨ Applying migrations to create a new database..." -ForegroundColor Cyan
python manage.py migrate

Write-Host "✅ Django Project Reset Complete!" -ForegroundColor Green

git add .
git commit -m "reset django project robust.ps1"
git push

python manage.py update --archive
python manage.py cluster_stores
python manage.py update --products
python manage.py update --prefixes
python manage.py update --category-links
python manage.py update --products
python manage.py generate_subs
python manage.py find_bargains
python manage.py analyze --report company_heatmap
python manage.py analyze --report subs
python manage.py analyze --report savings
python manage.py debug_savings_run
python manage.py test_unit_price_sorter
python manage.py archive