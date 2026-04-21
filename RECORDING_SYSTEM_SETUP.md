# ZEDU Recording System Setup Guide

## Overview

The ZEDU Recording System allows instructors to:
- Record live Google Meet sessions
- Upload recordings directly to the ZEDU platform
- Store recordings locally or in cloud storage
- Share recordings with students
- Track recording views and engagement

## Architecture

### Components

1. **Backend (Flask)**
   - Recording management endpoints
   - Database integration for recording metadata
   - File upload/download handling
   - Google Drive API integration

2. **Database (PostgreSQL)**
   - `recorded_lessons` table: Stores recording metadata
   - `live_sessions` table: Tracks session and recording status

3. **Frontend (HTML/JavaScript)**
   - Recording upload form
   - Recording player
   - Recording list view
   - Delete functionality

4. **File Storage**
   - Local storage: `/recordings/videos/` and `/recordings/thumbnails/`
   - Cloud storage: Google Drive, AWS S3, etc. (via URLs)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `google-auth-oauthlib==1.2.0` - Google OAuth authentication
- `google-auth-httplib2==0.2.0` - HTTP transport for Google API
- `google-api-python-client==2.108.0` - Google Drive API client
- `requests==2.31.0` - HTTP requests library

### 2. Create Local Storage Directories

```bash
mkdir -p recordings/videos
mkdir -p recordings/thumbnails
```

### 3. Google Drive Integration (Optional)

To enable automatic recording fetching from Google Drive:

1. **Create a Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Drive API
   - Create a Service Account
   - Download JSON credentials file

2. **Save Credentials:**
   - Save the JSON file as `credentials.json` in the project root
   - Grant the service account access to your Google Drive folder

3. **Initialize Google Drive Manager:**
   ```python
   from google_drive_integration import GoogleDriveManager
   
   drive_manager = GoogleDriveManager('./credentials.json')
   recordings = drive_manager.find_meeting_recordings('instructor@example.com')
   ```

### 4. Database Setup

The recording tables are automatically created when the app starts. They include:

**recorded_lessons table:**
```sql
CREATE TABLE IF NOT EXISTS recorded_lessons (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    instructor_id INTEGER NOT NULL,
    session_id INTEGER,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    duration_seconds INTEGER,
    file_size INTEGER,
    views INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE SET NULL
);
```

**live_sessions table (updated):**
- New column: `is_recorded BOOLEAN DEFAULT FALSE`

## Usage

### For Instructors

1. **Schedule Live Session**
   - Go to Instructor Dashboard
   - Click "Start Live Session"
   - Google Meet room is automatically created

2. **Record Session**
   - Use Google Meet's built-in record button
   - Or use external recording tool

3. **Upload Recording**
   - After session ends, go to session page
   - Scroll to "Recordings" section
   - Click "Upload Recording"
   - Fill in:
     - **Recording Title**: Descriptive name for the recording
     - **Recording URL**: Link to video file (local or cloud)
     - **Description**: Optional details
     - **Duration**: Video length in seconds (optional)
     - **File Size**: Size in MB (optional)
   - Click "Upload Recording"

4. **Manage Recordings**
   - View all recordings for a session
   - Click "Watch" to open recording
   - Click "Delete" to remove recording

### For Students

1. **Access Recordings**
   - View course materials/sessions
   - Click on recording to play
   - Watch counter increments

2. **Video Playback**
   - Opens in new window
   - Full video player controls

## API Endpoints

### Recording Management

**Upload Recording**
```
POST /api/session/<session_id>/upload-recording
Content-Type: application/json

{
    "title": "Lecture Recording",
    "video_url": "https://...",
    "description": "Optional description",
    "duration_seconds": 3600,
    "file_size": 500,
    "thumbnail_url": "https://..."
}

Response: {
    "success": true,
    "lesson": {
        "id": 123,
        "title": "Lecture Recording",
        "video_url": "https://...",
        "created_at": "2024-04-21T10:00:00"
    }
}
```

**Get Session Recordings**
```
GET /api/session/<session_id>/recordings

Response: {
    "success": true,
    "recordings": [
        {
            "id": 1,
            "title": "Recording Title",
            "description": "...",
            "video_url": "...",
            "thumbnail_url": "...",
            "duration_seconds": 3600,
            "views": 25,
            "created_at": "2024-04-21T10:00:00"
        }
    ]
}
```

**Get Recording Details**
```
GET /api/recording/<lesson_id>

Response: {
    "success": true,
    "recording": {
        "id": 1,
        "title": "Recording Title",
        "video_url": "...",
        "duration_seconds": 3600,
        "views": 26,  // incremented
        ...
    }
}
```

**Delete Recording**
```
DELETE /api/recording/<lesson_id>

Response: {
    "success": true,
    "message": "Recording deleted successfully",
    "video_url": "..."
}
```

