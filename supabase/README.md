# Supabase - Authentication & Services

This directory contains the **Supabase services configuration** for the Base Platform monorepo. Supabase provides authentication, storage, and real-time database services that integrate seamlessly with our cross-platform frontend.

## ⚠️ Important Architecture Note

**Database Schema Management**: While Supabase provides the database infrastructure, **all database schema changes are managed through Alembic migrations in the backend** (`backend/app/alembic/`). This ensures:

- **Single Source of Truth**: All schema changes go through the backend
- **Version Control**: Schema changes are tracked in Git
- **Consistency**: Both web and mobile use the same database schema
- **Deployment Safety**: Schema changes are applied safely in production

## What Supabase Provides

### **Authentication (Supabase Auth)**
- **User Management**: Email/password, OAuth (Google, Apple)
- **JWT Tokens**: Secure authentication for both web and mobile
- **Social Login**: Google Sign-In, Apple Sign-In support
- **Email Confirmation**: PKCE flow with local development support

### **Storage (Supabase Storage)**
- **File Uploads**: User avatars and other media files
- **Access Control**: Row-level security for file access
- **CDN**: Fast file delivery worldwide

### **Database (PostgreSQL)**
- **Real-time**: Live updates via WebSockets
- **Row-Level Security**: Fine-grained access control
- **Backup & Recovery**: Automatic database backups

## Local Development Setup

### **Starting Supabase Services**
```bash
# From the project root
cd supabase
nvm use && yarn start
```

**Services Started:**
- **Database**: PostgreSQL on port 5432
- **API**: Supabase API on port 54321
- **Dashboard**: Admin interface on port 54323
- **InBucket**: Email testing on port 54324

### **Environment Variables**
Set these in your root `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_AUTH_JWT_SECRET=your-jwt-secret-at-least-32-chars

# Frontend Configuration
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EXPO_PUBLIC_SUPABASE_URL=http://localhost:54321
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Production Setup

### **1. Create Supabase Project**
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and API keys

### **2. Configure Environment**
Update your production environment variables:

```bash
# Production Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-production-anon-key
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-production-anon-key
```

### **3. Configure Authentication**
In your Supabase dashboard:
1. Go to **Authentication** → **URL Configuration**
2. Add your production URLs to **Redirect URLs**
3. Configure OAuth providers if using social login

## OAuth Configuration

### **Google Sign-In**
1. Create Google Cloud project
2. Configure OAuth 2.0 credentials
3. Add to Supabase Auth settings
4. Update environment variables:

```bash
GOOGLE_IOS_SCHEME=your-ios-scheme
GOOGLE_IOS_CLIENT_ID=your-ios-client-id
GOOGLE_WEB_CLIENT_ID=your-web-client-id
GOOGLE_SECRET=your-secret
```

### **Apple Sign-In**
1. Configure Apple Developer account
2. Create App ID with Sign In capability
3. Add to Supabase Auth settings
4. Configure native iOS app

## Development Workflow

### **Email Testing (Local)**
When developing locally, emails are captured by InBucket:

1. Start Supabase: `cd supabase && nvm use && yarn start`
2. Navigate to: http://localhost:54324
3. Check email confirmations and password resets

### **Database Changes**
**Remember**: Schema changes go through the backend, not Supabase directly:

```bash
# 1. Modify models in backend/app/models.py
# 2. Generate migration
cd backend
alembic revision --autogenerate -m "description"

# 3. Apply migration
alembic upgrade head
```

### **Storage Management**
- Configure storage buckets in Supabase dashboard
- Set up Row-Level Security policies
- Test file uploads locally before production

## Troubleshooting

### **Common Issues**

#### **Authentication Errors**
- Verify environment variables are set correctly
- Check Supabase service is running locally
- Ensure JWT secret is at least 32 characters

#### **Database Connection Issues**
- Verify Supabase is running: `cd supabase && nvm use && yarn start`
- Check port 5432 is available
- Review backend database configuration

#### **OAuth Configuration**
- Verify client IDs and secrets are correct
- Check redirect URLs in Supabase dashboard
- Ensure OAuth providers are enabled

### **Useful Commands**
```bash
# Start Supabase services (use correct Node version)
cd supabase && nvm use && yarn start

# Stop Supabase services
cd supabase && yarn stop

# Reset local database
cd supabase && yarn reset

# Check status
cd supabase && yarn status
```

## Integration with Base Platform

### **Frontend Usage**
The frontend automatically uses Supabase for:
- User authentication and session management
- File uploads and storage
- Real-time database subscriptions

### **Backend Integration**
The FastAPI backend:
- Validates Supabase JWT tokens
- Manages database schema via Alembic
- Provides RESTful API endpoints
- Integrates with Supabase services

### **Mobile Support**
Expo apps automatically:
- Handle Supabase authentication
- Manage secure token storage
- Support offline-first development

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Row-Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Storage Configuration](https://supabase.com/docs/guides/storage)
- [Local Development](https://supabase.com/docs/guides/self-hosting/docker)
