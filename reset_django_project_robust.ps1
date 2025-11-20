# A PowerShell script to completely reset a Django project's database and migrations.

cd .\coding\splitcart\
.\venv\Scripts\Activate.ps1

$apps = @(
    "products",
    "companies",
    "data_management",
    "users"
)

# --- EXECUTION ---
Write-Host "🚀 Starting Django Project Reset..." -ForegroundColor Yellow

# 1. Manual Database Reset (MySQL Workbench or SQL Commands)
Write-Host "🔥 Skipping automatic MySQL database reset." -ForegroundColor Yellow
Write-Host "   Please manually drop and recreate the 'splitcart' database using one of the following methods:" -ForegroundColor Yellow
Write-Host "" -ForegroundColor Yellow
Write-Host "   Method 1: MySQL Workbench Interface" -ForegroundColor Yellow
Write-Host "   ----------------------------------" -ForegroundColor Yellow
Write-Host "   1. Open MySQL Workbench and connect to your local database server." -ForegroundColor Yellow
Write-Host "   2. In the Navigator panel (Schemas tab), right-click on the 'splitcart' database." -ForegroundColor Yellow
Write-Host "   3. Select "Drop Schema..." and confirm." -ForegroundColor Yellow
Write-Host "   4. Right-click in the empty space in the Schemas panel and select "Create Schema..."." -ForegroundColor Yellow
Write-Host "   5. Enter 'splitcart' as the name, set Charset to 'utf8mb4' and Collation to 'utf8mb4_unicode_ci'." -ForegroundColor Yellow
Write-Host "   6. Click "Apply" and then "Finish"." -ForegroundColor Yellow
Write-Host "" -ForegroundColor Yellow
Write-Host "   Method 2: SQL Commands (in MySQL Workbench Query Tab or MySQL CLI)" -ForegroundColor Yellow
Write-Host "   ------------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "   DROP DATABASE IF EXISTS splitcart;" -ForegroundColor Yellow
Write-Host "   CREATE DATABASE splitcart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor Yellow
Write-Host "" -ForegroundColor Yellow
Write-Host "   Press any key to continue after manually resetting the database..." -ForegroundColor Yellow
Pause

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

python manage.py update --archive # Server

python manage.py generate --store-groups # Server

python manage.py upload --product --dev # Local
python manage.py update --products # Server

python manage.py update --prefixes # Server

python manage.py generate --cat-links --dev # Local
python manage.py upload --cat-links --dev # Local
python manage.py update --cat-links # Server

python manage.py upload --product --dev # Local
python manage.py update --products

python manage.py generate --subs --dev # Local
python manage.py upload --subs --dev # Local
python manage.py update --subs # Server

python manage.py generate --bargains --dev # Local
python manage.py upload --bargains --dev # Local
python manage.py update --bargains # Server

python manage.py generate --primary-cats # Server

python manage.py analyze --report company_heatmap
python manage.py analyze --report subs
python manage.py analyze --report savings
python manage.py analyze --report category_product_counts --strict
python manage.py debug_savings_run
python manage.py test_unit_price_sorter

python manage.py generate --map --dev # Local


python manage.py generate --primary-cats
python manage.py input_pillars
python manage.py generate --category_stats