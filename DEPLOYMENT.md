# Deployment Guide: Open-Source & Free Cloud Hosting

This system packages the **FastAPI REST API**, **Trained TensorFlow LSTM Model**, and the **Compiled React Dashboard** into a unified web application served on a single port.

---

## Option 1: Hugging Face Spaces (Recommended for AI / Open-Source)

[Hugging Face Spaces](https://huggingface.co/spaces) is the leading open-source ML hosting platform. It provides **free 16 GB RAM + 2 vCPUs**, generous bandwidth, and a free permanent `https://*.hf.space` HTTPS link.

### Steps:

1. **Sign in to Hugging Face**: Go to [huggingface.co](https://huggingface.co) (free account).
2. **Create a New Space**:
   - Click your profile icon -> **New Space**.
   - Choose a name (e.g. `tn-flood-prediction`).
   - Space SDK: Choose **Docker** -> **Blank**.
   - Visibility: **Public**.
3. **Push the project**:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/tn-flood-prediction
   git add .
   git commit -m "Deploy Tamil Nadu Flood Prediction System"
   git push space main
   ```
4. Hugging Face will automatically detect the [Dockerfile](file:///e:/MiniProject/demo1/Dockerfile), build the container, seed the database, and launch your live application at `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/tn-flood-prediction`.

---

## Option 2: Self-Hosting with Coolify or Dokku (100% Open-Source PaaS)

If you have a Linux VPS (or an on-premise server), you can use open-source self-hosted platforms like **Coolify** or **Dokku**.

### Using Coolify:
1. In your Coolify dashboard, click **Add Application** -> **Public/Private Git Repository**.
2. Select your repository URL.
3. Coolify detects the `Dockerfile` automatically.
4. Set port to `7860` or `8000` and click **Deploy**.

### Using Dokku:
```bash
# On your Dokku server:
dokku apps:create flood-prediction
# On your local machine:
git remote add dokku dokku@your-server-ip:flood-prediction
git push dokku main
```

---

## Option 3: Render (Free Cloud Hosting via GitHub)

Render provides a free tier for web services connected directly to GitHub repositories.

1. Push your repository to [GitHub](https://github.com).
2. Log in to [render.com](https://render.com) and click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Render will read `render.yaml` automatically:
   - **Build Command**: `pip install -r requirements.txt && python scripts/init_database.py`
   - **Start Command**: `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**. Your app is live at `https://<your-service>.onrender.com`.

---

## Option 4: Instant Live Public URL (In 30 Seconds via Localtunnel)

If you need a public URL immediately to share or demo from your machine without creating cloud accounts:

1. **Start the backend server in Terminal 1:**
   ```powershell
   uvicorn src.api.app:app --host 127.0.0.1 --port 8000
   ```
2. **Expose it to the web in Terminal 2:**
   ```powershell
   npx localtunnel --port 8000
   ```
3. Localtunnel will output a public HTTPS link (e.g. `https://quiet-river-42.loca.lt`) accessible from any browser anywhere.
