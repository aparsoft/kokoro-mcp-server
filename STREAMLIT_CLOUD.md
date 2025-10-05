# Streamlit Cloud Deployment Guide

## Quick Deploy to Streamlit Cloud (FREE)

Streamlit offers free cloud hosting for public apps at https://share.streamlit.io

---

## Method 1: Deploy Button (Easiest)

### From Running App

1. **Run your Streamlit app locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Click the Deploy button:**
   - Look for **☰ (hamburger menu)** in top-right corner
   - Click **"Deploy this app"**
   - Follow the prompts

3. **Connect GitHub:**
   - Sign in with GitHub account
   - Authorize Streamlit
   - Select repository
   - Choose branch (usually `main`)
   - Set main file path: `streamlit_app.py`
   - Click **Deploy!**

---

## Method 2: Direct from Streamlit Cloud

### Step-by-Step

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add Streamlit app"
   git push origin main
   ```

2. **Go to Streamlit Cloud:**
   - Visit https://share.streamlit.io
   - Click **"New app"**

3. **Configure deployment:**
   - **Repository:** `your-username/youtube-creator`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`

4. **Click "Deploy!"**
   - Streamlit will install dependencies automatically
   - App will be live at: `https://share.streamlit.io/your-username/youtube-creator/main/streamlit_app.py`

---

## Required Files for Deployment

### 1. requirements.txt (REQUIRED)

Create `requirements.txt` in project root:

```txt
# Core TTS dependencies
kokoro>=0.9.2
soundfile>=0.12.1
librosa>=0.10.0
numpy>=1.24.0,<2.0.0
scipy>=1.10.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
structlog>=24.0.0
python-json-logger>=2.0.7

# Streamlit dependencies
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.0.0
pyarrow>=14.0.0
```

**Note:** Streamlit Cloud uses `requirements.txt`, not `pyproject.toml`

### 2. packages.txt (for system dependencies)

Create `packages.txt` in project root:

```txt
espeak-ng
ffmpeg
libsndfile1
```

### 3. .streamlit/config.toml (already created)

Already exists at `.streamlit/config.toml` with theme settings.

---

## Streamlit Cloud Secrets

For sensitive data (API keys, tokens), use Streamlit Secrets:

1. **In Streamlit Cloud dashboard:**
   - Go to your app settings
   - Click **"Secrets"**
   - Add your secrets in TOML format:

```toml
# Example secrets
[tts]
api_key = "your-api-key-here"
custom_model_path = "/path/to/model"

[logging]
log_level = "INFO"
```

2. **Access in your app:**
```python
import streamlit as st

# Access secrets
api_key = st.secrets["tts"]["api_key"]
```

---

## Important Notes for Deployment

### ⚠️ Model Size Limitations

**Streamlit Cloud Free Tier:**
- **1 GB RAM** per app
- **800 MB slug size** (total app size)

**Kokoro-82M Model:**
- ~200-300MB download
- ~2GB RAM when loaded

**Problem:** Kokoro requires more RAM than free tier provides.

### Solutions:

#### Option 1: Use Streamlit Cloud Teams (Paid)
- Upgrade to Teams plan ($20+/month)
- Get 4GB+ RAM
- Full feature support

#### Option 2: Deploy Core Features Only
Modify `streamlit_app.py` to use lighter features:
- Remove model loading
- Show UI only
- Use API backend for actual generation

#### Option 3: Use Alternative Hosting
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- AWS EC2 (full control)
- Google Cloud Run (serverless)
- Heroku (platform-as-a-service)
- Docker deployment (self-hosted)

---

## Recommended: Alternative Deployment

For this TTS app with large models, we recommend:

### Option A: AWS EC2 (Best for this app)

```bash
# Launch t2.medium or larger (4GB+ RAM)
# SSH into instance
git clone <your-repo>
cd youtube-creator
pip install -e ".[complete]"
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

**Cost:** ~$30-40/month for t2.medium

### Option B: Docker + Cloud Run

See `DEPLOYMENT_GUIDE.md` for complete Docker setup.

### Option C: Self-Hosted

Run on your own server:
```bash
# Use systemd service (see DEPLOYMENT_GUIDE.md)
sudo systemctl start aparsoft-tts-streamlit
```

---

## Testing Deployment Locally

Before deploying, test as if on Streamlit Cloud:

```bash
# 1. Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate

