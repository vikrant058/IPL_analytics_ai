import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env
DOTENV_PATH = Path('/Users/vikrant/Desktop/IPL_analytics_ai/.env')
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

# Get key
api_key = os.getenv('OPENAI_API_KEY')
print(f"✅ Key loaded: {api_key[:20]}...{api_key[-10:]}")
print(f"✅ Key length: {len(api_key)}")

import openai as openai_module
print(f"✅ OpenAI version: {openai_module.__version__}")

# Test with gpt-4o-mini
try:
    client = OpenAI(api_key=api_key)
    
    # List models
    models = list(client.models.list().data)
    print(f"✅ Can access {len(models)} models")
    
    # Make API call with gpt-4o-mini
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print(f"✅ gpt-4o-mini API call SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
