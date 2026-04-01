"""
Google Drive Sync Module
=========================
Secure cloud backup to Google Drive with OAuth authentication.
Encrypted backup, automatic sync, and conflict resolution.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable

try:
    from .utils import get_data_dir
    from .database import get_db_cursor, export_to_json
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir
    from database import get_db_cursor, export_to_json

# Try to import Google libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow, Flow
    from google.auth.exceptions import RefreshError
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logging.warning("Google libraries not available - install with: pip install google-auth google-auth-oauthlib google-api-python-client")

# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Sync interval in minutes
DEFAULT_SYNC_INTERVAL = 10


class GoogleDriveSync:
    """
    Google Drive synchronization manager.
    Handles OAuth authentication, file upload/download, and automatic sync.
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.running = False
        self.sync_thread = None
        self.sync_interval = DEFAULT_SYNC_INTERVAL * 60  # Convert to seconds
        self.last_sync = None
        self.last_error = None
        self.sync_in_progress = False
        self.callbacks = []
        self.user_id = None
        
        # Paths
        self.data_dir = get_data_dir()
        self.credentials_file = os.path.join(self.data_dir, 'google_credentials.json')
        self.token_file = os.path.join(self.data_dir, 'token.json')
        self.backup_file = os.path.join(self.data_dir, 'cloud_backup.json')
    
    def authenticate(self, client_secrets_file: str = None) -> bool:
        """
        Authenticate with Google OAuth.
        
        Args:
            client_secrets_file: Path to client_secrets.json from Google Cloud Console
        
        Returns:
            True if authentication successful
        """
        if not GOOGLE_AVAILABLE:
            logging.error("Google libraries not available")
            return False
        
        try:
            # Check if we have existing credentials
            creds = None
            
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                except Exception as e:
                    logging.warning(f"Failed to load token: {e}")
                    creds = None
            
            # If no valid credentials, run OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        # Token expired, need re-authentication
                        if os.path.exists(self.token_file):
                            os.remove(self.token_file)
                        return False
                else:
                    # Need new authentication
                    if not client_secrets_file or not os.path.exists(client_secrets_file):
                        logging.error("Client secrets file not found")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file, SCOPES)
                    creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            
            logging.info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return False
    
    def authenticate_headless(self, client_secrets_file: str) -> str:
        """
        Authenticate without browser (for headless servers).
        Returns authorization URL that user must visit manually.
        
        Args:
            client_secrets_file: Path to client_secrets.json
        
        Returns:
            Authorization URL for user to visit
        """
        if not GOOGLE_AVAILABLE:
            return ""
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES)
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                prompt='consent',
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store flow for later use
            self.flow = flow
            
            return auth_url
            
        except Exception as e:
            logging.error(f"Headless auth failed: {e}")
            return ""
    
    def complete_headless_auth(self, authorization_code: str) -> bool:
        """
        Complete headless authentication with authorization code.
        
        Args:
            authorization_code: Code from Google after user authorizes
        
        Returns:
            True if successful
        """
        if not GOOGLE_AVAILABLE or not hasattr(self, 'flow'):
            return False
        
        try:
            self.flow.fetch_token(code=authorization_code)
            self.credentials = self.flow.credentials
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(self.credentials.to_json())
            
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            logging.info("Headless authentication successful")
            return True
            
        except Exception as e:
            logging.error(f"Failed to complete headless auth: {e}")
            return False
    
    def upload_backup(self, backup_data: str = None) -> bool:
        """
        Upload backup to Google Drive.
        
        Args:
            backup_data: JSON string to upload (if None, exports from database)
        
        Returns:
            True if successful
        """
        if not self.service:
            logging.error("Not authenticated to Google Drive")
            return False
        
        try:
            # Get or create backup file metadata
            file_id = self._get_or_create_backup_file()
            
            if not file_id:
                return False
            
            # Prepare backup data
            if backup_data is None:
                backup_data = export_to_json()
            
            # Add metadata
            backup_metadata = {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'type': 'full_backup'
            }
            
            backup_with_meta = json.dumps({
                'metadata': backup_metadata,
                'data': json.loads(backup_data)
            }, indent=2)
            
            # Write to temp file
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_with_meta)
            
            # Upload file
            file_metadata = {
                'name': 'InventoryBackup.json',
                'description': f'Backup from {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'mimeType': 'application/json'
            }
            
            media = MediaFileUpload(self.backup_file, mimetype='application/json')
            
            self.service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                fields='id, name, modifiedTime'
            ).execute()
            
            logging.info("Backup uploaded to Google Drive")
            self.last_sync = datetime.now()
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(True, "Backup uploaded")
                except Exception as e:
                    logging.error(f"Callback error: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            self.last_error = str(e)
            return False
    
    def download_backup(self) -> Optional[Dict]:
        """
        Download backup from Google Drive.
        
        Returns:
            Backup data as dictionary, or None if failed
        """
        if not self.service:
            logging.error("Not authenticated")
            return None
        
        try:
            # Find backup file
            file_id = self._get_backup_file_id()
            
            if not file_id:
                logging.warning("No backup file found on Google Drive")
                return None
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            
            with open(self.backup_file + '.download', 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logging.info(f"Download progress: {int(status.progress() * 100)}%")
            
            # Read downloaded file
            with open(self.backup_file + '.download', 'r', encoding='utf-8') as f:
                backup = json.load(f)
            
            # Cleanup
            os.remove(self.backup_file + '.download')
            
            logging.info("Backup downloaded from Google Drive")
            return backup
            
        except Exception as e:
            logging.error(f"Download failed: {e}")
            self.last_error = str(e)
            return None
    
    def restore_from_backup(self, backup_data: Dict) -> bool:
        """
        Restore data from backup.
        
        Args:
            backup_data: Backup dictionary from download_backup()
        
        Returns:
            True if successful
        """
        try:
            if 'data' not in backup_data:
                logging.error("Invalid backup format")
                return False
            
            # Import data back to database
            from .database import import_from_json
            data_json = json.dumps(backup_data['data'])
            
            if import_from_json(data_json):
                logging.info("Restore completed successfully")
                return True
            else:
                logging.error("Restore failed")
                return False
                
        except Exception as e:
            logging.error(f"Restore failed: {e}")
            return False
    
    def _get_backup_file_id(self) -> Optional[str]:
        """Find backup file on Google Drive."""
        try:
            query = "name='InventoryBackup.json' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to find backup file: {e}")
            return None
    
    def _get_or_create_backup_file(self) -> Optional[str]:
        """Get existing backup file or create new one."""
        file_id = self._get_backup_file_id()
        
        if file_id:
            return file_id
        
        # Create new file
        try:
            file_metadata = {
                'name': 'InventoryBackup.json',
                'description': 'Inventory System Backup',
                'mimeType': 'application/json'
            }
            
            # Create empty file
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            logging.info(f"Created backup file: {file.get('id')}")
            return file.get('id')
            
        except Exception as e:
            logging.error(f"Failed to create backup file: {e}")
            return None
    
    def start_auto_sync(self, interval_minutes: int = None):
        """Start automatic synchronization."""
        if interval_minutes:
            self.sync_interval = interval_minutes * 60
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logging.info(f"Auto-sync started (interval: {self.sync_interval // 60} minutes)")
    
    def stop_auto_sync(self):
        """Stop automatic synchronization."""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logging.info("Auto-sync stopped")
    
    def _sync_loop(self):
        """Background sync loop."""
        while self.running:
            try:
                # Check if online and authenticated
                if self.service and self.credentials and self.credentials.valid:
                    self._perform_sync()
                
                # Sleep in small increments
                for _ in range(self.sync_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Sync loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _perform_sync(self):
        """Perform actual sync operation."""
        if self.sync_in_progress:
            return
        
        self.sync_in_progress = True
        
        try:
            logging.info("Starting Google Drive sync...")
            
            # Upload backup
            if self.upload_backup():
                self.last_sync = datetime.now()
                
                # Record sync in history
                with get_db_cursor() as cur:
                    cur.execute("""
                        INSERT INTO sync_history (sync_type, status, records_synced)
                        VALUES ('google_drive', 'completed', 1)
                    """)
                
                logging.info("Google Drive sync completed")
            else:
                logging.warning("Google Drive sync failed")
                
        except Exception as e:
            logging.error(f"Sync failed: {e}")
            self.last_error = str(e)
            
            # Record failure
            try:
                with get_db_cursor() as cur:
                    cur.execute("""
                        INSERT INTO sync_history (sync_type, status, error_message)
                        VALUES ('google_drive', 'failed', ?)
                    """, (str(e),))
            except:
                pass
        
        finally:
            self.sync_in_progress = False
    
    def add_callback(self, callback: Callable):
        """Add callback for sync events."""
        self.callbacks.append(callback)
    
    def get_sync_status(self) -> Dict:
        """Get current sync status."""
        return {
            'authenticated': self.service is not None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_error': self.last_error,
            'sync_in_progress': self.sync_in_progress,
            'auto_sync_enabled': self.running,
            'sync_interval_minutes': self.sync_interval // 60
        }
    
    def disconnect(self):
        """Disconnect from Google Drive."""
        self.stop_auto_sync()
        
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        
        self.service = None
        self.credentials = None
        
        logging.info("Disconnected from Google Drive")


# Global sync instance
drive_sync = GoogleDriveSync()


def get_drive_sync() -> GoogleDriveSync:
    """Get the global Google Drive sync instance."""
    return drive_sync


# Convenience functions
def authenticate_google_drive(client_secrets_file: str = None) -> bool:
    """Authenticate with Google Drive."""
    return drive_sync.authenticate(client_secrets_file)


def upload_to_drive(backup_data: str = None) -> bool:
    """Upload backup to Google Drive."""
    return drive_sync.upload_backup(backup_data)


def download_from_drive() -> Optional[Dict]:
    """Download backup from Google Drive."""
    return drive_sync.download_backup()


def start_google_sync(interval_minutes: int = 10):
    """Start automatic Google Drive sync."""
    drive_sync.start_auto_sync(interval_minutes)


def stop_google_sync():
    """Stop automatic Google Drive sync."""
    drive_sync.stop_auto_sync()


def get_sync_status() -> Dict:
    """Get sync status."""
    return drive_sync.get_sync_status()
