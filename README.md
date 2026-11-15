# Parametric STEP AP242 CAD Generator

A lightweight, high-performance web service that dynamically generates native ISO 10303-21 STEP AP242 CAD assemblies for arbitrary grid dimensions $M \times N$.

## Features
- Dynamic beam extrusion math and hole distribution (ToDn, LeRa, Soton)
- Native SolidWorks-compatible assembly hierarchy
- Automated mark-and-sweep tree garbage collector (0 orphaned shapes, 0 dangling references)
- Zero external pip or C++ dependencies — runs on standard Python 3.8+!

## Running Locally
```bash
python app.py
```
Open `http://localhost:8080` in your browser.

## Deploying to Render.com
1. Create a new Web Service on Render connected to this repository.
2. Settings:
   - **Runtime:** Python 3
   - **Build Command:** *(leave empty)*
   - **Start Command:** `python app.py`
3. Click **Deploy**.
