# EduDesk Backend API

A Flask-based REST API for the EduDesk student productivity platform.

## Features

- **Authentication**: JWT-based authentication with password reset
- **Calendar Management**: Create, read, update, delete calendar events
- **Mood Tracking**: Track daily moods with analytics
- **Journal**: Encrypted personal journal entries
- **Goal Setting**: Set and track academic and personal goals
- **Study Sessions**: Track study time with analytics
- **Blog System**: Create and manage blog posts
- **Alarms**: Set and manage reminders
- **Document Storage**: Upload and manage files
- **Analytics**: Comprehensive dashboard and productivity analytics

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Run the Application

```bash
python run.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Calendar
- `GET /api/calendar/events` - Get calendar events
- `POST /api/calendar/events` - Create calendar event
- `PUT /api/calendar/events/<id>` - Update calendar event
- `DELETE /api/calendar/events/<id>` - Delete calendar event

### Mood Tracking
- `GET /api/mood/entries` - Get mood entries
- `POST /api/mood/entries` - Create mood entry
- `GET /api/mood/analytics` - Get mood analytics
- `GET /api/mood/streak` - Get mood tracking streak

### Journal
- `GET /api/journal/entries` - Get journal entries
- `POST /api/journal/entries` - Create journal entry
- `PUT /api/journal/entries/<id>` - Update journal entry
- `DELETE /api/journal/entries/<id>` - Delete journal entry

### Goals
- `GET /api/goals/goals` - Get goals
- `POST /api/goals/goals` - Create goal
- `PUT /api/goals/goals/<id>` - Update goal
- `DELETE /api/goals/goals/<id>` - Delete goal
- `PUT /api/goals/goals/<id>/progress` - Update goal progress

### Study Sessions
- `GET /api/study/sessions` - Get study sessions
- `POST /api/study/sessions` - Create study session
- `GET /api/study/analytics` - Get study analytics

### Blog
- `GET /api/blog/posts` - Get blog posts
- `POST /api/blog/posts` - Create blog post
- `GET /api/blog/public` - Get public blog posts

### Alarms
- `GET /api/alarms/alarms` - Get alarms
- `POST /api/alarms/alarms` - Create alarm
- `PUT /api/alarms/alarms/<id>/toggle` - Toggle alarm

### Documents
- `GET /api/documents/documents` - Get documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/download/<id>` - Download document

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard analytics
- `GET /api/analytics/productivity` - Get productivity analytics

## Database Schema

The application uses SQLAlchemy with the following main models:

- **User**: User accounts and profiles
- **CalendarEvent**: Calendar events and appointments
- **MoodEntry**: Daily mood tracking entries
- **JournalEntry**: Personal journal entries
- **Goal**: Academic and personal goals
- **StudySession**: Study time tracking
- **BlogPost**: Blog posts and articles
- **Alarm**: Reminders and alarms
- **UserDocument**: File uploads and documents

## Deployment

### Railway/Render Deployment

1. Create a new project on Railway or Render
2. Connect your GitHub repository
3. Set environment variables in the dashboard
4. Deploy!

### Environment Variables for Production

```env
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-secret
DATABASE_URL=postgresql://user:pass@host:port/db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Development

### Running Tests

```bash
python -m pytest
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Input validation and sanitization
- CORS configuration
- File upload security
- Rate limiting (can be added)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
