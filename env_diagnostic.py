import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def diagnose_env_file():
    print("🔍 Environment Variable Diagnostic Tool 🔍")
    
    # Current working directory
    print(f"\n📂 Current Working Directory: {os.getcwd()}")
    
    # Potential .env file locations
    potential_locations = [
        Path.cwd() / '.env',
        Path(__file__).parent / '.env',
        Path.home() / '.env'
    ]
    
    print("\n🔎 Searching for .env file...")
    env_file = None
    for location in potential_locations:
        print(f"Checking: {location}")
        if location.exists():
            env_file = location
            print(f"✅ Found .env file at: {env_file}")
            break
    
    if not env_file:
        print("❌ No .env file found!")
        return
    
    # Load environment variables
    try:
        load_dotenv(dotenv_path=env_file, override=True)
        print("\n📋 Environment Variables:")
        
        # List of sensitive variables to check
        sensitive_vars = [
            'SLACK_BOT_TOKEN', 
            'SLACK_APP_TOKEN', 
            'SLACK_CHANNEL_ID',
            'OPENAI_API_KEY',
            'SLACK_SIGNING_SECRET'
        ]
        
        for var in sensitive_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive information
                masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else value
                print(f"{var}: {masked_value}")
            else:
                print(f"{var}: ❌ NOT SET")
        
        # Show full .env file contents for debugging
        print("\n📄 Full .env File Contents:")
        with open(env_file, 'r') as f:
            print(f.read())
    
    except Exception as e:
        print(f"❌ Error processing .env file: {e}")

if __name__ == "__main__":
    diagnose_env_file()