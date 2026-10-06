# 🚀 Universal Document & Image Engine

A privacy-focused, native-speed document conversion and image optimization platform built with Next.js and FastAPI.

## ✨ Features
- **PDF Operations:** PDF to Word (.docx), Excel (.xlsx), and PowerPoint (.pptx).
- **Office to PDF:** Word, Excel, and Slides to PDF with native rendering.
- **3-Tier PDF Compression:** Extreme, Recommended, and Low compression modes.
- **Image Optimizer:** Resize by pixels, inches, cm, and mm with locked aspect ratio and KB target capping.
- **Privacy Sandboxed:** Zero cloud retention — files are purged from disk post-download.

## 🛠️ Quickstart

### 1. Backend (FastAPI)
\`\`\`bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
\`\`\`

### 2. Frontend (Next.js)
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`
Visit \`http://localhost:3000\`.

### 🐳 Run with Docker
\`\`\`bash
docker compose up --build
\`\`\`

## 📄 License
MIT License - Free for personal and commercial use.