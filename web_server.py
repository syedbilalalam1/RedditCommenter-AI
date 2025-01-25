from flask import Flask, render_template, jsonify
import threading
from run_bot import run_bot
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify required environment variables
required_vars = [
    'OPENROUTER_API_KEY',
    'REDDIT_USERNAME',
    'REDDIT_PASSWORD',
    'CLIENT_ID',
    'CLIENT_SECRET',
    'USER_AGENT'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)

# Start time of the bot
START_TIME = datetime.now()

# Start the bot in a separate thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

def get_comment_history():
    try:
        with open('comment_history.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        comments = []
        current_comment = {}
        
        for line in lines:
            if line.startswith('[') and ']' in line:
                # This is a timestamp line with subreddit
                timestamp = line[1:20]
                subreddit = line.split('r/')[1].split(' -')[0] if 'r/' in line else 'unknown'
                title = line.split(' - ', 1)[1].strip() if ' - ' in line else ''
                current_comment = {
                    'time': timestamp,
                    'subreddit': subreddit,
                    'title': title
                }
            elif line.startswith('http'):
                # This is a comment link
                current_comment['link'] = line.strip()
                comments.append(current_comment.copy())
                
        return comments
    except FileNotFoundError:
        return []

def get_uptime():
    delta = datetime.now() - START_TIME
    hours = delta.total_seconds() / 3600
    return f"{int(hours)}h"

def count_today_comments():
    comments = get_comment_history()
    today = datetime.now().date()
    return sum(1 for comment in comments 
              if datetime.strptime(comment['time'], "%Y-%m-%d %H:%M:%S").date() == today)

def get_active_subreddits():
    try:
        with open('subreddits.txt', 'r') as f:
            return len([line.strip() for line in f if line.strip()])
    except FileNotFoundError:
        return 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    comments = get_comment_history()
    
    return jsonify({
        'total_comments': len(comments),
        'today_comments': count_today_comments(),
        'active_subreddits': get_active_subreddits(),
        'uptime': get_uptime(),
        'recent_comments': comments[-10:] if comments else []  # Last 10 comments
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Ensure the index.html template exists
    template_path = os.path.join('templates', 'index.html')
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} not found. Please create it with the provided HTML content.")
    
    app.run(host='0.0.0.0', port=10000) 