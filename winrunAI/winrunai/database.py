import sqlite3
from pathlib import Path

# In a real app, this might be in a user data directory
DB_FILE = Path(__file__).parent / "knowledge.db"

def initialize_database():
    """
    Initializes the SQLite database and creates the rules table if it doesn't exist.
    Populates the database with some initial rules.
    """
    # For this task, we want to re-initialize to add the new rule.
    # In a real app, you'd use migrations.
    if DB_FILE.exists():
        DB_FILE.unlink()

    print("Initializing new knowledge base...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE rules (
            id INTEGER PRIMARY KEY,
            error_pattern TEXT NOT NULL UNIQUE,
            fix_type TEXT NOT NULL,
            fix_argument TEXT NOT NULL,
            confidence REAL DEFAULT 0.95
        )
    ''')

    # Insert initial rules
    initial_rules = [
        ('d3dx9_43.dll', 'winetricks', 'd3dx9_43'),
        ('d3dcompiler_43.dll', 'winetricks', 'd3dcompiler_43'),
        ('msvcp140.dll', 'winetricks', 'vcrun2019'),
        ('vcruntime140.dll', 'winetricks', 'vcrun2019'),
        ('d3d11.dll', 'winetricks', 'dxvk'),
        ('dxgi.dll', 'winetricks', 'dxvk'),
        ('err:mscoree:LoadLibraryShim error reading registry key for installroot', 'winetricks', 'dotnet40'),
        ('err:ole:CoGetClassObject class', 'winetricks', 'corefonts'),
        # New rule for a registry fix
        ('fixme:d3d:wined3d_select_feature_level', 'regedit', '[HKEY_CURRENT_USER\\Software\\Wine\\Direct3D]\n"MaxVersionGL"=dword:00030002'),
    ]
    cursor.executemany('INSERT INTO rules (error_pattern, fix_type, fix_argument) VALUES (?, ?, ?)', initial_rules)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_FILE}")

def find_fix_for_error(error_string: str):
    """
    Queries the database for a fix based on a substring match in the error string.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT error_pattern, fix_type, fix_argument, confidence FROM rules")
    all_rules = cursor.fetchall()

    conn.close()

    for pattern, fix_type, fix_arg, confidence in all_rules:
        if pattern.lower() in error_string.lower():
            return {
                'pattern': pattern,
                'type': fix_type,
                'argument': fix_arg,
                'confidence': confidence
            }

    return None

if __name__ == '__main__':
    initialize_database()

    test_error = "002c:fixme:d3d:wined3d_select_feature_level software-rendering is not supported"
    fix = find_fix_for_error(test_error)

    if fix:
        print(f"Found a potential fix for '{test_error}':")
        print(f"  -> Action: {fix['type']}")
        print(f"  -> Argument: {fix['argument']}")
        print(f"  -> Confidence: {fix['confidence'] * 100}%")
    else:
        print("No fix found for the test error.")
