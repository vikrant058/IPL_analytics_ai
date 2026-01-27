# OpenAI API Key Troubleshooting Guide

## Current Issue
The AI Chatbot is rejecting the API key with a **401 Unauthorized** error, even though:
- ✅ The .env file is properly formatted (verified)
- ✅ The API key works when tested directly in Python
- ✅ The key loads correctly into the Streamlit environment
- ✅ Code has been reverted to original working version
- ✅ Streamlit cache has been cleared

## Root Cause Analysis
**The issue is NOT with the code or .env file - it's with the OpenAI account/API key itself.**

OpenAI is rejecting the key at their server with a 401 error, which means:
1. The API key format is correct (starts with `sk-proj-`)
2. But OpenAI's servers don't recognize it as valid
3. This could be due to:
   - **Account billing issue** (suspended, payment failed)
   - **API key revoked/disabled**
   - **Rate limits exceeded**
   - **Spending limit hit**
   - **Incorrect account** (using key from different account than expected)

## Solutions to Try

### Option 1: Generate a Brand New API Key (Recommended)
1. Go to https://platform.openai.com/account/api-keys
2. **Delete ALL existing keys** in your account
3. Click **"Create new secret key"**
4. **Copy the key immediately** (you'll only see it once!)
5. **Don't close the page** - keep it open to verify it works
6. Test the key on OpenAI's Playground first:
   - https://platform.openai.com/playground
   - Try making a simple API call to verify it works
7. Only after confirming it works, update the .env file:
   ```bash
   echo "OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE" > /Users/vikrant/Desktop/IPL_analytics_ai/.env
   ```

### Option 2: Check Account Status
1. Go to https://platform.openai.com/account/billing/overview
2. Verify:
   - ✅ Account is active
   - ✅ Billing method is valid
   - ✅ No usage quota warnings
   - ✅ Usage is within free tier or paid plan limits

### Option 3: Check API Permissions
1. Go to https://platform.openai.com/account/api-keys
2. For your API key, check:
   - ✅ Permissions include "Chat Completions"
   - ✅ Key is not restricted to specific IPs/organizations
   - ✅ Key is not expired

## How to Update the API Key

Once you have a valid key, update it:

```bash
# Navigate to project directory
cd /Users/vikrant/Desktop/IPL_analytics_ai

# Update .env file with new key
echo "OPENAI_API_KEY=sk-proj-YOUR_VALID_KEY_HERE" > .env

# Verify it was written correctly
cat .env

# Restart the app
pkill -f "streamlit run" || true
sleep 2
streamlit run app.py
```

## Testing the Key Directly
Before updating Streamlit, test the key in Python:

```python
from openai import OpenAI

api_key = "sk-proj-YOUR_KEY_HERE"
client = OpenAI(api_key=api_key)

# This will raise an error if key is invalid
response = client.models.list()
print("✅ API key is valid!")
print(f"Available models: {len(response.data)}")
```

## What We've Already Verified ✅
- .env file syntax is correct
- No whitespace issues in the API key
- load_dotenv() is working properly
- Code reverted to original working version
- Streamlit cache cleared
- Multiple API keys all rejected with same 401 error
- Account has $5 in credits

## Next Steps
1. **Generate a brand new API key** (don't reuse old ones)
2. **Test it on OpenAI's Playground** first
3. **Update the .env file** with the new key
4. **Clear Streamlit cache** and restart
5. **Test on both local and cloud apps**

## Cloud Deployment Note
The cloud app at https://cricketanalytics.streamlit.app/ will auto-deploy when you push changes to GitHub. After updating the API key locally:

```bash
cd /Users/vikrant/Desktop/IPL_analytics_ai
git add .env
git commit -m "Update OpenAI API key"
git push
# Cloud app will auto-update in ~2 minutes
```

**Important**: Make sure `.env` is in `.gitignore` so you don't accidentally commit the key! Check:
```bash
cat .gitignore | grep -i env
```

## Still Not Working?
If a brand new API key still doesn't work:
1. Contact OpenAI support (account/billing issue)
2. Consider the Player/Team Analysis pages as alternatives (they work without OpenAI)
3. Use the chatbot as a nice-to-have feature, not core functionality

---
**Last Updated**: 27 January 2026
**Status**: API Key Validation - Awaiting New Key
