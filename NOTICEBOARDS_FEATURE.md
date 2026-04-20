# ZEDU Noticeboard Feature Documentation

## Overview
The Noticeboard feature enables admins and tutors to share important announcements and notices with their institutions and students. Students can view all noticeboards they have access to and stay informed about updates from their tutors and institutions.

## Feature Components

### 1. **Database Tables**

#### `noticeboards` table
Stores noticeboard information:
```sql
CREATE TABLE noticeboards (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    owner_type VARCHAR(50) CHECK (owner_type IN ('tutor', 'admin')),
    institution_id INTEGER,
    course_id INTEGER,
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (institution_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

#### `noticeboard_posts` table
Stores individual posts on noticeboards:
```sql
CREATE TABLE noticeboard_posts (
    id SERIAL PRIMARY KEY,
    noticeboard_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    attachment_url VARCHAR(500),
    views INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (noticeboard_id) REFERENCES noticeboards(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
);
```

### 2. **Backend Functions** (db_helper.py)

#### Noticeboard Management
- `create_noticeboard(title, description, owner_id, owner_type, institution_id, course_id)` - Create new noticeboard
- `get_tutor_noticeboards(tutor_id)` - Get all noticeboards for a tutor
- `get_admin_noticeboards(admin_id)` - Get all noticeboards for an admin
- `get_noticeboard_details(noticeboard_id)` - Get detailed information about a noticeboard

#### Post Management
- `create_noticeboard_post(noticeboard_id, author_id, title, content, priority, attachment_url)` - Create post
- `get_noticeboard_posts(noticeboard_id, limit)` - Get all posts from a noticeboard
- `update_post_views(post_id)` - Increment view count
- `pin_noticeboard_post(post_id, noticeboard_id)` - Pin important post to top
- `unpin_noticeboard_post(post_id, noticeboard_id)` - Unpin post
- `delete_noticeboard_post(post_id, noticeboard_id)` - Delete post

#### Access Control
- `get_student_noticeboards(student_id)` - Get all noticeboards accessible to a student

### 3. **API Endpoints** (app.py)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/noticeboards/create` | Create new noticeboard | Tutor, Admin |
| GET | `/api/noticeboards/tutor/<id>` | Get tutor's noticeboards | Public |
| GET | `/api/noticeboards/admin/<id>` | Get admin's noticeboards | Public |
| GET | `/api/noticeboards/student/my-noticeboards` | Get student's accessible noticeboards | Student |
| GET | `/api/noticeboards/<id>` | Get noticeboard details & posts | Public |
| POST | `/api/noticeboards/<id>/post` | Create post on noticeboard | Tutor, Admin, Student |
| POST | `/api/noticeboards/posts/<id>/view` | Record post view | Public |
| POST | `/api/noticeboards/<id>/posts/<id>/pin` | Pin post | Noticeboard owner |
| POST | `/api/noticeboards/<id>/posts/<id>/unpin` | Unpin post | Noticeboard owner |
| DELETE | `/api/noticeboards/<id>/posts/<id>/delete` | Delete post | Noticeboard owner |

### 4. **Frontend** (noticeboards.html)

#### Features
- **Tab Interface**: Browse, My Noticeboards, Create Noticeboard
- **Noticeboard Cards**: Display with title, description, post count, creation date
- **Post Display**: With author info, priority badges, view count, pin status
- **Post Creation**: Form with title, content, priority level, attachment option
- **Responsive Design**: Mobile-friendly interface

#### Priority Levels
- **Low**: Green - General information
- **Normal**: Blue - Regular updates
- **High**: Red - Important announcements
- **Urgent**: Dark Red - Critical notifications

#### Pin Feature
- Pin important posts to the top of the noticeboard
- Pinned posts show with a thumbtack icon
- Highlighted background for visibility

### 5. **User Permissions**

#### Admins
- ✅ Create institution-wide noticeboards
- ✅ Post announcements
- ✅ Pin/unpin important posts
- ✅ Delete posts
- ✅ View all institution posts

#### Tutors
- ✅ Create course-specific noticeboards
- ✅ Post course announcements
- ✅ Pin/unpin important posts
- ✅ Delete their posts
- ✅ View all their noticeboard posts

#### Students
- ✅ View noticeboards from their enrolled courses
- ✅ View noticeboards from their institution's admin
- ✅ Post on their course noticeboards (optional based on settings)
- ❌ Delete or pin posts (unless they're the author)

#### Parents
- ✅ View noticeboards for their linked children's courses
- ✅ Stay informed about school announcements

## Usage Examples

### 1. **Admin Creating Institution Announcement**
```javascript
// POST /api/noticeboards/create
{
    "title": "New Academic Year Starts",
    "description": "Important dates and information",
    "owner_type": "admin"
}
```

### 2. **Tutor Creating Course Noticeboard**
```javascript
// POST /api/noticeboards/create
{
    "title": "Mathematics 101 - Important Updates",
    "description": "Course-specific announcements",
    "course_id": 5,
    "owner_type": "tutor"
}
```

### 3. **Posting Urgent Announcement**
```javascript
// POST /api/noticeboards/1/post
{
    "title": "Class Cancelled Today",
    "content": "Due to unforeseen circumstances...",
    "priority": "urgent",
    "attachment_url": null
}
```

### 4. **Viewing Student's Noticeboards**
```javascript
// GET /api/noticeboards/student/my-noticeboards
// Returns all noticeboards accessible to the student
```

## Integration Points

### With Courses
- Tutors can create course-specific noticeboards
- Posts are visible to enrolled students
- Course materials and live sessions can be referenced in posts

### With Users
- Posts show author information
- Admins and tutors identified for institutional authority
- Student access controlled by course enrollment

### With Forums
- Noticeboards are separate from forums for structured announcements
- Forums for discussions, Noticeboards for announcements
- Both available in the main navigation

## Future Enhancements

1. **Bulk Announcements** - Send to multiple courses simultaneously
2. **Email Notifications** - Email alerts for urgent/high priority posts
3. **Post Scheduling** - Schedule posts to publish at specific times
4. **File Attachments** - Upload PDFs, images, documents
5. **Post Expiration** - Automatically archive old posts
6. **Read Status Tracking** - Track which students have read posts
7. **Comments on Posts** - Allow discussion while keeping structure
8. **Categories/Tags** - Organize posts by category
9. **Search & Filter** - Find specific announcements
10. **Analytics Dashboard** - View post engagement metrics

## Security Considerations

- ✅ Authorization checks on all endpoints
- ✅ User type verification before allowing creation
- ✅ Owner verification before allowing modification
- ✅ SQL injection prevention with parameterized queries
- ✅ CSRF protection via Flask session
- ✅ Input validation on all forms

## Database Indexes

For optimal performance, the following indexes are created:
- `idx_noticeboards_owner` - Fast lookup by owner
- `idx_noticeboards_institution` - Fast lookup by institution
- `idx_noticeboards_course` - Fast lookup by course
- `idx_posts_noticeboard` - Fast lookup of posts by noticeboard
- `idx_posts_author` - Fast lookup of posts by author
- `idx_posts_pinned` - Fast lookup of pinned posts

## Migration Notes

To deploy this feature:

1. Run `create_tables()` in db_helper.py to create the new tables
2. Redeploy app.py with new imports and routes
3. Add noticeboards.html to templates folder
4. Update navigation links to include Noticeboards
5. Test with sample data for each user type

## Testing Checklist

- [ ] Admin can create institution noticeboard
- [ ] Tutor can create course noticeboard
- [ ] Posts can be created with all priority levels
- [ ] Posts can be pinned/unpinned
- [ ] Students see only their accessible noticeboards
- [ ] Views are tracked correctly
- [ ] Responsive design on mobile devices
- [ ] Authorization prevents unauthorized access
- [ ] Database queries are optimized
- [ ] No SQL injection vulnerabilities