# 2. Install from requirements.txt only
pip install -r requirements.txt

# 3. Test system packages
sudo apt-get install espeak-ng ffmpeg libsndfile1

# 4. Run app
streamlit run streamlit_app.py

# 5. Check RAM usage
# Should be under 800MB if targeting free tier
```

---

## Deployment Checklist

### Before Deploying

- [ ] Code pushed to GitHub (public or private repo)
- [ ] `requirements.txt` created and tested
- [ ] `packages.txt` created if needed
- [ ] `.streamlit/config.toml` configured
- [ ] Secrets configured (if needed)
- [ ] Tested locally with only requirements.txt
- [ ] Checked RAM usage
- [ ] Reviewed Streamlit Cloud limits

### During Deployment

- [ ] Connected GitHub account
- [ ] Selected correct repository and branch
- [ ] Set correct main file path
- [ ] Configured secrets (if needed)
- [ ] Clicked Deploy

### After Deployment

- [ ] App builds successfully
- [ ] All features work
- [ ] No memory errors
- [ ] Performance acceptable
- [ ] Custom domain configured (optional)

---

## Streamlit Cloud Features

### Free Tier
- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ GitHub integration
- ✅ Auto-deployment
- ✅ Community support
- ✅ Custom subdomains

### Teams/Enterprise (Paid)
- ✅ Private apps
- ✅ 4+ GB RAM
- ✅ Custom domains
- ✅ Priority support
- ✅ SSO authentication
- ✅ Advanced analytics

---

## Troubleshooting

### "Requirements too large"

**Solution:**
```bash
# Use lighter dependencies
# Remove unused packages from requirements.txt
```

### "Out of memory"

**Solution:**
- Upgrade to Teams plan
- Or use alternative hosting (AWS, GCP)
- Or reduce model size

### "App won't start"

**Check:**
1. `requirements.txt` has all dependencies
2. `packages.txt` has system dependencies
3. Main file path is correct
4. No syntax errors in code

### "Model download fails"

**Solution:**
```python
# Cache model download
@st.cache_resource
def load_model():
    return TTSEngine()
```

---

## Example Deployment

### 1. Create requirements.txt

```bash
# In project root
cat > requirements.txt << EOF
kokoro>=0.9.2
soundfile>=0.12.1
librosa>=0.10.0
numpy>=1.24.0,<2.0.0
scipy>=1.10.0
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.0.0
pyarrow>=14.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
EOF
```

### 2. Create packages.txt

```bash
cat > packages.txt << EOF
espeak-ng
ffmpeg
libsndfile1
EOF
```

### 3. Push to GitHub

```bash
git add requirements.txt packages.txt
git commit -m "Add deployment files"
git push origin main
```

### 4. Deploy

- Go to https://share.streamlit.io
- Click "New app"
- Select repository
- Deploy!

---

## URLs After Deployment

Your app will be available at:
```
https://share.streamlit.io/[username]/[repo]/[branch]/streamlit_app.py
```

Or with custom domain:
```
https://your-custom-domain.com
```

---

## Cost Comparison

| Platform | RAM | Storage | Cost/Month |
|----------|-----|---------|------------|
| **Streamlit Cloud Free** | 1 GB | 800 MB | $0 |
| **Streamlit Teams** | 4 GB | - | $20-250 |
| **AWS EC2 t2.medium** | 4 GB | 30 GB | $35 |
| **GCP Cloud Run** | 4 GB | - | ~$10-40 |
| **Heroku** | 512 MB | - | $7+ |
| **Self-Hosted** | Custom | Custom | Server cost |

---

## Recommendation

**For this TTS app:**

❌ **Don't use:** Streamlit Cloud Free (insufficient RAM)

✅ **Do use:**
1. **AWS EC2** (best control, predictable cost)
2. **Streamlit Teams** (easiest, good support)
3. **Self-Hosted** (cheapest long-term)

See `DEPLOYMENT_GUIDE.md` for complete production deployment instructions.

---

## Support

- **Streamlit Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Streamlit Forum:** https://discuss.streamlit.io
- **Streamlit Cloud:** https://share.streamlit.io

---

**Note:** While Streamlit Cloud is great for many apps, this TTS app with Kokoro-82M model is better suited for platforms with more RAM (4GB+). Consider AWS EC2, Google Cloud Run, or self-hosting for production use.
