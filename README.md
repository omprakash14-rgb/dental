# DentalAI – AI-Powered Dental Disease Detection Platform

DentalAI is an enterprise-grade medical computer vision platform that analyzes multi-angle intraoral dental photographs (**Front**, **Left Side**, and **Right Side** views) to identify possible dental conditions and assist dental professionals in clinical pre-screening.

Powered by a pretrained **ResNet-50** deep convolutional neural network fine-tuned on clinical oral photography, DentalAI incorporates **Grad-CAM (Gradient-weighted Class Activation Mapping)** to generate visual feature salience heatmaps and bounding boxes around detected oral pathologies.

---

## 1. AI Model Research & Verification Summary

During Phase 1 of this project, an exhaustive investigation was conducted into the pretrained model candidates:

### 1.1 Investigation of BinaModel YOLO26s Dental Detection
- **Repository:** `sina-04/dental-yolo26-detection` (often transliterated as BinaModel YOLO26s).
- **Pretrained Weights:** **Unavailable**. Inspection of repository releases (`curl -s https://api.github.com/repos/sina-04/dental-yolo26-detection/releases`) returns `[]` (empty). No model checkpoint (`.pt`, `.onnx`, or `.pth`) is hosted in the git tree.
- **Dataset & Modality:** Trained exclusively on **panoramic dental radiographs (orthopantomograms / OPGs)** from the Kaggle Dental Disease Panoramic Detection Dataset v6.
- **Intraoral Compatibility:** **Incompatible**. The model architecture was designed for panoramic full-arch radiographic geometry and cannot process ordinary intraoral RGB camera photographs.
- **Repository Evaluation:** The author explicitly notes that the dataset fails independent patient support gates, has high class imbalance, and remains exploratory and non-diagnostic.

### 1.2 Evaluation & Selection of ResNet-50 Oral Disease Model
As stipulated by the project instructions: *"If BinaModel is unavailable or incompatible, evaluate ResNet50 oral disease classification as an alternative."*
- **Architecture:** ResNet-50 deep CNN with Global Average Pooling, dense projection, and 6-class softmax output.
- **Pretrained Weights:** Verified and downloaded from Hugging Face (`best_model_resnet50.keras`, 98.2 MB).
- **Modality:** Specifically trained on **ordinary intraoral clinical photographs** (including frontal and lateral arch photography).
- **Supported Disease Categories:** Exactly 6 validated oral conditions:
  1. `Calculus` (Dental tartar / calcified plaque along gingival margins)
  2. `Caries` (Tooth decay, demineralization, and cavitation)
  3. `Gingivitis` (Marginal gingival inflammation, edema, and erythema)
  4. `Hypodontia` (Congenitally missing teeth / arch diastema)
  5. `Mouth_Ulcer` (Aphthous ulcers and oral mucosal lesions)
  6. `Tooth_Discoloration` (Extrinsic or intrinsic enamel staining)
- **Visual Localization:** ResNet-50 final convolutional layer (`conv5_block3_out`) is probed with **Grad-CAM** to produce activation heatmaps and compute bounding boxes `[ymin, xmin, ymax, xmax]`.

---

## 2. Technology Stack

### Frontend:
- **Framework:** React 19 with Vite & TypeScript
- **Styling:** Tailwind CSS (Custom medical soft-blue theme, responsive cards, glassmorphism)
- **Icons:** Lucide React icons
- **Data Visualization:** Recharts (Frequency bar charts & triage urgency distribution)
- **Components:** Interactive Bounding Box / Heatmap image switcher, drag-and-drop 3-view upload zones, clinical disclaimer modal.

### Backend:
- **Framework:** FastAPI with Python 3.14 / Uvicorn ASGI server
- **Validation:** Pydantic v2
- **Computer Vision & ML:** Keras 3 / TensorFlow, OpenCV, Pillow, NumPy
- **Image Preprocessing:** Caffe-style mean subtraction `[103.939, 116.779, 123.68]`, RGB-to-BGR conversion, blur detection (Laplacian variance), dimension checks.

### Database:
- **Primary Engine:** PostgreSQL 16 (via Docker / `psycopg2-binary`)
- **ORM:** SQLAlchemy 2.0 with auto-migrated relational schema
- **Fallback:** Automatic seamless fallback to SQLite (`sqlite:///./dentalai.db`) if PostgreSQL is unavailable.

---

## 3. Project Directory Structure

