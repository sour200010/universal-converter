# ⚡ Universal Document & Image Engine

A high-performance, local-first document converter, PDF optimizer, and image processing suite built with **Next.js** and **FastAPI**.

Unlike online cloud alternatives, this engine runs **100% locally on your machine**. Your files never touch an external server or cloud storage bucket.

---

## 🔒 Why This Project?

- **Complete Data Privacy:** All document operations occur inside your local environment (`localhost`). Financial files, legal contracts, identity documents, and personal photos remain strictly private.
- **Zero Subscriptions or Paywalls:** No daily conversion quotas, file count restrictions, or paywalls.
- **Immediate Post-Download Wipe:** Converted and uploaded artifacts are purged immediately after download completion, supplemented by an automatic 30-minute background sweeper.
- **Production-Grade Defenses:** Built-in magic-byte validation (detects disguised payloads), 50 MB chunked stream limits to prevent RAM exhaustion, path traversal sanitization, and macro-disabled execution.

---

## 🛠️ Supported Tools

| Tool | Capabilities |
| :--- | :--- |
| **PDF to Office** | Converts PDF pages into editable `.docx`, `.xlsx`, or `.pptx` documents with formatting retention. |
| **Office to PDF** | Converts Word (`.docx`), Excel (`.xlsx`), and PowerPoint (`.pptx`) directly to PDF. |
| **3-Tier PDF Compression** | **Extreme** (maximum size reduction), **Recommended** (balanced quality/size), or **Less** (preserves maximum clarity). |
| **Image Resizer & Optimizer** | Resize by **pixels, inches, cm, or mm**, dynamic aspect-ratio locking, target file size capping (**KB**), and conversion between JPEG, PNG, and WEBP. |
| **Image to PDF** | Combines single or multiple images into a unified, clean PDF. |

---

## 🚀 How to Run the Application

You can launch the entire stack using **Docker** (recommended) or set it up **manually** with Python and Node.js.

### Prerequisites

- [Git](https://git-scm.com/) installed
- For Docker: [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- For Manual Setup: **Python 3.10+** and **Node.js 18+** installed

---

### Option 1: Run with Docker (Recommended)

Docker packages Python, headless LibreOffice, system fonts, and the Next.js runtime into isolated containers with a single command.

1. **Clone the repository:**
Bash
   git clone [https://github.com/YOUR_USERNAME/universal-converter.git](https://github.com/YOUR_USERNAME/universal-converter.git)
   cd universal-converter

2. **Start the containers:**

Bash
docker compose up --build

3. **Open the application:**
Navigate to http://localhost:3000 in your browser.

To stop the containers at any point:

Bash
docker compose down

**Option 2: Manual Local Setup (Without Docker)**
**1. Backend Service (FastAPI)**
Open a terminal window:

cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Start the API server
python -m uvicorn main:app --reload --port 8000

The backend API will run on http://127.0.0.1:8000.

**2. Frontend Dashboard (Next.js)**
Open a separate terminal window:

Bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
The web interface will run on http://localhost:3000.

🖥️ How to Use
Choose a Tool: Select an action from the top navigation grid (e.g., PDF to Word, Compress PDF, Resize & Compress Image).

Add Files: Drag and drop your documents/images into the upload zone, or click to browse files. Multi-file batch processing is supported.

Configure Options:

PDF Compression: Choose between Extreme, Recommended, or Less Compression.

Image Resizer: Select your preferred unit (px, in, cm, mm), toggle the aspect ratio lock, or set a maximum target file size in KB.

Convert & Download: Click Convert Batch / Process File. Files are converted and downloaded directly to your computer.

Instant Wipe (Optional): Click Delete Files from Server Now at any time to immediately scrub all working job files from the temporary storage directory.

🛡️ Security Architecture
Sandboxed Processing: Files exist in a temporary working directory solely for execution and are isolated by random UUID namespaces.

Execution Hardening: Office automation forces AutomationSecurity = 3 to neutralize embedded VBA macros.

Rate Limiting: Guarded by slowapi to prevent bot spam and denial-of-service abuse.

📄 License
Distributed under the MIT License. Free for personal, educational, and open-source usage.


---

### How to Save & Push It to GitHub

Run these commands in your VS Code terminal (from the project root folder):

```powershell
git add README.md
git commit -m "docs: add comprehensive README with setup and user instructions"
git push origin main
