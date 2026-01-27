# 🚀 Deploy to Streamlit Cloud - Step-by-Step Guide

Your code is now ready! Follow these 4 steps to deploy.

## **STEP 1: Create a GitHub Repository**

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `IPL_analytics_ai`
3. **Description** (optional): "IPL Cricket Analytics with 2025 data"
4. **Make it PUBLIC** (required for free Streamlit Cloud)
5. Click **"Create repository"**

---

## **STEP 2: Push Code to GitHub**

Copy these commands from your new GitHub repo and run them in terminal:

```bash
cd /Users/vikrant/Desktop/IPL_analytics_ai

git branch -M main

git remote add origin https://github.com/YOUR_USERNAME/IPL_analytics_ai.git

git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username.

---

## **STEP 3: Deploy on Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Deploy an app"** button
3. Fill in these fields:
   - **GitHub repo owner**: YOUR_USERNAME
   - **Repository**: IPL_analytics_ai
   - **Branch**: main  
   - **Main file path**: app.py
4. Click **"Deploy"** button

Streamlit will now build and deploy your app (takes 2-3 minutes).

---

## **STEP 4: Add Your OpenAI API Key**

Once deployed, your app needs the OpenAI API key:

1. In your app on Streamlit Cloud, click the **⋮ (menu)** button (top right)
2. Click **"Settings"**
3. Click **"Secrets"** tab
4. Paste this:
```
OPENAI_API_KEY = "sk-proj-YOUR_ACTUAL_API_KEY_HERE"
```
5. Replace with your actual OpenAI key from your account
6. Click **"Save"**

The app will **auto-restart** with your secret.

---

## **✅ Done!**

Your app is now live! You'll get a public URL like:
```
https://ipl-analytics-ai.streamlit.app
```

Share this URL with anyone to test your app!

---

## **💡 Useful Links**

- **App Dashboard**: https://share.streamlit.io/admin/apps
- **Streamlit Docs**: https://docs.streamlit.io
- **View App Logs**: Click your app → "Manage app" → "Logs"

---

## **🔧 If Something Goes Wrong**

**App shows errors?**
- Check the **Logs** in app settings
- Verify OpenAI key is added in Secrets
- Make sure all files committed to GitHub

**Need to update code?**
- Make changes locally
- `git add .` and `git commit`
- `git push` to GitHub
- Streamlit auto-deploys!

---

Enjoy your live IPL Analytics AI app! 🏏
