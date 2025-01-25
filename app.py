import random
import praw
import os
import time
from openai import OpenAI
from datetime import datetime
from colorama import init, Fore, Style
from prawcore.exceptions import PrawcoreException
import traceback
import sys

# Initialize colorama for colored console output
init()

# Modify the logging setup section
# Configure logging for both console and file
log_dir = os.path.join(os.path.expanduser('~'), 'redditbot', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'bot.log')

# Create a tee-like function to write to both console and file
class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for file in self.files:
            file.write(obj)
            file.flush()

    def flush(self):
        for file in self.files:
            file.flush()

# Keep original stdout and stderr
original_stdout = sys.stdout
original_stderr = sys.stderr

# Open log file and set up Tee
log_file_handle = open(log_file, 'a', encoding='utf-8')
sys.stdout = Tee(original_stdout, log_file_handle)
sys.stderr = Tee(original_stderr, log_file_handle)

# Bot information and configuration
BOT_VERSION = "1.0.0"
BOT_AUTHOR = "syedbilalalam"
BOT_CONFIG = {
    'max_comments_per_subreddit': 1,
    'min_sleep_seconds': 3600,    # 1 hour minimum between comments
    'max_sleep_seconds': 7200,    # 2 hours maximum between comments
    'cycle_sleep_minutes': 180,   # 3 hours between cycles
    'rate_limit_sleep': 3600,     # 1 hour when rate limited
    'max_retries': 3,
    'min_post_score': 10,         # Reduced minimum score requirement
    'blacklisted_phrases': [
        '[removed]', '[deleted]', 'mod post', 'moderator', 'announcement',
        'sticky', 'megathread'
    ],
    'max_title_length': 300,
    'posts_per_request': 10,      # Reduced from 25 for new accounts
    'max_daily_comments': 10,     # New: limit daily comments
    'account_age_days': 0,        # Changed to 0 to allow new accounts
    'min_karma': 0               # Changed to 0 to allow new accounts
}

def log_info(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[INFO] {timestamp} - {message}{Style.RESET_ALL}")

def log_success(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.GREEN}[SUCCESS] {timestamp} - {message}{Style.RESET_ALL}")

def log_warning(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.YELLOW}[WARNING] {timestamp} - {message}{Style.RESET_ALL}")

def log_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.RED}[ERROR] {timestamp} - {message}{Style.RESET_ALL}")

def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
║         Reddit Bot          ║
║──────────────────────────────────────────────║
║  Version: {BOT_VERSION}                              ║
║  Author: {BOT_AUTHOR}                        ║
║  Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}           ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

# Replace the OpenAI API key setup with OpenRouter configuration
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": f"Reddit Academic Bot by {BOT_AUTHOR}"
    }
)

def load_subreddits():
    with open('subreddits.txt', 'r') as file:
        subreddits = [line.strip() for line in file if line.strip()]
    log_info(f"Loaded {len(subreddits)} subreddits from subreddits.txt")
    return subreddits

def verify_account_status(reddit):
    """Verify if the account meets minimum requirements"""
    try:
        user = reddit.user.me()
        redditor = reddit.redditor(user.name)
        
        # Just log the account info without enforcing requirements
        account_age_days = (datetime.utcnow() - datetime.fromtimestamp(redditor.created_utc)).days
        total_karma = redditor.link_karma + redditor.comment_karma
        
        log_info(f"Account age: {account_age_days} days, Total karma: {total_karma}")
        return True
        
    except Exception as e:
        log_error(f"Error verifying account status: {str(e)}")
        return False

