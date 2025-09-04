# EduDesk Deployment Guide

## Overview
EduDesk is a comprehensive student productivity platform with features including calendar management, study timers, mood tracking, goal setting, and career guidance.

## Features Implemented

### 1. Career & Profile Building
- **Interactive Questionnaire**: 5-question assessment covering career interests, work environment preferences, location preferences, academic level, and career goals
- **Personalized Results**: 
  - Career path recommendations based on responses
  - University recommendations for different fields
  - Customized tips for career development
- **Fields Covered**: Technology, Medicine, Business, Arts, Engineering

### 2. Enhanced Forgot Password System
- **Secure Token Generation**: Uses crypto.getRandomValues() for secure token generation
- **Token Expiration**: 1-hour expiration for security
- **Email Validation**: Proper email format validation
- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, and number requirements
- **URL-based Reset**: Token passed via URL parameters

## Server-Side Implementation Requirements

### For Production Deployment

#### 1. Email Service Setup
```javascript
// Example using Node.js with Nodemailer
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransporter({
  service: 'gmail',
  auth: {
    user: 'your-email@gmail.com',
    pass: 'your-app-password'
  }
});

async function sendResetEmail(email, token) {
  const resetLink = `https://yourdomain.com/reset-password.html?token=${token}`;
  
  const mailOptions = {
    from: 'your-email@gmail.com',
    to: email,
    subject: 'Password Reset Request - EduDesk',
    html: `
      <h2>Password Reset Request</h2>
      <p>You requested a password reset for your EduDesk account.</p>
      <p>Click the link below to reset your password:</p>
      <a href="${resetLink}">Reset Password</a>
      <p>This link will expire in 1 hour.</p>
      <p>If you didn't request this, please ignore this email.</p>
    `
  };
  
  await transporter.sendMail(mailOptions);
}
```

#### 2. Database Schema
```sql
-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password reset tokens table
CREATE TABLE password_resets (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. API Endpoints (Node.js/Express)
```javascript
const express = require('express');
const bcrypt = require('bcrypt');
const crypto = require('crypto');

// Forgot password endpoint
app.post('/api/forgot-password', async (req, res) => {
  const { email } = req.body;
  
  // Check if user exists
  const user = await db.query('SELECT * FROM users WHERE email = $1', [email]);
  
  if (user.rows.length === 0) {
    return res.json({ message: 'If this email is registered, a reset link will be sent.' });
  }
  
  // Generate secure token
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + 3600000); // 1 hour
  
  // Store token in database
  await db.query(
    'INSERT INTO password_resets (email, token, expires_at) VALUES ($1, $2, $3)',
    [email, token, expiresAt]
  );
  
  // Send email
  await sendResetEmail(email, token);
  
  res.json({ message: 'Password reset link has been sent to your email.' });
});

// Reset password endpoint
app.post('/api/reset-password', async (req, res) => {
  const { token, password } = req.body;
  
  // Validate token
  const resetRecord = await db.query(
    'SELECT * FROM password_resets WHERE token = $1 AND expires_at > NOW()',
    [token]
  );
  
  if (resetRecord.rows.length === 0) {
    return res.status(400).json({ error: 'Invalid or expired token' });
  }
  
  // Hash new password
  const passwordHash = await bcrypt.hash(password, 10);
  
  // Update user password
  await db.query(
    'UPDATE users SET password_hash = $1 WHERE email = $2',
    [passwordHash, resetRecord.rows[0].email]
  );
  
  // Delete used token
  await db.query('DELETE FROM password_resets WHERE token = $1', [token]);
  
  res.json({ message: 'Password reset successful' });
});
```

## Deployment Steps

### 1. Static Hosting (Netlify/Vercel)
1. Upload all HTML files to your hosting platform
2. Configure custom domain
3. Set up HTTPS

### 2. Backend Deployment (Railway/Render)
1. Create Node.js application
2. Set up PostgreSQL database
3. Configure environment variables
4. Deploy API endpoints

### 3. Email Service
1. Set up Gmail App Password or use SendGrid
2. Configure SMTP settings
3. Test email delivery

### 4. Environment Variables
```env
DATABASE_URL=postgresql://username:password@host:port/database
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
JWT_SECRET=your-jwt-secret
```

## Security Considerations

1. **HTTPS Only**: All communications should use HTTPS
2. **Password Hashing**: Use bcrypt for password storage
3. **Token Security**: Generate cryptographically secure tokens
4. **Rate Limiting**: Implement rate limiting on password reset endpoints
5. **Input Validation**: Validate all user inputs server-side
6. **CORS Configuration**: Configure CORS for your domain

## Testing Checklist

- [ ] User registration works
- [ ] User login works
- [ ] Forgot password email sends
- [ ] Reset password link works
- [ ] Token expiration works
- [ ] Password requirements enforced
- [ ] Career questionnaire works
- [ ] All navigation links work
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility

## File Structure
```
schedule/
├── index.html (landing page)
├── login.html
├── signup.html
├── forgot-password.html
├── reset-password.html
├── dashboard.html
├── career-profile.html
├── calendar.html
├── study-timer.html
├── mood-tracker.html
├── goal-setting.html
├── diary.html
├── mindfulness.html
├── wallet.html
├── alarm.html
├── Journal.html
├── createblog.html
├── blogfeed.html
├── settings.html
├── styles.css
├── The EDUDESK..png
├── BoySuccess.png
├── BoyWorking.png
└── DEPLOYMENT_GUIDE.md
```

## Support
For deployment issues or feature requests, please refer to the implementation details above or contact the development team. 