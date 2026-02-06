# Staff & Admin Portal Access Guide

## Overview
Staff and administrators can now access their portals directly from the public-facing hotel website at any time.

## Access Points

### 1. **Navigation Bar - "Staff Login" Button**
- Located in the top-right corner of the navigation bar
- Click the **🔐 Staff Login** button
- Available on all pages when scrolling

### 2. **Footer - Staff Access Section**
- Scroll to the bottom of the homepage
- Look for the **"🔐 Staff & Admin Access"** section
- Click **"Login to Portal"** button

## Login Process

1. **Click either access point** (navbar or footer)
2. **Login modal appears** as an overlay
3. **Enter your credentials:**
   - Email address
   - Password
4. **Click "Login"**
5. **You'll be redirected to:**
   - Staff Portal (for general staff)
   - Admin Dashboard (for administrators)

## Portal Features

### Staff Portal
- AI Knowledge Assistant
- Access to procedures and training materials
- Guest request handling
- Service standards lookup

### Admin Dashboard
- System status monitoring
- Booking management
- Tool statistics
- Index status and reindexing
- User management
- Analytics and reports

## Technical Details

- **Authentication:** OAuth2 token-based
- **Backend Port:** 8010
- **Session:** Persists until logout
- **Security:** HTTPS recommended for production

## Mobile Access

On mobile devices:
- Navigation menu collapses
- Staff login still accessible via footer section
- Responsive design ensures easy access

## Registration

New staff members:
1. Click "Staff Login"
2. Select "Register here"
3. Create account with email and password
4. After registration, login with credentials

## Support

If you encounter login issues:
- Ensure backend server is running on port 8010
- Check network connection
- Clear browser cache if needed
- Contact IT support for credential reset

---

**Last Updated:** February 2026
**Version:** 2.0
