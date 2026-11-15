# Parametric STEP AP242 CAD Generator

A high-performance, lightweight web application and parametric engine for generating native ISO 10303-21 (STEP AP242) modular CAD assemblies for arbitrary grid dimensions $M \times N$.

Compatible with **SolidWorks**, **AutoCAD**, **CATIA**, **Siemens NX**, **FreeCAD**, and **OpenCascade**.

---

## Features

- **Arbitrary $M \times N$ Generation**: Dynamically scale both rows ($M$) and columns ($N$) with exact physical contact ($0.0000\text{ mm}$ gap).
- **Parametric B-Rep Beam Extrusion & Hole Patterns**:
  - Longitudinal beams (`ToDn`) with equal-interval mounting holes.
  - Transverse beams (`LeRa`) with replicated column holes.
  - Internal column support pillars (`#Soton`) scaled to match frame height.
  - Row endplate caps (`MUDS Geometry`) scaled to fit column width.
- **Mark-and-Sweep Assembly Cleaner**:
  - Automatically sweeps assembly references and purges orphaned definitions.
  - Guarantees **strictly 1 root Free Shape** (zero floating or rotated parts at origin).
  - Guarantees **0 unresolved entity references**.
- **Zero External Dependencies**:
  - Pure Python standard library (`http.server`, `re`, `collections`, `urllib`).
  - No C++ CAD bindings, no OpenCascade binaries, and no heavy pip packages required at runtime.
  - Lightweight output (~5–7 MB per generated STEP file).

---

## Repository Structure

```text
.
├── app.py                  # Web server & interactive browser UI
├── parametric_generator.py # Parametric math engine & mark-and-sweep tree cleaner
├── step_parser.py          # Fast ISO 10303-21 entity parser
├── requirements.txt        # Python dependency manifest (standard library)
├── 3X4_01.stp              # Base CAD template (3x4)
├── 4X7_01.stp              # Base CAD template (4x7)
├── 4X8_02.stp              # Base CAD template (4x8)
├── 5X9_06.stp              # Master base CAD template (5x9)
└── README.md               # Project documentation
```

---

## Local Quick Start

### 1. Requirements
- Python 3.8 or higher. No external pip packages needed.

### 2. Run the Web Interface
```bash
python app.py
```
Open [http://localhost:8080](http://localhost:8080) in your web browser.

### 3. Command Line Generation (CLI)
You can also generate STEP files directly from the command line:
```bash
# Syntax: python parametric_generator.py <Rows_M> <Cols_N> <Output_File>
python parametric_generator.py 8 16 output/8X16_01.stp
python parametric_generator.py 5 3  output/5X3_01.stp
```

---

## Deployment to Render.com

1. Create a new repository on [GitHub](https://github.com) and upload the repository files.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** $\rightarrow$ **Web Service**, and select your GitHub repository.
4. Configure the service:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Instance Type:** `Free`
5. Click **Deploy Web Service**.
Render will provision the service and provide a public URL (e.g. `https://your-service.onrender.com`).

---

## REST API Endpoint

You can generate and download assemblies programmatically via HTTP GET:

### `GET /api/generate`
**Query Parameters:**
- `m` *(integer, required)*: Number of rows ($M \ge 1$)
- `n` *(integer, required)*: Number of columns ($N \ge 1$)

**Example Request:**
```bash
curl -O -J "https://your-service.onrender.com/api/generate?m=8&n=16"
```
**Response:**
- Content-Type: `application/step`
- Content-Disposition: `attachment; filename="8X16_01.stp"`
- HTTP Body: Binary STEP AP242 CAD file data.
