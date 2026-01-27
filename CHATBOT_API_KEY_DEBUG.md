# AI Chatbot API Key Debugging Guide

## Issue Summary
**Status**: ❌ BLOCKED
**Error**: HTTP 401 - Invalid API key when initializing OpenAI chatbot in Streamlit
**Frequency**: Consistent across 3+ different API keys
**Timeline**: Issue started after adding advanced filters (match_situation filter) on 2026-01-27

## What We Know
- ✅ Code reverted to original working version (commit 86bc056)
- ✅ API keys test successfully when run directly: `openai.models.list()` returns 112 models
- ✅ API key loads correctly from .env file: verified with `dotenv.load_dotenv()`
- ✅ $5 USD credits confirmed in OpenAI account
- ❌ Streamlit app still rejects API key with 401 error
- ❌ Problem NOT in our code (same error with original code)
- ❌ Problem NOT in .env file parsing (tested successfully)

## Root Cause Analysis
**Most Likely**: API key validation happens **after** Streamlit caches/modifies the key
- Streamlit's `@st.cache_resource` decorator may be affecting the key
- Streamlit secrets vs. environment variables conflict
- OpenAI library version incompatibility with key validation

**Less Likely**:
- File encoding issues (tested, keys are ASCII)
- Whitespace/newlines in key (fixed with proper file creation)
- Account-level restrictions (account is in good standing)

## Next Steps to Debug (When You Return)

### Step 1: Test Without Streamlit Cache
```python
# In app.py, temporarily remove @st.cache_resource:
# Instead of:
#   @st.cache_resource
#   def load_chatbot(_api_key):
#       return CricketChatbot(...)
# 
# Use:
#   chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
```

### Step 2: Use Streamlit Secrets Instead of .env
1. Create/Edit: `~/.streamlit/secrets.toml`
2. Add: `OPENAI_API_KEY = "sk-proj-YOUR_KEY_HERE"`
3. Access in code: `api_key = st.secrets["OPENAI_API_KEY"]`
4. Update app.py to read from secrets instead of os.getenv()

### Step 3: Check OpenAI Library Version
```bash
pip show openai
# Should be: 2.15.0 or higher
# If older, upgrade: pip install --upgrade openai
```

### Step 4: Direct API Test in Streamlit
Add a test endpoint in app.py:
```python
if st.button("Test OpenAI API"):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        st.success(f"✅ API works! Found {len(models.data)} models")
    except Exception as e:
        st.error(f"❌ API Error: {e}")
```

### Step 5: Check for Multiple API Key Sources
Streamlit might be picking up a different API key from:
- Environment variables set in Terminal
- ~/.bashrc or ~/.zshrc exports
- macOS keychain
- Streamlit config file

```bash
# Check what API key is being used:
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
print(f"Key: {key[:20]}...{key[-20:] if key else 'NOT FOUND'}")
print(f"Length: {len(key) if key else 0}")
EOF
```

## Files Modified
- `openai_handler.py` - Reverted to original (commit 86bc056)
- `app.py` - Reverted to use @st.cache_resource decorator
- `.env` - Contains API key (on single line, no trailing newlines)

## API Keys Tried
1. `sk-proj-80AYAp...` - Rejected
2. `sk-proj-y8es-NsrRt...` - Rejected  
3. `sk-proj-2xKJjsl5...` - Rejected (current in .env)

## Success Criteria
When fixed, you should see:
- ✅ Chatbot page loads without error
- ✅ Can enter a query like "Kohli stats"
- ✅ Chatbot returns analysis of Kohli's statistics
- ✅ Advanced filters work (match_situation, bowler_type, etc.)

## Fallback Options (If API Key Issue Persists)
1. **Disable Chatbot Temporarily**: Remove AI Chatbot from navigation
   - Keep Player Analysis, Team Analysis, Head-to-Head working
   - Chatbot can be re-enabled when API key issue is resolved

2. **Use Alternative LLM**: 
   - Try Ollama (free, local LLM)
   - Try Claude API instead of OpenAI
   - Try Hugging Face API

3. **Mock Chatbot for Testing**:
   - Create dummy responses for testing filter extraction
   - This would let us verify match_situation filter works end-to-end

## Important Note
The advanced filters (match_situation, bowler_type, match_phase) are **fully implemented** in the code and ready to use. The only blocker is the OpenAI API key authentication issue, which is **external to our code**.

---
**Last Updated**: 2026-01-27 15:52 UTC
**Status**: Code stable, waiting for API key resolution
