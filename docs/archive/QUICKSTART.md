# 🚀 Moneta Quick Start Guide

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- An OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- A Supabase account ([Sign up here](https://supabase.com))

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create a `.env` file in the Moneta2 directory:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Flask Settings
FLASK_DEBUG=True
FLASK_PORT=4000

# Security
JWT_SECRET=your-random-secret-key-here
```

## Step 3: Setup Database

Run the setup scripts to create necessary tables:

```bash
python scripts/setup_chat_tables.py
python scripts/setup_cloud.py
```

## Step 4: Run the Application

```bash
python run.py
```

Your application will start at: **http://localhost:4000**

## 🎉 You're Ready!

Open your browser and navigate to `http://localhost:4000` to start using Moneta!

### What You Can Do:

1. **Sign Up/Login** - Create an account or login
2. **Start Chatting** - Have conversations with the AI
3. **View Memories** - See your memory network visualization
4. **Manage Subscriptions** - Choose a plan that fits your needs

## 📚 Next Steps

- Read the [Full Documentation](README.md)
- Check out [How to Use Guide](docs/HOW_TO_USE.md)
- Learn about the [Memory System](docs/MEMORY_SYSTEM_OVERVIEW.md)

## 🆘 Troubleshooting

### Port Already in Use?

Change the port in your `.env` file:
```env
FLASK_PORT=5000
```

### Database Connection Issues?

1. Verify your Supabase credentials in `.env`
2. Run the setup scripts again
3. Check Supabase dashboard for errors

### OpenAI API Errors?

1. Verify your API key is valid
2. Check your OpenAI account has credits
3. Ensure the key has proper permissions

## 💡 Tips

- Use **CTRL+C** to stop the server
- Check the terminal for logs and errors
- The first run might take longer as it downloads ML models

---

**Need Help?** Check the `docs/` folder for detailed guides!