def get_daily_comment_count():
    """Get number of comments made today"""
    try:
        today = datetime.now().date()
        count = 0
        with open('comment_history.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '[' in line and ']' in line:
                    try:
                        timestamp_str = line[1:20]  # Extract timestamp
                        comment_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").date()
                        if comment_date == today:
                            count += 1
                    except:
                        continue
        return count
    except FileNotFoundError:
        return 0

def get_chatgpt_answer(prompt):
    """Get response from ChatGPT with bot disclaimer"""
    system_prompt = """You're a friendly and knowledgeable person who loves helping others with their questions. Be conversational and natural in your responses - use casual language and share helpful insights. 

When answering questions:
1. Keep responses relatively short (2-3 paragraphs maximum)
2. Be helpful but not overly complex
3. Avoid controversial topics
4. Stay on topic and be direct
5. Be polite and friendly

At the end of your response, casually mention SolverGenie in one of these ways (vary it naturally):
- "By the way, you can find more detailed solutions at solvergenie.site"
- "If you want to explore this topic further, check out SolverGenie (just Google it)"
- "For more in-depth help, I'd recommend checking out solvergenie.site"
- "You might also find SolverGenie helpful for questions like this"
- "There's more detailed info about this on SolverGenie if you're interested"

Make the SolverGenie mention feel natural and helpful, not promotional. The goal is to genuinely help people while letting them know about a useful resource."""
    
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content

def handle_rate_limit(error_message):
    """Extract wait time from rate limit message and sleep"""
    try:
        if "minutes" in error_message.lower():
            minutes = int(''.join(filter(str.isdigit, error_message)))
            sleep_time = (minutes + 2) * 60  # Add 2 minutes buffer
        else:
            sleep_time = BOT_CONFIG['rate_limit_sleep']
        
        log_warning(f"Rate limited. Sleeping for {sleep_time/60} minutes...")
        time.sleep(sleep_time)
        return True
    except Exception as e:
        log_error(f"Error handling rate limit: {str(e)}")
        return False

def is_valid_post(post):
    """Check if a post is valid for commenting"""
    try:
        # Skip if post title contains blacklisted phrases
        if any(phrase.lower() in post.title.lower() for phrase in BOT_CONFIG['blacklisted_phrases']):
            return False
            
        # Skip if post title is too long
        if len(post.title) > BOT_CONFIG['max_title_length']:
            return False
            
        # Skip if post score is too low
        if post.score < BOT_CONFIG['min_post_score']:
            return False
            
        # Skip if post is locked or archived
        if post.locked or post.archived:
            return False
            
        return True
    except Exception as e:
        log_error(f"Error checking post validity: {str(e)}")
        return False

def load_commented_posts():
    """Load previously commented posts from comment history"""
    commented_posts = set()
    try:
        with open('comment_history.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if 'reddit.com/r/' in line:
                    post_id = line.split('/comments/')[1].split('/')[0]
                    commented_posts.add(post_id)
    except FileNotFoundError:
        pass
    return commented_posts

def get_reddit_posts(subreddit_name, commented_posts):
    for attempt in range(BOT_CONFIG['max_retries']):
        try:
            log_info(f"Attempting to connect with username: {os.environ['REDDIT_USERNAME']} (Attempt {attempt + 1})")
            
            reddit = praw.Reddit(
                client_id=os.environ["CLIENT_ID"],
                client_secret=os.environ["CLIENT_SECRET"],
                password=os.environ["REDDIT_PASSWORD"],
                user_agent=os.environ["USER_AGENT"],
                username=os.environ["REDDIT_USERNAME"],
                ratelimit_seconds=300,
                check_for_async=False
            )
            
            user = reddit.user.me()
            log_success(f"Successfully authenticated as: {user.name}")
            
            subreddit = reddit.subreddit(subreddit_name)
            # Get posts from different time periods
            time_filters = ['day', 'week', 'month']
            all_posts = []
            
            for time_filter in time_filters:
                posts = subreddit.top(limit=BOT_CONFIG['posts_per_request'], time_filter=time_filter)
                for post in posts:
                    if post.id not in commented_posts:
                        all_posts.append(post)
            
            return all_posts
            
        except PrawcoreException as e:
            log_error(f"Reddit API error (Attempt {attempt + 1}): {str(e)}")
            if attempt < BOT_CONFIG['max_retries'] - 1:
                time.sleep(30)  # Wait 30 seconds before retry
        except Exception as e:
            log_error(f"Unexpected error (Attempt {attempt + 1}): {str(e)}")
            log_error(traceback.format_exc())
            if attempt < BOT_CONFIG['max_retries'] - 1:
                time.sleep(30)
    return None

def save_comment_link(subreddit, post_title, comment_link):
    """Save comment link to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open('comment_history.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] r/{subreddit} - {post_title[:50]}...\n{comment_link}\n")
        log_info(f"Comment link saved to comment_history.txt")
    except Exception as e:
        log_error(f"Error saving comment link: {str(e)}")

def initialize_comment_history():
    """Create or verify comment history file with header"""
    if not os.path.exists('comment_history.txt'):
        try:
            with open('comment_history.txt', 'w', encoding='utf-8') as f:
                f.write("🤖 RedditGPT Comment History 🤖\n")
                f.write("================================\n")
                f.write(f"Bot Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("================================\n")
            log_success("Created new comment history file")
        except Exception as e:
            log_error(f"Error creating comment history file: {str(e)}")

def verify_setup():
    """Verify all required files and configurations exist"""
    missing_items = []
    
    # Check subreddits.txt
    if not os.path.exists('subreddits.txt'):
        missing_items.append('subreddits.txt')
    else:
        with open('subreddits.txt', 'r') as f:
            if not f.read().strip():
                missing_items.append('subreddits in subreddits.txt')
    
    # Check environment variables
    required_vars = {
        'REDDIT_USERNAME': os.environ.get('REDDIT_USERNAME'),
        'REDDIT_PASSWORD': os.environ.get('REDDIT_PASSWORD'),
        'CLIENT_ID': os.environ.get('CLIENT_ID'),
        'CLIENT_SECRET': os.environ.get('CLIENT_SECRET'),
        'USER_AGENT': os.environ.get('USER_AGENT'),
        'OPENROUTER_API_KEY': os.environ.get('OPENROUTER_API_KEY')
    }
    
    for var, value in required_vars.items():
        if not value:
            missing_items.append(f'Environment variable: {var}')
    
    if missing_items:
        log_error("Missing required items:")
        for item in missing_items:
            log_error(f"- {item}")
        return False
    
    return True

def main():
    print_banner()
    log_info("Bot initialization started")
    
    while True:
        try:
            # Check daily comment limit
            daily_comments = get_daily_comment_count()
            if daily_comments >= BOT_CONFIG['max_daily_comments']:
                log_warning(f"Daily comment limit ({BOT_CONFIG['max_daily_comments']}) reached. Waiting until tomorrow...")
                time.sleep(3600)  # Sleep for an hour before checking again
                continue
                
            subreddits = load_subreddits()
            cycle_count = 1
            commented_posts = load_commented_posts()
            
            log_info(f"Starting cycle #{cycle_count}")
            log_info(f"Currently tracking {len(commented_posts)} commented posts")
            
            for subreddit_name in subreddits:
                successful_posts = 0
                log_info(f"Processing subreddit: r/{subreddit_name}")
                
                reddit_posts = get_reddit_posts(subreddit_name, commented_posts)
                if reddit_posts is None:
                    continue

                for post in reddit_posts:
                    try:
                        if not is_valid_post(post) or post.id in commented_posts:
                            continue

                        log_info(f"Processing post: {post.title[:50]}...")
                        
                        chatgpt_response = get_chatgpt_answer(post.title)
                        if not chatgpt_response:
                            continue
                            
                        comment = post.reply(body=chatgpt_response)
                        comment_link = f"https://reddit.com{comment.permalink}"
                        
                        log_success(f"Successfully commented on post in r/{subreddit_name}")
                        log_success(f"Comment link: {comment_link}")
                        
                        save_comment_link(subreddit_name, post.title, comment_link)
                        commented_posts.add(post.id)
                        
                        successful_posts += 1

                        # Sleep between posts (increased for rate limiting)
                        sleep_time = random.randint(BOT_CONFIG['min_sleep_seconds'], BOT_CONFIG['max_sleep_seconds'])
                        log_info(f"Sleeping for {sleep_time} seconds...")
                        time.sleep(sleep_time)

                    except Exception as e:
                        error_message = str(e)
                        if "RATELIMIT" in error_message:
                            if not handle_rate_limit(error_message):
                                break
                        else:
                            log_error(f"Error posting comment: {error_message}")
                            time.sleep(60)  # Wait 1 minute before next attempt

                log_success(f"Completed {successful_posts} comments in r/{subreddit_name}")
                
            log_success(f"Completed cycle #{cycle_count}")
            cycle_count += 1
            
            log_info(f"Taking a {BOT_CONFIG['cycle_sleep_minutes']}-minute break before starting next cycle...")
            time.sleep(BOT_CONFIG['cycle_sleep_minutes'] * 60)
            
        except KeyboardInterrupt:
            log_info("Bot shutdown initiated by user")
            return
        except Exception as e:
            log_error(f"Unexpected error in main loop: {str(e)}")
            log_error(traceback.format_exc())
            time.sleep(300)  # Sleep for 5 minutes before retrying

if __name__ == "__main__":
    try:
        print("Script starting...")
        print("Current working directory:", os.getcwd())
        print_banner()
        log_info("Starting setup verification...")
        
        # Verify setup before starting
        if not verify_setup():
            log_error("Setup verification failed. Please fix the issues above and try again.")
            exit(1)
            
        # Initialize Reddit instance for verification
        reddit = praw.Reddit(
            client_id=os.environ["CLIENT_ID"],
            client_secret=os.environ["CLIENT_SECRET"],
            password=os.environ["REDDIT_PASSWORD"],
            user_agent=os.environ["USER_AGENT"],
            username=os.environ["REDDIT_USERNAME"]
        )
        
        # Verify account status
        if not verify_account_status(reddit):
            log_error("Account verification failed. Please check the requirements above.")
            exit(1)
        
        log_info("Setup verification successful!")
        log_info("Environment variables loaded:")
        log_info(f"Username: {os.environ.get('REDDIT_USERNAME')}")
        log_info(f"User Agent: {os.environ.get('USER_AGENT')}")
        log_info(f"Client ID: {os.environ.get('CLIENT_ID')[:5]}...")
        
        # Initialize comment history file
        initialize_comment_history()
        
        main()
    except KeyboardInterrupt:
        log_info("Bot shutdown initiated by user")
        print(f"\n{Fore.CYAN}Thank you for using Reddit Bot by {BOT_AUTHOR}!{Style.RESET_ALL}")
    except Exception as e:
        log_error(f"Fatal error: {str(e)}")
        log_error(traceback.format_exc())
