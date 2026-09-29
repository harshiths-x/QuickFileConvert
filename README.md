# QuickFileConvert

**Convert files quickly. No account required.**

QuickFileConvert is a small, privacy-focused file conversion website. It accepts one file per operation, processes it on a FastAPI backend, and lets the user download the result from a temporary result card.

## Features and limits

| Category | Tools |
| --- | --- |
| Documents | PDF to Word, Word to PDF, PDF to TXT, TXT to PDF, DOCX to TXT |
| PDF tools | Split a page range, rotate pages, extract selected pages, reorder all pages |
| Images | JPG/JPEG to PNG, PNG to JPG, image to PDF |
| Spreadsheets | CSV to Excel, Excel to CSV |

- **One upload at a time**, maximum **50 MB**, checked by the browser and server.
- Files are temporarily processed and automatically deleted within **5 minutes**. Failed jobs and intermediate uploads are removed promptly. The janitor also removes expired files after abandoned sessions and on server startup.
- A successful result waits for the user to press **Download file**. The random download ID expires with the file.
- PDF page numbers in the UI start at 1. Split accepts one continuous range; extract accepts lists and ranges; reorder requires each page exactly once. Rotation accepts 90°, 180°, or 270° on all or selected pages.
- Excel to CSV uses the first sheet unless an exact worksheet name is entered. CSV is read as UTF-8 (with or without BOM); CSV output uses UTF-8 with BOM for Excel compatibility. Formulas are exported as cached values where available.
- PDF to TXT extracts embedded text only; OCR is not included. PDF to Word quality depends on the PDF layout.

## Stack and architecture

- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS, Lucide icons. Deployable to Vercel.
- **Backend:** FastAPI, Python, Uvicorn, pypdf, pdf2docx, Pillow, python-docx, openpyxl, ReportLab, and LibreOffice. Packaged in Docker.
- **Storage:** Per-conversion temporary directories on the backend filesystem. No database, accounts, history, or permanent file storage.

The browser sends one multipart upload to the backend. The backend validates and processes it, then returns a random download ID and file metadata. The browser shows the result card. A separate download endpoint serves the output until its 5-minute expiry. The frontend and backend must share an HTTPS deployment configuration in production.

## Local development

Requirements: Node.js 20 or later, Python 3.12, and LibreOffice for Word to PDF. On Windows, install LibreOffice and add its `program` directory to PATH. From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Visit `http://localhost:3000`; the API health check is `http://localhost:8000/health`. On macOS/Linux, activate the Python environment with `source .venv/bin/activate` and copy the env example with `cp`.

## Docker backend

Docker includes LibreOffice. The frontend is **not** Dockerized.

```sh
docker compose up --build
```

Or build and run only the backend:

```sh
docker build -t quickfileconvert-backend ./backend
docker run --rm -p 8000:8000 -e ALLOWED_ORIGINS=http://localhost:3000 --tmpfs /srv/app/temp:size=512m quickfileconvert-backend
```

The container listens on port 8000 at `0.0.0.0`. Mount a writable ephemeral volume at `/srv/app/temp` if the host does not support tmpfs. Allow enough space for uploaded and generated files. Do not put this directory on permanent shared storage.

## Configuration

Copy the `.env.example` files as a starting point. Do not commit real `.env` files.

| Variable | Where | Default / purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://localhost:8000`; public backend base URL |
| `ALLOWED_ORIGINS` | Backend | `http://localhost:3000`; comma-separated exact frontend origins |
| `ENVIRONMENT` | Backend | `development` |
| `MAX_UPLOAD_SIZE` | Backend | `52428800` bytes (50 MB); may be lowered, never raised beyond 50 MB |
| `TEMP_FILE_TTL` | Backend | `300` seconds |
| `RATE_LIMIT_REQUESTS` | Backend | `60` upload requests per IP per window |
| `RATE_LIMIT_WINDOW` | Backend | `3600` seconds |
| `CONVERSION_TIMEOUT` | Backend | `120` seconds |
| `TEMP_ROOT` | Backend | `backend/app/temp`; optional controlled temp root |
| `LIBREOFFICE_PATH` | Backend | Optional explicit path to `soffice.exe` or `libreoffice`; standard installs are detected automatically |

Keep the 50 MB and 5-minute values aligned with the frontend text. For a public deployment, set `ALLOWED_ORIGINS` to the exact Vercel origin, never `*`. The rate limiter uses the direct connection IP and a single process in-memory store. Hosts behind a proxy should apply their own trusted edge rate limit; multiple backend replicas do not share these limits or temporary files. Route a download to the same replica that processed it, or deploy a single replica for this version.

## Deployment

1. Deploy `frontend/` to Vercel as a Next.js project. Set `NEXT_PUBLIC_API_URL` to the public **HTTPS** backend origin and redeploy after changing it.
2. Build `backend/Dockerfile` on a Docker-compatible host. Expose port 8000 over HTTPS using the host's ingress or reverse proxy. Set `ALLOWED_ORIGINS` to the exact Vercel origin and provide writable ephemeral temp storage.
3. Check `GET /health`, then run a conversion from the deployed frontend. Keep a single backend replica unless temporary result storage and rate limiting are redesigned for multiple replicas.

No deployment or Git operation is performed by this project.

## API

- `GET /health`
- `POST /api/convert/{tool}` for the ten document, image, and spreadsheet conversions
- `POST /api/pdf/{split|rotate|extract|reorder}` for PDF operations
- `POST /api/pdf/inspect` for page count (the inspection upload is deleted immediately)
- `GET /api/download/{download_id}` for an unexpired result

POST requests use multipart form fields `file` and `options` (a JSON object string). PDF operations use `pages` and, for rotation, `rotation`; Excel to CSV may use `sheet`. A successful conversion returns `download_id`, `filename`, `mime_type`, and `size`. Errors use FastAPI's `detail` field. The download ID is a random UUID and never contains a server path.

## Security and privacy

The backend checks size, extension, and file signatures or structures; rejects executables and unrelated files; bounds expanded Office ZIP content; and never uses a user-supplied filename as a filesystem path. Outputs are named safely for download. Conversion workers have a timeout, LibreOffice uses a temporary profile and an argument array, and CORS accepts only configured origins. The server does not return stack traces in API responses. Logs may include technical errors but not file contents. Uploaded files may still contain sensitive information, so deploy the API over HTTPS and use an appropriate trusted host.

The 5-minute cleanup policy is approximate: a background janitor checks every 5 seconds and also runs at startup. A requested download can be served until expiry; intermediate uploads are removed as soon as processing finishes. On a hard process or host failure, the ephemeral storage's lifecycle provides the final cleanup boundary.

## Tests

```sh
cd backend
python -m pytest
cd ../frontend
npm run build
```

Backend tests cover health, valid conversion and download, format and size rejection, PDF page behavior, image transparency, expiry, and safe names.

## Project layout

```text
frontend/         Next.js pages, components, styles, and tool definitions
backend/app/      FastAPI API, processing services, validation, cleanup
backend/tests/    Backend tests
backend/Dockerfile
docker-compose.yml
```

## Known limitations

- No OCR, password-protected PDFs, legacy `.doc`/`.xls`, or PDF merge.
- Complex PDF to Word layouts may not reproduce perfectly.
- The backend uses one process and local ephemeral result storage. Horizontal scaling requires shared short-lived storage and coordinated rate limits.
- Word to PDF requires LibreOffice outside Docker too.
- The in-memory rate limiter resets when the backend restarts.

This is an open-source-style utility project. Add a license of your choice before publishing it as an open-source repository.
