# BestCV: ATS Resume Scorer

BestCV analyzes a PDF or DOCX resume, optionally compares it with a job description, and provides an ATS score and feedback. It uses a FastAPI backend, Streamlit frontend, spaCy, Sentence Transformers, Groq, and Supabase for accounts and saved analyses. Legacy `.doc` files must be converted to PDF or DOCX.

## Windows setup

Install **64-bit Python 3.11** and open PowerShell in the project folder. Run:

```powershell
.\scripts\setup.ps1
```

The setup script prepares the local Python environment using `requirements.windows.txt` and the tested versions in `requirements.windows.lock.txt`, downloads the NLP models, and prepares portable PDF libraries. Initial setup needs an internet connection. Run setup again to resume an interrupted download.

For PDF export, `scripts/setup-pdf-runtime.ps1` downloads the [official WeasyPrint 70.0 portable archive](https://github.com/Kozea/WeasyPrint/releases/tag/v70.0), verifies its pinned SHA256 checksum, and extracts its native libraries into `.runtime/weasyprint`. It does not require an administrator or a system GTK installation. The app discovers these libraries automatically.

## Configure services

Use the root **`.env`** as the single source of local credentials. If it does not exist, copy `.env.example` to `.env`; preserve an existing file. Both applications load this file automatically, so a separate Streamlit secrets file is unnecessary.

Fill in:

- `SUPABASE_URL`: your Supabase project URL.
- `SUPABASE_KEY`: the backend's service-role key for saving and loading history. Keep this secret.
- `SUPABASE_ANON_KEY`: the public anon key used for account sign-in.
- `SUPABASE_JWT_SECRET`: needed only for Supabase projects that still sign access tokens with HS256. Projects using asymmetric signing keys are verified through the project's public signing keys.
- `GROQ_API_KEY`: **required for resume analysis**, including analysis without a job description.
- `AUTH_REDIRECT_URL`: keep `http://localhost:8501` for the default local frontend.
- `SENTENCE_TRANSFORMER_MODEL`: keep `all-MiniLM-L6-v2` unless you intentionally use another model.

In the Supabase dashboard:

1. Open the SQL Editor and run the contents of [`supabase/schema.sql`](supabase/schema.sql). It creates the `analyses` table, history index, and policies restricting authenticated users to their own rows.
2. In Authentication, enable email/password sign-in. If email confirmation is enabled, confirm your email before signing in.
3. In Authentication's URL Configuration, add `http://localhost:8501` as an allowed redirect URL. For a project dedicated to local development, use it as the Site URL too.
4. Optionally enable the Google authentication provider and configure its client credentials and the callback URL shown by Supabase. Keep `AUTH_REDIRECT_URL` consistent with the allowed frontend redirect URL.

Never commit `.env`, Streamlit secrets, or service-role credentials.

## Start the app

From the project folder:

```powershell
.\scripts\start.ps1
```

Open the frontend at [http://localhost:8501](http://localhost:8501). The backend API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs), and its model readiness check is at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

Stop both services with `.\scripts\stop.ps1`. Logs are saved in `.local/`. After changing `.env`, stop and start the app again.

If PowerShell blocks a script because of its execution policy, run it with a process-only override:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

To start the services manually, run each command in a separate terminal from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

## Verify your setup

Check that the frontend loads and the backend health endpoint reports both NLP models loaded. Then sign in, upload a small PDF or DOCX resume, run an analysis, and check History. A job description can be pasted or uploaded as a `.txt` file.

Local startup and health checks do not confirm a complete account-to-analysis workflow. That requires valid Supabase and Groq credentials, the database schema above, and a signed-in account. If PDF export reports missing native libraries, rerun `scripts/setup-pdf-runtime.ps1` and restart the backend.

The notebooks are research material and are not required to run the app.
