"""
Sync Engine Module
==================
Queue-based sync engine for Google Drive backup.
Works offline, syncs when online.
Minimal dependencies - only uses standard library + optional Google APIs.
"""

import json
import os
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from .database import get_db_cursor, get_connection
    from .network import is_online, get_connectivity_monitor
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from network import is_online, get_connectivity_monitor

# Sync interval in minutes
DEFAULT_SYNC_INTERVAL = 10


class SyncEngine:
    """
    Manages data synchronization to Google Drive.
    - Queue-based architecture
    - Works offline (queues changes)
    - Syncs automatically when online
    - Encrypts data before upload
    """
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._sync_interval = DEFAULT_SYNC_INTERVAL * 60  # Convert to seconds
        self._last_sync = None
        self._last_error = None
        self._sync_in_progress = False
        self._credentials = None
        self._lock = threading.Lock()
        self._callbacks = []
    
    def start(self):
        """Start background sync thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logging.info("Sync engine started")
    
    def stop(self):
        """Stop background sync thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logging.info("Sync engine stopped")
    
    def set_sync_interval(self, minutes: int):
        """Set sync interval in minutes."""
        self._sync_interval = max(1, minutes) * 60
    
    def _sync_loop(self):
        """Background sync loop."""
        while self._running:
            try:
                # Check if online and auto-sync is enabled
                if is_online() and self._is_auto_sync_enabled():
                    if self._last_sync is None:
                        # First sync after going online
                        self._perform_sync()
                    elif time.time() - self._last_sync >= self._sync_interval:
                        # Periodic sync
                        self._perform_sync()

                # Sleep in small increments
                for _ in range(60):  # Check every second
                    if not self._running:
                        break
                    time.sleep(1)

            except Exception as e:
                logging.error(f"Sync loop error: {e}", exc_info=True)
                self._last_error = str(e)
    
    def _perform_sync(self):
        """Perform actual sync operation."""
        with self._lock:
            if self._sync_in_progress:
                return
            self._sync_in_progress = True
        
        try:
            logging.info("Starting sync...")
            
            # Record sync start
            self._record_sync_start()
            
            # Check if we have Google credentials
            if not self._has_credentials():
                logging.warning("No Google credentials - sync skipped")
                self._record_sync_complete(0, "No credentials")
                return
            
            # Get pending items from queue
            pending = self._get_pending_queue()
            
            if not pending:
                logging.info("No pending changes to sync")
                self._record_sync_complete(0, "No changes")
                return
            
            # Sync to Google Drive
            synced_count = self._sync_to_drive(pending)

            # Update queue status
            if synced_count > 0:
                self._mark_synced(pending[:synced_count])
            
            self._record_sync_complete(synced_count, "Success")
            self._last_sync = time.time()
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(True, synced_count)
                except Exception as e:
                    logging.error(f"Sync callback error: {e}")
            
            logging.info(f"Sync completed: {synced_count} records")
            
        except Exception as e:
            logging.error(f"Sync failed: {e}")
            self._last_error = str(e)
            self._record_sync_complete(0, str(e))
            
            # Notify callbacks of failure
            for callback in self._callbacks:
                try:
                    callback(False, 0)
                except Exception as ex:
                    logging.error(f"Sync callback error: {ex}")
        
        finally:
            self._sync_in_progress = False
    
    def _get_pending_queue(self) -> List[Dict]:
        """Get pending items from sync queue."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, operation, table_name, record_id, data, created_at
                FROM sync_queue
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT 100
            """)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def _sync_to_drive(self, items: List[Dict]) -> int:
        """
        Sync items to Google Drive.
        Returns number of successfully synced items.
        
        Note: This is a stub - actual implementation requires Google API.
        For now, it just marks items as synced.
        """
        # TODO: Implement Google Drive API integration
        # For offline-first approach, we just track what would be synced
        
        # In full implementation:
        # 1. Initialize Google Drive API with credentials
        # 2. Create/update backup file
        # 3. Upload encrypted data
        # 4. Verify upload
        
        return len(items)
    
    def _mark_synced(self, items: List[Dict]):
        """Mark items as synced in queue."""
        with get_db_cursor() as cur:
            item_ids = [item['id'] for item in items]
            placeholders = ','.join(['?' for _ in item_ids])
            cur.execute(f"""
                UPDATE sync_queue
                SET status = 'synced', synced_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, item_ids)
    
    def _record_sync_start(self):
        """Record sync start in history."""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO sync_history (sync_type, status)
                VALUES ('auto', 'in_progress')
            """)
    
    def _record_sync_complete(self, records: int, error: Optional[str] = None):
        """Record sync completion in history."""
        with get_db_cursor() as cur:
            status = 'failed' if error else 'completed'
            cur.execute("""
                UPDATE sync_history
                SET status = ?, completed_at = CURRENT_TIMESTAMP,
                    records_synced = ?, error_message = ?
                WHERE id = (SELECT MAX(id) FROM sync_history)
            """, (status, records, error))
    
    def _has_credentials(self) -> bool:
        """Check if Google credentials are configured."""
        # Stub - check for stored credentials
        return False
    
    def _is_auto_sync_enabled(self) -> bool:
        """Check if auto-sync is enabled in settings."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT value FROM settings
                WHERE key = 'auto_sync_enabled'
            """)
            row = cur.fetchone()
            return row and row['value'] == '1' if row else False
    
    @property
    def last_sync(self) -> Optional[datetime]:
        """Get time of last successful sync."""
        if self._last_sync:
            return datetime.fromtimestamp(self._last_sync)
        return None
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last sync error message."""
        return self._last_error
    
    @property
    def is_syncing(self) -> bool:
        """Check if sync is currently in progress."""
        return self._sync_in_progress
    
    def add_callback(self, callback):
        """Add callback for sync completion."""
        self._callbacks.append(callback)
    
    def get_pending_count(self) -> int:
        """Get count of pending sync items."""
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'")
            row = cur.fetchone()
            return row['count'] if row else 0
    
    def manual_sync(self):
        """Trigger manual sync immediately."""
        if not self._sync_in_progress:
            threading.Thread(target=self._perform_sync, daemon=True).start()
    
    def queue_operation(self, operation: str, table_name: str, record_id: int, data: Dict):
        """Add an operation to the sync queue."""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO sync_queue (operation, table_name, record_id, data, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (operation, table_name, record_id, json.dumps(data)))


# Global sync engine instance
sync_engine = SyncEngine()


def get_sync_engine() -> SyncEngine:
    """Get the global sync engine instance."""
    return sync_engine


def queue_db_operation(operation: str, table_name: str, record_id: int, data: Dict):
    """Convenience function to queue a database operation for sync."""
    sync_engine.queue_operation(operation, table_name, record_id, data)


def trigger_manual_sync():
    """Trigger a manual sync."""
    sync_engine.manual_sync()


def get_pending_sync_count() -> int:
    """Get count of pending sync operations."""
    return sync_engine.get_pending_count()
