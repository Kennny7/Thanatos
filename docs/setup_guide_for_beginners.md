# Thanatos AI — Beginner's Setup Guide ("Setup for Dummies")

Welcome to **Thanatos AI**! This guide walks you through every setup step in plain English so you can get the full autonomous AI assistant and job-hunting engine running without hassle.

---

## 1. Quick One-Click Terminal Setup

To run Thanatos directly from **any folder** in Windows Terminal, Command Prompt, or PowerShell without typing long paths:

1. Open PowerShell in the `Thanatos` project folder.
2. Run:
   ```powershell
   .\install_cli.ps1
   ```
3. Open a **new** terminal window and type:
   ```bash
   thanatos
   ```
   *That's it!* Thanatos is now installed on your system PATH just like `python` or `git`.

### Non-Interactive Single Commands:
You can also run instant one-off commands without entering the interactive shell:
```bash
thanatos -c "/status"
thanatos -c "/jobs AI engineer in Pune"
thanatos -c "/audit 127.0.0.1"
```

---

## 2. Setting Up Email Sending (SMTP & Google App Passwords)

When Thanatos finds relevant job openings, it tailors your resume and drafts humanized outreach emails. To actually send them, configure SMTP credentials:

### Step 1: Generate a 16-Character Google App Password
1. In your browser, open Google's App Passwords page:  
   👉 **[https://myaccount.google.com/apppasswords?st_source=ai_mode](https://myaccount.google.com/apppasswords?st_source=ai_mode)**
2. Enter an app name (e.g., `Thanatos AI`) and click **Create**.
3. Google will show a **16-character code** (like `abcd efgh ijkl mnop`). Copy this code (spaces don't matter).

### Step 2: Configure in Thanatos
In the Thanatos terminal, run:
```text
/smtp set smtp.gmail.com 587 your_email@gmail.com YOUR_16_CHAR_CODE
```
Thanatos will test the connection and confirm:
```text
[✓] SMTP credentials updated for your_email@gmail.com@smtp.gmail.com:587
[✓] Connected to smtp.gmail.com:587 and verified authentication!
```

---

## 3. Resume and Cover Letter Attachments (Automatic PDF Generation)

Thanatos **never sends plain `.tex` or `.md` files** to employers.
- When searching and applying for jobs, Thanatos reads your profile data from `data/profile_dir/` (which can hold LaTeX `.tex`, `.md`, or `.txt` resumes).
- It extracts your GitHub, LinkedIn, portfolio links, and skills.
- It autonomously designs and compiles:
  1. **A polished, tailored Resume PDF** (`<company>_resume.pdf`)
  2. **A personalized Cover Letter PDF** (`<company>_cover_letter.pdf`)
- Both PDF documents are automatically attached to your outreach email.

---

## 4. Vector Database & Automatic Enterprise Scaling

Thanatos is pre-configured with zero-configuration local vector databases:
- **Milvus Lite** & **ChromaDB**: Store your indexed memories, resumes, and embeddings locally without any setup.
- **Scale Detection**: When your indexed knowledge base exceeds 1,000 documents or high concurrency, Thanatos prompts you and offers automated Docker scaling:
  ```bash
  docker compose -f docker-compose.scaling.yml up -d
  ```
  This brings up **Milvus Standalone** (with GPU acceleration) and **PostgreSQL 16**.

---

## 5. Multi-Device Mesh: Auto-Discovery & Wi-Fi Compute Clustering

Thanatos lets you pool the computational power of other laptops and Android devices on the same Wi-Fi.

### Step 1: Start a Worker on Your Other Device
On your secondary laptop or Android phone (via Termux):
```bash
python -m services.mesh.worker --port 8002 --role worker
```

### Step 2: Auto-Discovery & Remote Control from Primary Machine
You don't even need to type IP addresses manually! From your main Thanatos terminal:
```text
thanatos> /nodes scan
[✓] Discovery scan complete. Discovered LAN mesh nodes automatically!

thanatos> /nodes
• Distributed LAN Mesh Nodes (1 Registered):
  • LAPTOP-WORKER (http://192.168.1.15:8002): ONLINE Role: worker
```

### Step 3: Controlling Secondary Nodes from Primary Terminal
You can manage models and run commands on the secondary device directly:
```text
# Instruct secondary node to pull an SLM model (e.g. Qwen, Phi-3, LLaMA)
thanatos> /nodes pull LAPTOP-WORKER qwen2.5:3b

# Run remote shell commands on the secondary node
thanatos> /nodes exec LAPTOP-WORKER "ollama list"

# Sync resumes, profile documents, and settings to all connected nodes
thanatos> /nodes sync
```

---

## 6. Job Applications, Authentic LaTeX Resumes & Draft Previews

When running autonomous job applications:
1. Thanatos searches positions matching your preferences and **strictly filters out** any openings without direct email addresses.
2. It ingests your authentic LaTeX resumes (`AI_Engineer.tex` / `AI_Developer.tex` from `data/profile_dir/` or any custom folder) and generates comprehensive, tailored applications preserving your real career achievements (C-DAC, Maritime Knowledge Cluster, PySpark, Airflow, MLflow).
3. **Interactive Draft Review Gate**:
   Thanatos provides an interactive draft review stage where you can view or open drafts in WPS / Microsoft Word / PDF reader before sending:
   ```text
   Proceed with dispatch? [Y/o/s]:
   - Enter (Y) = Approve and dispatch
   - 'o' = Open PDF in WPS / Word / default viewer for quick review
   - 's' = Skip this opportunity
   ```
4. **Auto-Pilot Mode**:
   Once you trust the system completely, toggle off the manual review gate:
   ```text
   thanatos> /preview off
   [✓] Draft preview gate disabled (Autonomous Auto-Pilot mode active).
   ```

---

## 6. Exporting Thanatos to Another Device

Want to move your entire configured Thanatos assistant to another PC or phone?
Run the built-in bundler:
```bash
python tools/pack_bundle.py
```
This produces `thanatos_portable.zip` containing all code, skills, and configurations (cleanly excluding virtual environments and cache files) ready to unpack anywhere.
