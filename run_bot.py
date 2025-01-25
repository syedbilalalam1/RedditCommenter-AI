#!/usr/bin/env python3
import subprocess
import time
import sys
import os

def run_bot():
    while True:
        try:
            # Run the bot
            process = subprocess.Popen([sys.executable, 'app.py'])
            process.wait()
            
            # If the bot crashes, wait 5 minutes before restarting
            time.sleep(300)
        except Exception as e:
            print(f"Error running bot: {e}")
            time.sleep(300)

if __name__ == "__main__":
    run_bot() 