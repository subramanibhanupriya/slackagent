from dotenv import load_dotenv
import os

def test_env_variables():
    # Load the environment variables
    load_dotenv()
    
    # Get the tokens
    app_token = os.getenv('SLACK_APP_TOKEN')
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Check if tokens exist and print first/last few characters
    if app_token:
        print(f"✓ SLACK_APP_TOKEN found! Starts with: {app_token[:10]}... ends with: ...{app_token[-10:]}")
    else:
        print("❌ SLACK_APP_TOKEN not found!")
        
    if bot_token:
        print(f"✓ SLACK_BOT_TOKEN found! Starts with: {bot_token[:10]}... ends with: ...{bot_token[-10:]}")
    else:
        print("❌ SLACK_BOT_TOKEN not found!")
        
    if openai_key:
        print(f"✓ OPENAI_API_KEY found! Starts with: {openai_key[:10]}... ends with: ...{openai_key[-10:]}")
    else:
        print("❌ OPENAI_API_KEY not found!")

if __name__ == "__main__":
    test_env_variables()
