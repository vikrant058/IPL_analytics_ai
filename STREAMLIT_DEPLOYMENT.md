# 🏏 IPL Analytics AI - Streamlit Cloud Deployment Guide

## Quick Deployment (5 minutes)

### Step 1: Push to GitHub
```bash
# Initialize git (if not already)
git init
git add .
git commit -m "IPL Analytics AI - Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/IPL_analytics_ai.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Deploy an app"**
3. Select:
   - **GitHub repo**: YOUR_USERNAME/IPL_analytics_ai
   - **Branch**: main
   - **Main file path**: app.py
4. Click **"Deploy!"**

### Step 3: Add Secrets (OpenAI API Key)
1. In Streamlit Cloud dashboard, click your app
2. Click **Settings** (gear icon) → **Secrets**
3. Paste your OpenAI API key:
```
OPENAI_API_KEY = "sk-proj-YOUR_ACTUAL_KEY_HERE"
```
4. Save → App auto-restarts

### Step 4: Share Your Link
Once deployed, you'll get a public URL like:
```
https://ipl-analytics-ai.streamlit.app
```

Share this link with anyone to test!

---

## Features Available

✅ **Player Analysis** - Stats, trends, top performers
✅ **Team Analysis** - Performance metrics, home/away stats
✅ **AI Chatbot** - Natural language queries with season filters
✅ **Head-to-Head** - Player comparisons
✅ **2025 IPL Data** - Latest season included (74 matches)
✅ **1,169 Matches** - Complete 2008-2025 history

---

## Data Included

- **Matches**: 1,169 (2008-2025)
- **Deliveries**: 278,205 ball-by-ball data
- **Teams**: 10 active IPL franchises
- **Venues**: 59 stadiums worldwide
- **Players**: 1,000+ unique batters & bowlers

---

## Environment Variables Required

- `OPENAI_API_KEY`: Your OpenAI API key (for chatbot)

---

## Troubleshooting

**Issue**: App says "No API key found"
- **Solution**: Add `OPENAI_API_KEY` in Streamlit Cloud Secrets

**Issue**: Data loading slowly
- **Solution**: First load caches data, subsequent loads are instant

**Issue**: Want to update data?
- **Solution**: Re-run the merge scripts locally, commit to GitHub, redeploy

---

## Local Development

```bash
# Install dependencies
pip install -r requirement.txt

# Run locally
streamlit run app.py

# Visit: http://localhost:8501
```

---

Created with ❤️ for IPL Analytics