**Get Course Lessons**
```
GET /api/course/<course_id>/lessons

Response: {
    "success": true,
    "lessons": [...]
}
```

## Recording URL Options

Supported recording URL formats:

### 1. Local Storage
```
/recordings/videos/recording_123.mp4
```

### 2. Google Drive
```
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
https://drive.google.com/uc?id=FILE_ID&export=download
```

### 3. Cloud Storage (AWS S3)
```
https://mybucket.s3.amazonaws.com/recording_123.mp4
https://mybucket.s3.region.amazonaws.com/recording_123.mp4?AWSAccessKeyId=...&Expires=...
```

### 4. Other Cloud Services
```
https://storage.googleapis.com/bucket/recording.mp4  (Google Cloud Storage)
https://blob.azure.com/container/recording.mp4        (Azure Blob Storage)
https://example-cdn.com/recording.mp4                  (Any CDN or web server)
```

## Video Format Support

- **Recommended**: MP4 (H.264 video, AAC audio)
- **Supported**: WebM, OGG, MOV, MKV
- **Maximum size**: Server-dependent (default: 2GB)
- **Recommended bitrate**: 1-5 Mbps for optimal quality/size

## Database Queries

### Get recordings for a course
```sql
SELECT * FROM recorded_lessons 
WHERE course_id = ? AND is_published = TRUE 
ORDER BY created_at DESC;
```

### Get instructor's recordings
```sql
SELECT * FROM recorded_lessons 
WHERE instructor_id = ? 
ORDER BY created_at DESC;
```

### Get top viewed recordings
```sql
SELECT * FROM recorded_lessons 
WHERE course_id = ? 
ORDER BY views DESC 
LIMIT 10;
```

### Mark session as recorded
```sql
UPDATE live_sessions 
SET is_recorded = TRUE 
WHERE id = ?;
```

## File Storage Management

### Clean up old recordings
```python
import os
from datetime import datetime, timedelta

def cleanup_old_recordings(days=30):
    """Delete recordings older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    recordings_dir = './recordings/videos'
    
    for file in os.listdir(recordings_dir):
        filepath = os.path.join(recordings_dir, file)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getctime(filepath))
            if file_time < cutoff:
                os.remove(filepath)
                print(f"Deleted: {file}")
```

### Get storage usage
```python
import os

def get_storage_usage(directory='./recordings'):
    """Calculate total size of recordings"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)  # Convert to MB
```

## Troubleshooting

### Issue: "Recording upload fails with 413 error"
**Solution**: Increase Flask max request size
```python
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB
```

### Issue: "Video won't play"
**Possible causes:**
- URL is incorrect or unreachable
- Video format not supported
- Cross-origin issues (CORS headers needed)

**Solution:**
- Verify URL is accessible in browser
- Convert video to MP4 format
- Ensure CORS headers allow video access

### Issue: "Recordings not showing up"
**Possible causes:**
- `is_published` is FALSE in database
- Recording URL is invalid
- Database query error

**Solution:**
```sql
UPDATE recorded_lessons SET is_published = TRUE WHERE id = ?;
```

### Issue: "Google Drive API not working"
**Possible causes:**
- Credentials file not found
- Service account lacks permissions
- API not enabled in Google Cloud Console

**Solution:**
1. Verify `credentials.json` exists in project root
2. Grant service account access to recording folder
3. Enable Google Drive API in Google Cloud Console

## Performance Optimization

1. **Video Encoding**
   - Use H.264 codec for compatibility
   - 1080p resolution for quality
   - 2-3 Mbps bitrate for balance

2. **Thumbnails**
   - Generate thumbnails at 320x180px
   - Store as JPG for compression

3. **Streaming**
   - Use HTTP range requests for fast seeking
   - Implement progressive download
   - Consider CDN for distributed access

4. **Database**
   - Index on `course_id`, `instructor_id`, `session_id`
   - Paginate large recording lists
   - Cache popular recordings

## Security Considerations

1. **Access Control**
   - Only instructors can upload/delete recordings
   - Students can only view course recordings
   - Implement enrollment checks

2. **URL Validation**
   - Validate URLs before storing
   - Use allowlist for trusted domains
   - Prevent malicious URL injection

3. **File Handling**
   - Scan uploaded files for malware
   - Validate MIME types
   - Store outside web root

4. **Privacy**
   - Encrypt URLs in database
   - Implement access logging
   - Support GDPR data deletion

## Future Enhancements

- [ ] Automatic transcription with timestamps
- [ ] Recording chapters/bookmarks
- [ ] Playback speed control
- [ ] Video quality selection
- [ ] Closed captions support
- [ ] Analytics dashboard
- [ ] Live recording status
- [ ] Automatic YouTube upload
- [ ] Recording streaming (HLS/DASH)
- [ ] Recording editing tools
