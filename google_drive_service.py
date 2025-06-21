#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: google_drive_service.py
Version: 1.0.1
Last Updated: 2025-01-11

REVISION HISTORY:
- v1.0.1 (2025-01-11) - Refactored to remove fallback, conform to project methodology
- v1.0.0 (2024-12-28) - Initial version with fallback support

PURPOSE:
Provides unified Google Drive access for Trading System services.
Used by TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py and enhanced_startup_manager.py.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
from google.colab import userdata
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload

class GoogleDriveService:
    """
    Unified Google Drive service for Trading System.
    Provides API access to Google Drive without fallback mechanisms.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize Google Drive service"""
        self.service = None
        self.project_folder_id = None
        self.logger = logger or self._setup_default_logger()
        
        # Project configuration
        self.project_name = "TradingSystem_Phase1"
        self.subfolders = [
            'data', 'models', 'logs', 'config', 
            'backups', 'reports', 'coordination', 
            'project_documentation', 'updates'
        ]
        
        # Initialize service
        self._authenticate()
        self._setup_project_structure()
    
    def _setup_default_logger(self) -> logging.Logger:
        """Setup default logger if none provided"""
        logger = logging.getLogger('GoogleDriveService')
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _authenticate(self):
        """Authenticate using service account credentials from Colab secrets"""
        try:
            # Build service account info from Colab secrets
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
            
            # Validate required fields
            required_fields = ['project_id', 'private_key', 'client_email', 'client_id']
            for field in required_fields:
                if not service_account_info.get(field):
                    raise ValueError(f"Missing required field: GOOGLE_{field.upper()}")
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Build the service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Test authentication
            self.service.about().get(fields="user").execute()
            
            self.logger.info("✅ Google Drive API authenticated successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Google Drive authentication failed: {e}")
            raise RuntimeError(f"Failed to authenticate with Google Drive: {e}")
    
    def _setup_project_structure(self):
        """Setup project folder structure in Google Drive"""
        try:
            # Find or create main project folder
            self.project_folder_id = self._find_or_create_folder(
                self.project_name, 
                parent_id=None
            )
            self.logger.info(f"✅ Project folder ready: {self.project_name}")
            
            # Create subfolders
            for subfolder in self.subfolders:
                self._find_or_create_folder(subfolder, self.project_folder_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error setting up project structure: {e}")
            raise
    
    def _find_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Find existing folder or create new one"""
        try:
            # Build query
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and parents in '{parent_id}'"
            query += " and trashed=false"
            
            # Search for existing folder
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=1
            ).execute()
            
            if results.get('files'):
                folder_id = results['files'][0]['id']
                self.logger.debug(f"   📁 Found existing folder: {folder_name}")
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                folder_metadata['parents'] = [parent_id]
                
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            self.logger.info(f"   📁 Created folder: {folder_name}")
            return folder['id']
            
        except Exception as e:
            self.logger.error(f"Error with folder {folder_name}: {e}")
            raise
    
    def get_subfolder_id(self, subfolder: str) -> str:
        """Get the ID of a subfolder"""
        if not self.project_folder_id:
            raise RuntimeError("Project folder not initialized")
            
        return self._find_or_create_folder(subfolder, self.project_folder_id)
    
    def list_files(self, folder_name: Optional[str] = None, mime_type: Optional[str] = None) -> List[Dict]:
        """List files in a folder"""
        try:
            # Determine parent folder
            if folder_name:
                parent_id = self.get_subfolder_id(folder_name)
            else:
                parent_id = self.project_folder_id
            
            # Build query
            query = f"parents in '{parent_id}' and trashed=false"
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            # Get files
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, size)",
                orderBy="modifiedTime desc"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            self.logger.error(f"Error listing files: {e}")
            return []
    
    def read_file(self, filename: str, subfolder: Optional[str] = None) -> bytes:
        """Read file content from Google Drive"""
        try:
            # Find the file
            file_id = self._find_file(filename, subfolder)
            if not file_id:
                raise FileNotFoundError(f"File not found: {filename}")
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
            file_content.seek(0)
            return file_content.read()
            
        except Exception as e:
            self.logger.error(f"Error reading file {filename}: {e}")
            raise
    
    def write_file(self, filename: str, content: bytes, subfolder: Optional[str] = None, 
                   mime_type: str = 'application/octet-stream') -> str:
        """Write file to Google Drive"""
        try:
            # Get parent folder
            if subfolder:
                parent_id = self.get_subfolder_id(subfolder)
            else:
                parent_id = self.project_folder_id
            
            # Check if file exists
            existing_file_id = self._find_file(filename, subfolder)
            
            # Prepare content
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mime_type,
                resumable=True
            )
            
            if existing_file_id:
                # Update existing file
                file_metadata = {'name': filename}
                updated_file = self.service.files().update(
                    fileId=existing_file_id,
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                self.logger.info(f"Updated file: {filename}")
                return updated_file['id']
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'parents': [parent_id]
                }
                created_file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                self.logger.info(f"Created file: {filename}")
                return created_file['id']
                
        except Exception as e:
            self.logger.error(f"Error writing file {filename}: {e}")
            raise
    
    def _find_file(self, filename: str, subfolder: Optional[str] = None) -> Optional[str]:
        """Find file ID by name"""
        try:
            # Get parent folder
            if subfolder:
                parent_id = self.get_subfolder_id(subfolder)
            else:
                parent_id = self.project_folder_id
            
            # Search for file
            query = f"name='{filename}' and parents in '{parent_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id)",
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
            
        except Exception as e:
            self.logger.error(f"Error finding file {filename}: {e}")
            return None
    
    def delete_file(self, filename: str, subfolder: Optional[str] = None) -> bool:
        """Delete a file from Google Drive"""
        try:
            file_id = self._find_file(filename, subfolder)
            if not file_id:
                self.logger.warning(f"File not found for deletion: {filename}")
                return False
            
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info(f"Deleted file: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting file {filename}: {e}")
            return False
    
    def create_backup(self, source_folder: str, backup_name: str) -> str:
        """Create a backup of a folder"""
        try:
            # Create backup folder
            backup_folder_id = self._find_or_create_folder(
                backup_name, 
                self.get_subfolder_id('backups')
            )
            
            # Get source folder contents
            source_files = self.list_files(source_folder)
            
            # Copy files to backup
            for file_info in source_files:
                if file_info['mimeType'] != 'application/vnd.google-apps.folder':
                    # Copy file
                    copy_metadata = {
                        'name': file_info['name'],
                        'parents': [backup_folder_id]
                    }
                    self.service.files().copy(
                        fileId=file_info['id'],
                        body=copy_metadata
                    ).execute()
                    
            self.logger.info(f"Created backup: {backup_name}")
            return backup_folder_id
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    # Convenience methods for JSON operations
    def save_json(self, filename: str, data: Dict, subfolder: Optional[str] = None) -> bool:
        """Save JSON data to Google Drive"""
        try:
            json_content = json.dumps(data, indent=2, default=str)
            self.write_file(
                filename, 
                json_content.encode('utf-8'), 
                subfolder,
                mime_type='application/json'
            )
            return True
        except Exception as e:
            self.logger.error(f"Error saving JSON {filename}: {e}")
            return False
    
    def load_json(self, filename: str, subfolder: Optional[str] = None) -> Optional[Dict]:
        """Load JSON data from Google Drive"""
        try:
            content = self.read_file(filename, subfolder)
            return json.loads(content.decode('utf-8'))
        except FileNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error loading JSON {filename}: {e}")
            return None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database file"""
        try:
            db_info = {
                'exists': False,
                'size': 0,
                'last_modified': None,
                'file_id': None
            }
            
            file_id = self._find_file('trading.db', 'data')
            if file_id:
                # Get file metadata
                file_meta = self.service.files().get(
                    fileId=file_id,
                    fields='size,modifiedTime'
                ).execute()
                
                db_info.update({
                    'exists': True,
                    'size': int(file_meta.get('size', 0)),
                    'last_modified': file_meta.get('modifiedTime'),
                    'file_id': file_id
                })
                
            return db_info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return {'exists': False, 'error': str(e)}


# Global instance management
_drive_service_instance = None

def get_drive_service(logger: Optional[logging.Logger] = None) -> GoogleDriveService:
    """Get or create global drive service instance"""
    global _drive_service_instance
    if _drive_service_instance is None:
        _drive_service_instance = GoogleDriveService(logger)
    return _drive_service_instance

def init_drive_service(logger: Optional[logging.Logger] = None) -> GoogleDriveService:
    """Initialize drive service - call this in each notebook/script"""
    return get_drive_service(logger)

# Legacy compatibility functions
def get_project_path(subfolder: Optional[str] = None) -> str:
    """Legacy: Get virtual project path for compatibility"""
    base = f"/drive_api/{get_drive_service().project_name}"
    return f"{base}/{subfolder}" if subfolder else base

def get_database_path() -> str:
    """Legacy: Get virtual database path for compatibility"""
    return f"/drive_api/{get_drive_service().project_name}/data/trading.db"

# Direct export for convenience
save_json = lambda filename, data, subfolder=None: get_drive_service().save_json(filename, data, subfolder)
load_json = lambda filename, subfolder=None: get_drive_service().load_json(filename, subfolder)

if __name__ == "__main__":
    # Test the service
    print("🚀 Google Drive Service v1.0.1")
    print("================================")
    
    try:
        service = init_drive_service()
        print("✅ Service initialized successfully")
        
        # Test listing files
        print("\n📁 Project structure:")
        for folder in service.subfolders:
            files = service.list_files(folder)
            print(f"   {folder}/: {len(files)} files")
            
    except Exception as e:
        print(f"❌ Error: {e}")
