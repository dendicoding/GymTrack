import os
import shutil
from datetime import datetime

# Percorso del database originale
DATABASE_PATH = "gym_manager.db"

# Directory di backup
BACKUP_DIR = "backups"

def backup_database():
    # Crea la directory di backup se non esiste
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Nome del file di backup con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")

    # Copia il database nella directory di backup
    try:
        shutil.copy(DATABASE_PATH, backup_file)
        print(f"Backup completato: {backup_file}")
    except Exception as e:
        print(f"Errore durante il backup: {e}")

def cleanup_old_backups(days=30):
    now = datetime.now()
    for file in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, file)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if (now - file_time).days > days:
                os.remove(file_path)
                print(f"Backup eliminato: {file_path}")

if __name__ == "__main__":
    backup_database()
    cleanup_old_backups()