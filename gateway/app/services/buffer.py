"""
Offline data buffering service using SQLite
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..core.logger import logger
from ..core.config import settings


class DataBuffer:
    """
    SQLite-based buffer for storing data when backend is unavailable
    """

    def __init__(self, db_path: str = None):
        """
        Initialize data buffer

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.BUFFER_DB_PATH

        # Create database directory
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create buffer tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create buffer table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    tag_name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    buffered_at TEXT NOT NULL,
                    sent BOOLEAN DEFAULT 0
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sent
                ON buffer(sent)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device
                ON buffer(device_id)
            ''')

            conn.commit()
            conn.close()

            logger.info(f"Data buffer initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize buffer database: {str(e)}")

    def add(self, device_id: str, tag_id: str, tag_name: str, value: Any, quality: str, timestamp: datetime):
        """
        Add data point to buffer

        Args:
            device_id: Device identifier
            tag_id: Tag identifier
            tag_name: Tag name
            value: Tag value
            quality: Data quality
            timestamp: Data timestamp
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert value to JSON string
            value_str = json.dumps(value)

            cursor.execute('''
                INSERT INTO buffer (device_id, tag_id, tag_name, value, quality, timestamp, buffered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_id,
                tag_id,
                tag_name,
                value_str,
                quality,
                timestamp.isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to add data to buffer: {str(e)}")

    def get_unsent(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get unsent buffered data

        Args:
            limit: Maximum number of records to retrieve

        Returns:
            List of buffered data dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM buffer
                WHERE sent = 0
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            # Convert to dictionaries
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'device_id': row['device_id'],
                    'tag_id': row['tag_id'],
                    'tag_name': row['tag_name'],
                    'value': json.loads(row['value']),
                    'quality': row['quality'],
                    'timestamp': row['timestamp'],
                    'buffered_at': row['buffered_at']
                })

            return results

        except Exception as e:
            logger.error(f"Failed to get unsent buffer data: {str(e)}")
            return []

    def mark_sent(self, record_ids: List[int]):
        """
        Mark records as sent

        Args:
            record_ids: List of record IDs to mark as sent
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f'''
                UPDATE buffer
                SET sent = 1
                WHERE id IN ({placeholders})
            ''', record_ids)

            conn.commit()
            conn.close()

            logger.debug(f"Marked {len(record_ids)} records as sent")

        except Exception as e:
            logger.error(f"Failed to mark records as sent: {str(e)}")

    def delete_sent(self, older_than_days: int = 7):
        """
        Delete old sent records

        Args:
            older_than_days: Delete records older than this many days
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now().replace(microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days)

            cursor.execute('''
                DELETE FROM buffer
                WHERE sent = 1 AND buffered_at < ?
            ''', (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old buffer records")

        except Exception as e:
            logger.error(f"Failed to delete old buffer records: {str(e)}")

    def get_stats(self) -> Dict[str, int]:
        """Get buffer statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM buffer WHERE sent = 0')
            unsent_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM buffer WHERE sent = 1')
            sent_count = cursor.fetchone()[0]

            conn.close()

            return {
                'unsent': unsent_count,
                'sent': sent_count,
                'total': unsent_count + sent_count
            }

        except Exception as e:
            logger.error(f"Failed to get buffer stats: {str(e)}")
            return {'unsent': 0, 'sent': 0, 'total': 0}

    def clear_all(self):
        """Clear all buffer data (use with caution!)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM buffer')
            conn.commit()
            conn.close()

            logger.warning("Buffer cleared completely")

        except Exception as e:
            logger.error(f"Failed to clear buffer: {str(e)}")
