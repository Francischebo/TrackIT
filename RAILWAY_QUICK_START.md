# 🚀 Railway Deployment - Quick Start (10 Minutes)

Deploy TrackIT backend to Railway in 10 minutes.

---

## ✅ Prerequisites

- GitHub account with TrackIT repository pushed
- Railway account (free): https://railway.app
- Supabase credentials ready
- Generated SECRET_KEY and JWT_SECRET_KEY

---

## 📋 Quick Steps

### 1️⃣ Create Railway Account (2 min)

```
https://railway.app → Sign up with GitHub → Authorize
```

### 2️⃣ New Project (1 min)

```
Railway Dashboard → "New Project" → "Deploy from GitHub"
```

### 3️⃣ Select Repository (1 min)

```
Search "TrackIT" or "Francischebo/TrackIT" → Select → Deploy
```

### 4️⃣ Add Environment Variables (3 min)

In Railway dashboard, go to **"Variables"** and add:

```env
FLASK_ENV=production
FLASK_APP=run.py
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=<paste-your-generated-key>
JWT_SECRET_KEY=<paste-your-generated-jwt-key>
CORS_ORIGINS=https://localhost:3000,https://yourdomain.com
BCRYPT_LOG_ROUNDS=12
FORCE_HTTPS=False
DEBUG=False
```

Save → Done!

### 5️⃣ Deploy (2 min)

```
Click "Deploy" button → Wait for green checkmark → Done!
```

### 6️⃣ Get Your URL (1 min)

```
Railway Dashboard → Your Project → "Domains" tab → Copy URL
```

Example: `https://trackit-production.up.railway.app`

---

## ✅ Verify It's Working

```bash
curl https://trackit-production.up.railway.app/health
```

Expected:
```json
{"success":true,"status_code":200,"message":"OK"}
```

---

## 🎯 That's It!

Your backend is now live on Railway! 🎉

### Next:
1. Test the health endpoint ✅
2. Update frontend to use Railway URL
3. Configure custom domain (optional)
4. Set up monitoring

---

## 📚 Need More Help?

See full guide: `RAILWAY_DEPLOYMENT_GUIDE.md`

**Common Issues:**
- "Build failed" → Check `requirements.txt` in backend folder
- "Connection timeout" → Verify `DATABASE_URL_PROD` is correct
- "503 Service Unavailable" → Wait 30 seconds, Railway is starting up

---

**Time to Deploy**: ⏱️ 10 minutes  
**Cost**: 💰 Free (or $5/month hobby tier)  
**Complexity**: 🟢 Easy
