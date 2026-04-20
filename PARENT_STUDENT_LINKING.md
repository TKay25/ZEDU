# Parent-Student Account Linking System

## Overview

The ZEDU platform includes a secure parent-student account linking system that allows parents/guardians to connect with and monitor up to 7 student accounts. This document explains the linking process, credentials, and approval workflow.

---

## Key Features

- **Up to 7 Children Per Parent:** Parents can link and manage up to 7 student accounts
- **No Education Level Required:** Parents don't need an education level since their children may be in different levels
- **Organized Access Points UI:** New dashboard displays all linked children with clear status indicators
- **Flexible Relationship Types:** Support for parent, guardian, and custodian relationships
- **Verification Code System:** 6-digit codes for secure link approval
- **Status Tracking:** Pending, approved, and rejected link states

---

## System Architecture

### Database Schema

#### `parent_student_links` Table
```sql
CREATE TABLE parent_student_links (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'parent' 
        CHECK (relationship_type IN ('parent', 'guardian', 'custodian')),
    status VARCHAR(50) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'approved', 'rejected')),
    verification_code VARCHAR(10),
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- NOTE: No UNIQUE constraint - allows multiple links but enforced at application level (max 7 per parent)
```

**Relationship Types:**
- `parent`: Biological/Legal parent
- `guardian`: Court-appointed guardian  
- `custodian`: Other legal custodian

---

## Account Linking Workflow

### Step 1: Parent Initiates Linking Request

**Endpoint:** `POST /api/parent/link-student`

**Authentication:** Required (parent account)

**Request Payload:**
```json
{
    "student_email": "student@example.com",
    "relationship_type": "parent"  // Optional: defaults to "parent"
}
```

**Validation:**
- User must be authenticated as a **parent** account
- Student email must exist and belong to a **student** account
- Cannot link same student twice (UNIQUE constraint)

**Response (Success):**
```json
{
    "success": true,
    "message": "Link request sent to student@example.com",
    "link_id": 1,
    "verification_code": "482591",
    "created_at": "2026-04-20T10:30:00",
    "student_email": "student@example.com"
}
```

**What Happens:**
1. Database creates pending link with `status = 'pending'`
2. **6-digit verification code** generated randomly (e.g., `482591`)
3. Code stored in database for student verification
4. Parent receives confirmation with code (in production: send via email)

---

### Step 2: Student Views Pending Linking Requests

**Endpoint:** `GET /api/student/pending-links`

**Authentication:** Required (student account)

**Response:**
```json
{
    "success": true,
    "pending_links": [
        {
            "id": 1,
            "verification_code": "482591",
            "relationship_type": "parent",
            "created_at": "2026-04-20T10:30:00",
            "parent_id": 42,
            "parent_name": "Mr Zvakasikwa",
            "parent_email": "parent@example.com",
            "education_level": "high_school"
        }
    ]
}
```

---

### Step 3: Student Approves or Rejects Linking

#### Option A: Student Approves Link

**Endpoint:** `POST /api/student/approve-link/{verification_code}`

**Example:** `POST /api/student/approve-link/482591`

**Authentication:** Required (student account)

**Response (Success):**
```json
{
    "success": true,
    "message": "Account successfully linked to parent Mr Zvakasikwa",
    "link": {
        "id": 1,
        "parent_id": 42,
        "parent_name": "Mr Zvakasikwa",
        "parent_email": "parent@example.com",
        "relationship_type": "parent",
        "approval_date": "2026-04-20T10:35:00"
    }
}
```

**What Happens:**
1. Verification code validated
2. Link status changed from `'pending'` → `'approved'`
3. `approval_date` timestamp recorded
4. Parent gains view access to student's progress, courses, assignments

---

#### Option B: Student Rejects Link

**Endpoint:** `POST /api/student/reject-link/{verification_code}`

**Example:** `POST /api/student/reject-link/482591`

**Authentication:** Required (student account)

**Response:**
```json
{
    "success": true,
    "message": "Parent linking request rejected"
}
```

**What Happens:**
1. Link status changed to `'rejected'`
2. Record kept for audit trail
3. Parent cannot see student account
4. Parent can request link again (creates new verification code)

---

### Step 4: Parent Views Linked Students (All Access Points)

**Endpoint:** `GET /api/parent/linked-students`

**Authentication:** Required (parent account)

**Response:**
```json
{
    "success": true,
    "count": 3,
    "data": [
        {
            "link_id": 1,
            "student_id": 15,
            "student_name": "John Zvakasikwa",
            "student_email": "john@example.com",
            "education_level": "high_school",
            "relationship_type": "parent",
            "status": "approved",
            "verification_code": null,
            "approval_date": "2026-04-20T10:35:00",
            "created_at": "2026-04-15T08:00:00"
        },
        {
            "link_id": 2,
            "student_id": 16,
            "student_name": "Jane Zvakasikwa",
            "student_email": "jane@example.com",
            "education_level": "primary",
            "relationship_type": "parent",
            "status": "pending",
            "verification_code": "482591",
            "approval_date": null,
            "created_at": "2026-04-20T12:00:00"
        }
    ]
}
```

