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

## 5. Multi-Device Mesh: Linking Secondary Laptops & Android (Termux)

You can turn secondary computers or Android phones on the same Wi-Fi into worker nodes:

### On the Secondary Device (Laptop or Termux):
1. Copy Thanatos or unbundle the portable archive (`python tools/pack_bundle.py`).
2. Run:
   ```bash
   python -m services.mesh.worker --port 8002
   ```

### On the Primary Thanatos Machine:
In the Thanatos CLI, link the node by IP address:
```text
thanatos> /nodes add 192.168.1.50:8002 PhoneWorker
[✓] Registered node PhoneWorker (http://192.168.1.50:8002)
  Status: ONLINE
```
Now Thanatos can offload sub-agent tasks and background compute across your local network.

---

## 6. Exporting Thanatos to Another Device

Want to move your entire configured Thanatos assistant to another PC or phone?
Run the built-in bundler:
```bash
python tools/pack_bundle.py
```
This produces `thanatos_portable.zip` containing all code, skills, and configurations (cleanly excluding virtual environments and cache files) ready to unpack anywhere.
