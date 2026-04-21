"""
Google Drive Integration Module for Recording Management
Handles fetching, uploading, and storing Google Meet recordings from Google Drive
"""

import os
import requests
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logger = logging.getLogger(__name__)

# Google API Scopes for Drive
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveManager:
    """
    Manages Google Drive API interactions for recordings
    Requires a service account JSON credentials file
    """
    
    def __init__(self, credentials_path=None):
        """
        Initialize Google Drive manager with service account credentials
        
        Args:
            credentials_path: Path to service account JSON credentials file
                             Default: ./credentials.json
        """
        self.credentials_path = credentials_path or './credentials.json'
        self.service = None
        self.initialize_service()
    
    def initialize_service(self):
        """Initialize Google Drive API service"""
        try:
            if not os.path.exists(self.credentials_path):
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                logger.info("To enable Google Drive integration:")
                logger.info("1. Create a service account in Google Cloud Console")
                logger.info("2. Download the JSON credentials file")
                logger.info("3. Save as credentials.json in project root")
                return False
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=GOOGLE_SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            return False
    
    def find_meeting_recordings(self, instructor_email, search_query="recording"):
        """
        Find Google Meet recordings in instructor's Google Drive
        
        Args:
            instructor_email: Email of the instructor
            search_query: Search term for finding recordings
            
        Returns:
            List of file objects matching search criteria
        """
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            # Search for files matching the query
            query = f"name contains '{search_query}' and trashed = false and mimeType = 'video/mp4'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, size, mimeType, webViewLink, webContentLink)',
                pageSize=50,
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} recordings for {instructor_email}")
            return files
        except Exception as e:
            logger.error(f"Error finding recordings: {e}")
            return []
    
    def download_recording(self, file_id, output_path):
        """
        Download a recording from Google Drive
        
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Google Drive service not initialized")
            return False
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, size, createdTime'
            ).execute()
            
            # Download the file
            request = self.service.files().get_media(fileId=file_id)
            
            with open(output_path, 'wb') as f:
                downloader = MediaFileUpload(output_path, resumable=True)
                # Actually use basic download
                response = request.execute()
                f.write(response)
            
            logger.info(f"Successfully downloaded recording: {file_metadata['name']}")
            return True
        except Exception as e:
            logger.error(f"Error downloading recording: {e}")
            return False
    
    def upload_recording_metadata(self, file_path, folder_id=None):
        """
        Upload file to Google Drive and get metadata
        
        Args:
            file_path: Path to local video file
            folder_id: Optional Google Drive folder ID
            
        Returns:
            Dictionary with file metadata if successful
        """
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            file_metadata = {
                'name': file_name,
                'mimeType': 'video/mp4'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, createdTime, size, webViewLink, webContentLink',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"Successfully uploaded recording: {file['name']}")
            return {
                'file_id': file.get('id'),
                'name': file.get('name'),
                'size': file_size,
                'created_time': file.get('createdTime'),
                'view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
        except Exception as e:
            logger.error(f"Error uploading recording: {e}")
            return None


def get_recording_duration(file_path):
    """
    Get duration of a video file using ffprobe
    Requires ffmpeg-python package
    
    Args:
        file_path: Path to video file
        
    Returns:
        Duration in seconds, or None if error
    """
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1:novalue=1', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get video duration: {e}")
        return None


def generate_recording_thumbnail(video_path, output_path, time_offset=5):
    """
    Generate a thumbnail from video file
    Requires ffmpeg
    
    Args:
        video_path: Path to video file
        output_path: Path to save thumbnail
        time_offset: Seconds into video to capture (default: 5s)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess
        subprocess.run(
            ['ffmpeg', '-i', video_path, '-ss', str(time_offset),
             '-vframes', '1', '-vf', 'scale=320:180', output_path],
            capture_output=True,
            timeout=30
        )
        return os.path.exists(output_path)
    except Exception as e:
        logger.warning(f"Could not generate thumbnail: {e}")
        return False


# Recording Storage Helper Functions

def ensure_recordings_directory():
    """Ensure recordings directory exists"""
    os.makedirs('./recordings', exist_ok=True)
    os.makedirs('./recordings/videos', exist_ok=True)
    os.makedirs('./recordings/thumbnails', exist_ok=True)


def get_local_storage_path(recording_id, extension='mp4'):
    """Get local storage path for a recording"""
    return f'./recordings/videos/recording_{recording_id}.{extension}'


def get_thumbnail_path(recording_id):
    """Get thumbnail storage path"""
    return f'./recordings/thumbnails/thumb_{recording_id}.jpg'


def cleanup_recording_file(file_path):
    """Delete a local recording file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted recording file: {file_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
    return False