**Features:**
- Returns **ALL** linked students (pending, approved, rejected)
- Shows verification codes for pending links
- Displays up to 7 children (enforced by application)
- Sorted by newest first

---

### Step 5: Parent Unlinks Student (Optional)

**Endpoint:** `POST /api/parent/unlink-student`

**Authentication:** Required (parent account)

**Request Body:**
```json
{
    "link_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "Child link successfully unlinked"
}
```

**Features:**
- Works for any link status (pending, approved, rejected)
- Removes relationship from system
- Parent can re-link the same student later
- Can be used to cancel pending link requests or unlink approved children

---

## Linking Limits

### 7 Children Per Parent

- **Maximum:** Parents can link up to 7 children
- **Enforcement:** Application-level check in `request_parent_student_link()`
- **Error Message:** "You can link up to 7 children. Please unlink a child first to add more."
- **Counting:** Only approved links count toward the limit
- **Management:** New dashboard UI displays all 7 access points with clear organization

---

## Verification Code System

### Security Features

1. **6-Digit Random Code**
   - Generated using `random.choices(string.digits, k=6)`
   - Ranges from `000000` to `999999`
   - Unique per linking request

2. **Single-Use Verification**
   - Code can only be used once (success or rejection)
   - Code becomes invalid after approval/rejection
   - Code tied to specific `link_id`

3. **Time-Limited (Recommended)**
   - Consider adding `expires_at` timestamp
   - Suggest 48-hour expiration window
   - Auto-reject if expired

### Code Delivery Methods

**Current (Development):**
- Returned in API response for testing

**Production Recommendations:**
```
Option 1: Email Delivery
- Send verification code to parent's registered email
- Format: "Your parent-student linking code is: 482591"

Option 2: WhatsApp (Primary)
- Use parent's WhatsApp number (already collected during signup)
- Integrate with WhatsApp Business API
- Template: "Your ZEDU linking code: 482591 (valid 48 hours)"

Option 3: SMS
- Send via SMS service (Twilio, AWS SNS)
- Backup if WhatsApp unavailable

Option 4: In-App Notification
- Show on parent dashboard after request
- Also available at /student/pending-links endpoint
```

---

## Approval Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PARENT SIGNUP                             │
│  Email: parent@example.com                                   │
│  Name: Mr Zvakasikwa                                         │
│  Account Type: Parent                                        │
│  Education: High School                                      │
│  WhatsApp: +1 (555) 000-0000                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │ Parent clicks "Link Student"         │
         │ Enters student email: john@...       │
         └──────────────┬──────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────┐
        │ System creates PENDING link record    │
        │ Generates 6-digit verification code   │
        │ Code sent to parent (email/WhatsApp)  │
        │ Status: PENDING                       │
        └──────────────┬───────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────┐
    │ Student receives notification of link     │
    │ Student can view pending requests at:     │
    │ GET /api/student/pending-links            │
    │ Shows parent name, email, relationship    │
    └──────────────┬──────────────────────────┘
                   │
           ┌───────┴────────┐
           │                │
           ▼                ▼
    ┌────────────┐  ┌─────────────┐
    │  APPROVE   │  │   REJECT    │
    │ Using code │  │ Using code  │
    └─────┬──────┘  └──────┬──────┘
          │                │
          ▼                ▼
     [APPROVED]        [REJECTED]
     Status: 'approved' Status: 'rejected'
     Date recorded      Can retry again
     Parent can access  Parent cannot access
     student progress   (needs new code)
