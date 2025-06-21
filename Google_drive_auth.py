# drive_auth.py - Google Drive Authentication Module
import json
import os
from pathlib import Path
from google.colab import userdata
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

class ColabDriveManager:
    def __init__(self):
        self.service = None
        self.project_folder_id = None
        self.project_root = None
        self._authenticate()
        self._setup_project_structure()

    def _authenticate(self):
        """Authenticate using service account credentials from Colab secrets"""
        try:
            # Get service account credentials from Colab secrets
            service_account_info = {
                "type": "service_account",
                "project_id": userdata.get('GOOGLE_PROJECT_ID'),
                "private_key_id": userdata.get('GOOGLE_PRIVATE_KEY_ID'),
                "private_key": userdata.get('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": userdata.get('GOOGLE_CLIENT_EMAIL'),
                "client_id": userdata.get('GOOGLE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{userdata.get('GOOGLE_CLIENT_EMAIL')}"
            }

            # Create credentials
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive']
            )

            # Build the service
            self.service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive API authenticated successfully")
            return True

        except Exception as e:
            print(f"❌ Service account authentication failed: {e}")
            print("🔄 Falling back to traditional Drive mounting...")
            return self._fallback_mount()

    def _fallback_mount(self):
        """Fallback to traditional Google Drive mounting"""
        try:
            from google.colab import drive
            drive.mount('/content/drive')

            # Set up local file system paths
            self.project_root = Path('/content/drive/MyDrive/TradingSystem_Phase1')
            self.project_root.mkdir(exist_ok=True)

            print("✅ Google Drive mounted successfully (fallback mode)")
            return True

        except Exception as e:
            print(f"❌ Drive mounting failed: {e}")
            return False

    def _setup_project_structure(self):
        """Setup project folder structure"""
        if self.service:
            self._setup_api_folders()
        else:
            self._setup_local_folders()

    def _setup_api_folders(self):
        """Setup folder structure using Drive API"""
        try:
            # Find or create main project folder
            folder_name = 'TradingSystem_Phase1'

            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()

            if results['files']:
                self.project_folder_id = results['files'][0]['id']
                print(f"✅ Found existing project folder: {folder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata).execute()
                self.project_folder_id = folder['id']
                print(f"✅ Created project folder: {folder_name}")

            # Create subfolders
            subfolders = ['data', 'models', 'logs', 'config', 'backups', 'reports', 'coordination']
            for subfolder in subfolders:
                self._create_subfolder(subfolder)

        except Exception as e:
            print(f"❌ Error setting up API folders: {e}")

    def _create_subfolder(self, subfolder_name):
        """Create a subfolder in the project directory"""
        try:
            # Check if subfolder exists
            results = self.service.files().list(
                q=f"name='{subfolder_name}' and parents in '{self.project_folder_id}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()

            if not results['files']:
                # Create subfolder
                folder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.project_folder_id]
                }
                self.service.files().create(body=folder_metadata).execute()
                print(f"   📁 Created subfolder: {subfolder_name}")

        except Exception as e:
            print(f"   ⚠️ Error creating subfolder {subfolder_name}: {e}")

    def _setup_local_folders(self):
        """Setup folder structure using local file system"""
        if self.project_root:
            subfolders = ['data', 'models', 'logs', 'config', 'backups', 'reports', 'coordination']
            for subfolder in subfolders:
                (self.project_root / subfolder).mkdir(exist_ok=True)
            print("✅ Local project structure created")

    def get_project_path(self, subfolder: str = None) -> Path:
        """Get path to project or subfolder"""
        if self.project_root:
            # Local file system mode
            if subfolder:
                return self.project_root / subfolder
            return self.project_root
        else:
            # API mode - return a simulated path for compatibility
            if subfolder:
                return Path(f"/drive_api/TradingSystem_Phase1/{subfolder}")
            return Path("/drive_api/TradingSystem_Phase1")

    def get_database_path(self) -> str:
        """Get the database path"""
        if self.service:
            # For API mode, we'll use a local temp file that syncs with Drive
            return "/tmp/trading.db"
        else:
            return str(self.project_root / "data" / "trading.db")

# Global instance for easy importing
drive_manager = None

def get_drive_manager():
    """Get or create global drive manager instance"""
    global drive_manager
    if drive_manager is None:
        drive_manager = ColabDriveManager()
    return drive_manager

def init_drive_connection():
    """Initialize drive connection - call this in each notebook"""
    return get_drive_manager()

# Convenience functions for easy use
def get_project_path(subfolder: str = None):
    """Get project path"""
    return get_drive_manager().get_project_path(subfolder)

def save_json(filename: str, data: dict, subfolder: str = None):
    """Save JSON data to drive"""
    dm = get_drive_manager()
    if dm.project_root:
        # Local file system mode
        if subfolder:
            path = dm.project_root / subfolder / filename
        else:
            path = dm.project_root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    return False

def load_json(filename: str, subfolder: str = None):
    """Load JSON data from drive"""
    dm = get_drive_manager()
    if dm.project_root:
        # Local file system mode
        if subfolder:
            path = dm.project_root / subfolder / filename
        else:
            path = dm.project_root / filename
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    return None

def get_database_path():
    """Get database path"""
    return get_drive_manager().get_database_path()

print("✅ Drive Authentication Module loaded")
print("💡 Usage: drive_manager = init_drive_connection()")
