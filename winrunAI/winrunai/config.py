import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.yml"

DEFAULT_CONFIG = {
    'ai_engine': {
        'auto_apply_confidence_threshold': 0.9,
    },
    'service': {
        'scan_interval': 5,
    }
}

def get_config():
    """
    Loads the configuration from config.yml.
    If the file doesn't exist, it returns the default configuration.
    """
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except (yaml.YAMLError, IOError) as e:
        print(f"Warning: Could not load or parse config.yml: {e}")
        print("Using default configuration.")
        return DEFAULT_CONFIG

# Load config once at startup
config = get_config()

if __name__ == '__main__':
    # Example usage
    print("Loading WinRunAI configuration...")
    conf = get_config()

    print("\nAI Engine Settings:")
    print(f"  Auto-apply threshold: {conf.get('ai_engine', {}).get('auto_apply_confidence_threshold')}")

    print("\nService Settings:")
    print(f"  Scan interval: {conf.get('service', {}).get('scan_interval')} seconds")