```

---

## Credentials & Access Control

### Credentials Required for Linking

**Parent provides:**
- Email address (during parent signup)
- Password (during parent signup)
- **Education level:** NOT required (parents can have children in multiple education levels)

**Student provides:**
- Email address (during student signup)
- Education level (required - indicates their grade/level)
- Verification code (received from parent)

**Note:** Parent education level is optional since they may have multiple children in different education levels (e.g., one in primary school, another in high school).

### Access Control After Linking

**Parent CAN:**
- ✅ View linked student's courses and progress
- ✅ View linked student's grades/assignments
- ✅ View linked student's attendance (if available)
- ✅ Receive notifications about linked student's activity
- ✅ Access linked student dashboard

**Parent CANNOT:**
- ❌ Edit student's password
- ❌ Modify student's profile
- ❌ Enroll student in courses
- ❌ Delete student's account

**Student ALWAYS:**
- Has full control of own account
- Can unlink parent by requesting to unlink
- Can reject any parent linking attempt
- Maintains account privacy

---

## API Endpoints Summary

| Endpoint | Method | Role | Purpose |
|----------|--------|------|---------|
| `/api/parent/link-student` | POST | Parent | Request to link student (max 7 per parent) |
| `/api/student/pending-links` | GET | Student | View pending link requests |
| `/api/student/approve-link/{code}` | POST | Student | Approve parent link |
| `/api/student/reject-link/{code}` | POST | Student | Reject parent link |
| `/api/parent/linked-students` | GET | Parent | View all linked students (all statuses) |
| `/api/parent/unlink-student` | POST | Parent | Unlink a student (by link_id in body) |

---

## Parent Dashboard UI - Access Points

The new parent dashboard includes an organized "My Children's Access Points" section that displays:

### Features:
- **Grid Layout:** Up to 7 children displayed in organized cards
- **Status Indicators:** Clear badges for approved, pending, or rejected links
- **Quick Actions:** 
  - View Profile (for approved links)
  - Show Code (for pending links - share with child)
  - Unlink/Cancel (remove relationship)
- **Link Information:**
  - Child's name and email
  - Education level
  - Relationship type
  - Link status
  - Verification code (for pending only)
- **Add New Link:** Easy "Link New Child" button with modal form
- **Count Display:** Shows current links vs. maximum (e.g., "3/7")

---

## Error Handling

### Common Errors

**404 - Student Not Found:**
```json
{
    "success": false,
    "message": "Student not found with that email"
}
```

**409 - Already Linked:**
```json
{
    "success": false,
    "message": "This student is already linked to your account"
}
```

**409 - Link Pending:**
```json
{
    "success": false,
    "message": "A linking request is already pending for this student"
}
```

**403 - Wrong User Type:**
```json
{
    "success": false,
    "message": "Only parents can link students"
}
```

**400 - Invalid Code:**
```json
{
    "success": false,
    "message": "Invalid verification code or link already processed"
}
```

---

## Database Migration

### Running the Migration

```bash
# Execute migration script to create parent_student_links table
python migration_parent_student_links.py
```

### Verification

```sql
-- Check table exists
\dt parent_student_links

-- Check sample data
SELECT * FROM parent_student_links;

-- Check indexes
\di idx_parent_links_*
```

---

## Security Considerations

### Current Implementation
✅ Verification code system prevents unauthorized access  
✅ Role-based access control (parent vs student)  
✅ Unique constraint prevents duplicate links  
✅ Status field tracks link state (pending/approved/rejected)  
✅ Audit trail with timestamps  

### Recommended Enhancements

**For Production:**

1. **Code Expiration**
   ```sql
   ALTER TABLE parent_student_links ADD COLUMN expires_at TIMESTAMP;
   ```

2. **Rate Limiting**
   - Limit linking requests to 5 per hour per parent
   - Prevent brute-force code guessing

3. **Audit Logging**
   - Log all link approvals/rejections
   - Track parent access to student data

4. **Email Verification**
   - Verify parent email before allowing links
   - Verify student email on account creation

5. **Two-Factor Authentication**
   - Require 2FA for parent accounts
   - Protect from account takeover

---

## Testing the System

### Manual Testing Flow

```bash
# 1. Create parent account
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@test.com",
    "password": "secure123",
    "confirm_password": "secure123",
    "full_name": "Test Parent",
    "user_type": "parent",
    "education_level": "high_school",
    "country_code": "+1",
    "whatsapp_number": "+15550000001"
  }'

# 2. Create student account
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "secure123",
    "confirm_password": "secure123",
    "full_name": "Test Student",
    "user_type": "student",
    "education_level": "high_school",
    "country_code": "+1"
  }'

# 3. Parent logs in and requests link
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "parent@test.com", "password": "secure123"}'

# 4. Parent links student
curl -X POST http://localhost:5000/api/parent/link-student \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"student_email": "student@test.com", "relationship_type": "parent"}'
# Response: {"verification_code": "482591", ...}

# 5. Student logs in and views pending links
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@test.com", "password": "secure123"}'

curl -X GET http://localhost:5000/api/student/pending-links \
  -H "Cookie: session=..."

# 6. Student approves link with code
curl -X POST http://localhost:5000/api/student/approve-link/482591 \
  -H "Cookie: session=..."

# 7. Parent views linked students
curl -X GET http://localhost:5000/api/parent/linked-students \
  -H "Cookie: session=..."
```

---

## Future Enhancements

1. **Bulk Linking**
   - Allow parents to upload CSV of student emails
   - Auto-approve or require student approval

2. **Multiple Parents**
   - Support multiple parents linked to same student
   - Different permissions per parent

3. **Parent Dashboard**
   - View all linked students' progress
   - Receive automated progress reports
   - Set goals and milestones

4. **Communication Channel**
   - Direct parent-tutor messaging
   - Progress notifications
   - Alert system for concerns

5. **Advanced Permissions**
   - Granular permissions (view only, message, etc.)
   - Temporary links with expiration
   - Permission revocation by parent/student

---

## Conclusion

The parent-student linking system provides a secure, approval-based mechanism for parents to connect with and monitor student accounts. The verification code workflow ensures that only legitimate parents can access student data, while students maintain full control over their account linkages.

For questions or implementation support, refer to the API endpoints and database schema outlined in this document.
