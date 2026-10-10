# 🚗 CarScan — AI Car Damage Detection

Detect car damages from a single image using **YOLOv8** + **FastAPI**.

**Detects 6 damage types:** scratch · dent · glass shatter · broken lamp · crack · flat tire.

---

## ✨ Features

- 🎯 YOLOv8 model trained on 6 damage classes (**91% accuracy**)
- 🖼️ Three input methods: **upload**, **drag & drop**, **camera**
- 📦 Results saved to **Supabase** (Storage + Postgres)
- 📊 History and statistics pages
- ⚡ FastAPI backend + vanilla JS frontend (no framework needed)

---

## 🛠 Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11 · FastAPI · Pydantic |
| Model | YOLOv8 (ultralytics) |
| Database | Supabase (Storage + Postgres) |
| Image | OpenCV |
| Frontend | HTML · CSS · Vanilla JS |


## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- A **Supabase** account (free tier is enough)
- ~2 GB free disk space (for PyTorch)

### 1. Clone the repository

```bash
git clone https://github.com/karimabdelmonem/carvision-ai-with-yolov8n.git
cd carvision-ai-with-yolov8n
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> First install may take **3–5 minutes** (PyTorch download).

### 4. Setup Supabase

Create a **public** bucket called `car-images`, then run this SQL in the Supabase SQL editor:

```sql
create table scans (
  id uuid primary key default gen_random_uuid(),
  image_path text not null,
  image_url text not null,
  detections jsonb not null default '[]',
  damage_count int not null default 0,
  summary jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index scans_created_at_idx on scans (created_at desc);
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and fill in your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=car-images
```

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/app/** in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scan` | Upload an image → returns detections |
| `GET` | `/scans` | List all scans (paginated) |
| `GET` | `/scans/stats` | Aggregate statistics |
| `GET` | `/scans/{id}` | Get a single scan |
| `DELETE` | `/scans/{id}` | Delete a scan + its image |
| `GET` | `/health` | Health check |

**Interactive docs:** http://127.0.0.1:8000/docs

---

## 🧠 Model

| Property | Value |
|---|---|
| Architecture | YOLOv8 |
| Classes | `crack`, `dent`, `glass shatter`, `lamp broken`, `scratch`, `tire flat` |
| Confidence threshold | 0.25 |
| IOU threshold | 0.45 |
| Accuracy | 91% on 22 test images |
| Weights | `models/best.pt` (6.25 MB) |