```text
dental/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── model_loader.py          # Singleton loader for ResNet-50 & class metadata
│   │   │   ├── image_preprocessing.py   # Format checks, dimension validation, Caffe normalizer
│   │   │   ├── inference.py             # Forward pass & Grad-CAM bounding box extraction
│   │   │   ├── prediction_processor.py  # Multi-angle consensus without naive score summation
│   │   │   └── report_generator.py      # Structured clinical screening report builder
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py             # FastAPI routes (/analyze, /patients, /reports, /stats)
│   │   │   └── schemas.py               # Pydantic request and response models
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py              # Engine setup with PostgreSQL + SQLite fallback
│   │   │   └── models.py                # Patient, DentalAnalysis, UploadedImage, GeneratedReport
│   │   ├── core/
│   │   │   └── security.py
│   │   └── main.py                      # FastAPI app entrypoint with static SPA & uploads mount
│   ├── models/
│   │   ├── best_model_resnet50.keras    # Pretrained model weights (98.2 MB)
│   │   └── class_indices.json           # 6 oral disease class indices
│   ├── samples/                         # Intraoral test images for immediate evaluation
│   ├── uploads/                         # Secure storage for images, heatmaps, and bounding boxes
│   ├── tests/
│   │   ├── test_inference.py            # Phase 3 standalone AI pipeline test
│   │   └── test_api.py                  # Phase 4 end-to-end API test suite
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx               # Top medical branding & live AI status pill
│   │   │   ├── Sidebar.tsx              # Clean clinical navigation bar
│   │   │   ├── ImageUploadZone.tsx      # 3 separate drag-and-drop cards with live previews
│   │   │   ├── BoundingBoxOverlay.tsx   # Interactive viewer (Boxes, Heatmap, Raw)
│   │   │   └── DisclaimerModal.tsx      # Clinical regulatory & dentist review modal
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx            # KPI metrics, Recharts charts, recent scans table
│   │   │   ├── NewAnalysis.tsx          # Patient form + 3-view uploads + 1-click sample loader
│   │   │   ├── AnalysisResult.tsx       # Multi-angle findings, bounding boxes, recommendations
│   │   │   └── PatientHistory.tsx       # Searchable patient directory & chronological timeline
│   │   ├── services/
│   │   │   └── api.ts                   # Typed API service with upload progress monitoring
│   │   ├── types/
│   │   │   └── index.ts                 # Complete TypeScript definitions
│   │   ├── App.tsx                      # Layout coordinator & routing
│   │   ├── main.tsx
│   │   └── index.css                    # Tailwind CSS + print styling
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docker-compose.yml                   # PostgreSQL container orchestration
├── README.md
└── .env.example
```

---

## 4. Multi-Angle Photographic Aggregation Logic

The AI pipeline adheres strictly to clinical aggregation rules:
1. **No Naive Summation:** Confidences across views are not blindly added (which would violate probability axioms). Instead, the model extracts the calibrated peak confidence and applies a conservative multi-view consensus reinforcement factor (maximum +6%).
2. **De-duplication:** Detections of the same condition occurring on both Front and Lateral views (e.g. Gingivitis spanning anterior and premolar regions) are unified into a single clinical disease finding with `affected_views: ["front", "left"]`.
3. **Inconclusive Handling:** If photographic contrast or orientation prevents confident attribution (confidence < 35%), the system flags the view as **Inconclusive** rather than declaring false negatives.

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.14 on macOS)
- Node.js 18+ and npm
- Docker (optional, for PostgreSQL container)

### Step 1: Start PostgreSQL (Optional but Recommended)
```bash
docker run -d --name dentalai-postgres \
  -e POSTGRES_DB=dentalai \
  -e POSTGRES_USER=dentalai \
  -e POSTGRES_PASSWORD=dentalai_password \
  -p 5432:5432 postgres:16-alpine
```
*(Note: If Docker is omitted, the backend will automatically initialize a local SQLite database `dentalai.db`.)*

### Step 2: Set Up & Run the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the test suite to verify model inference & API endpoints
PYTHONPATH=. python3 tests/test_inference.py
PYTHONPATH=. python3 tests/test_api.py

# Launch the FastAPI application
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend API will be live at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.

### Step 3: Set Up & Run the Frontend
```bash
cd frontend
npm install
npm run build   # Builds production assets into frontend/dist
npm run dev     # Starts Vite development server with proxy to backend
```
Open `http://localhost:5173` in your browser.

---

## 6. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health, model residency check, DB status, supported classes. |
| `POST` | `/api/analyze` | Accepts patient info + 3 images (front, left, right), runs inference, returns report. |
| `GET` | `/api/stats` | Aggregated dashboard metrics (patients count, scans count, disease distribution). |
| `GET` | `/api/patients` | Lists registered patients with completed scan counts. |
| `GET` | `/api/patients/{id}` | Returns patient profile and chronological scan timeline. |
| `GET` | `/api/reports/{id}` | Fetches stored clinical screening report JSON. |

---

## 7. Clinical Disclaimer & Ethics Notice

> **IMPORTANT NOTICE:** DentalAI is an assistive artificial intelligence screening tool designed to aid registered dental practitioners in preliminary photographic review. This system **DOES NOT** formulate a definitive diagnosis, surgical plan, or pharmaceutical prescription. All findings, classifications, and localized bounding regions must be confirmed by a qualified dentist through comprehensive chairside examination, tactile periodontal probing, and diagnostic radiographic imaging (such as bitewing or periapical X-rays) when clinically indicated.

