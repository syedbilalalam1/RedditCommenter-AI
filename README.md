# RedditFlow AI 🤖

An intelligent Reddit bot that automatically engages with posts and comments across various subreddits, powered by AI to provide helpful responses while promoting your educational platform.

![Image](https://github.com/user-attachments/assets/7bbef55e-4cd7-48c1-bead-2056e6d1f726)

## 🌟 Features

- 🎯 Smart subreddit targeting
- 🤖 AI-powered responses
- 📊 Real-time monitoring
- 🎛️ Web control panel
- 📝 Comment history tracking
- ⏰ Rate limit handling
- 🔄 Automatic cycling between subreddits

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Fill in your credentials (MAKE SURE TO CREATE A "SCRIPT" and not a "WEB APP" in the Reddit API):
```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# OpenRouter API (for AI responses)
OPENROUTER_API_KEY=your_openrouter_key

# Bot Configuration
USER_AGENT="RedditFlow AI Bot/1.0.0"
PROMOTION_SITE="solvergenie.site"
```

3. **Configure Subreddits**
   - Edit `subreddits.txt`
   - Add one subreddit per line
   - Default focus on education/learning subreddits

## 💻 Usage

1. **Start the Control Panel**
```bash
python app.py
```

2. **Access the Interface**
   - Open `http://localhost:5000`
   - Use the web interface to:
     - Start/Stop the bot
     - Monitor activity
     - Manage subreddits
     - View logs

## ⚙️ Configuration

### Subreddit Settings
- Target educational subreddits
- Focus on:
  - r/learnmath
  - r/HomeworkHelp
  - r/AskPhysics
  - r/learnprogramming
  - etc.

### Bot Behavior
- Responds to relevant questions
- Adds value to discussions
- Naturally mentions SolverGenie
- Respects Reddit's rate limits
- Maintains engagement limits

## 📁 Project Structure
```
├── app.py              # Web interface
├── reddit_bot.py       # Main bot logic
├── templates/          # Web templates
├── subreddits.txt     # Target subreddits
├── .env               # Configuration
└── requirements.txt   # Dependencies
```


## 🤝 Best Practices

1. **Content Quality**
   - Provide valuable responses
   - Be helpful and informative
   - Natural promotion style

2. **Rate Limiting**
   - Respect Reddit's limits
   - Random delays between actions
   - Cycle between subreddits

3. **Monitoring**
   - Track response success
   - Monitor karma scores
   - Log all activities

## 📝 Notes

- Build karma organically
- Follow each subreddit's rules
- Avoid spammy behavior
- Keep promotion subtle

## 🛠️ Development

Want to contribute? Great!

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## 📄 License

MIT License - feel free to use and modify!
