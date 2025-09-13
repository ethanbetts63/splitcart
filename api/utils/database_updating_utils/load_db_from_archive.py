import os
import subprocess

def load_db_from_latest_archive(command):
    base_archive_dir = os.path.join('api', 'data', 'archive', 'db_backups')
    load_order = [
        'companies.company.json',
        'companies.division.json',
        'companies.store.json',
        'companies.category.json',
        'products.productbrand.json',
        'products.brandprefix.json',
        'products.product.json',
        'products.price.json',
        'products.productsubstitution.json',
        'products.productsizevariant.json',
    ]

    if not os.path.exists(base_archive_dir):
        command.stderr.write(command.style.ERROR(f"Archive directory not found: {base_archive_dir}"))
        return
    
    all_dirs = [d for d in os.listdir(base_archive_dir) if os.path.isdir(os.path.join(base_archive_dir, d))]
    if not all_dirs:
        command.stderr.write(command.style.ERROR("No archive directories found."))
        return
    
    latest_dir_name = sorted(all_dirs, reverse=True)[0]
    archive_dir = os.path.join(base_archive_dir, latest_dir_name)

    command.stdout.write(f"Loading data from latest archive: {archive_dir}")

    python_executable = os.path.abspath(os.path.join('venv', 'Scripts', 'python.exe'))
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'

    command.stdout.write(command.style.WARNING("This will completely wipe the database before loading data."))
    flush_command = [python_executable, 'manage.py', 'flush', '--no-input']
    try:
        command.stdout.write("Flushing database...")
        subprocess.run(flush_command, check=True, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    except subprocess.CalledProcessError as e:
        command.stderr.write(command.style.ERROR(f"Failed to flush database.\n    Error: {e.stderr}"))
        return

    for filename in load_order:
        filepath = os.path.join(archive_dir, filename)
        if os.path.exists(filepath):
            command.stdout.write(f"  - Loading {filename}...")
            loaddata_command = [
                python_executable, 'manage.py', 'loaddata', filepath
            ]
            try:
                subprocess.run(loaddata_command, check=True, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
            except subprocess.CalledProcessError as e:
                command.stderr.write(command.style.ERROR(f"    Failed to load {filename}.\n    Error: {e.stderr}"))
                command.stderr.write(command.style.ERROR("Aborting data load."))
                return
        else:
            command.stderr.write(command.style.WARNING(f"    - Could not find {filename} in archive, skipping."))
    
    command.stdout.write(command.style.SUCCESS("\nData loading from archive complete."))
