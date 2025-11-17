# Environment Variables Configuration

Create a `.env` file in the root directory with these variables:

## Clerk Authentication
Get these from [Clerk Dashboard](https://clerk.com)

```bash
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
```

## Supabase Configuration
Get these from [Supabase Dashboard](https://supabase.com)

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here
```

## OpenAI Configuration
Get this from [OpenAI Platform](https://platform.openai.com)

```bash
OPENAI_API_KEY=sk-your_openai_api_key_here
```

## Flask Configuration

```bash
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=4000
JWT_SECRET=your_random_jwt_secret_for_legacy_support
```

## Setup Instructions

### 1. Clerk Setup
1. Go to https://clerk.com and create an account
2. Create a new application
3. Enable Google OAuth provider in the Clerk dashboard
4. Copy your API keys from the dashboard

### 2. Supabase Setup
1. Go to https://supabase.com and create an account
2. Create a new project
3. Run the SQL commands from `docs/SUPABASE_SETUP.md`
4. Copy your project URL and keys from the settings

### 3. OpenAI Setup
1. Go to https://platform.openai.com
2. Create an account or log in
3. Navigate to API keys section
4. Create a new API key
5. Copy the key (you won't be able to see it again!)

### 4. Create .env file
Create a file named `.env` in the root directory and paste all your keys.


