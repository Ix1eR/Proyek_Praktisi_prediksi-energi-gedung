from pathlib import Path
from datetime import date

import json
import joblib
import pandas as pd
import numpy as np

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.features import bersihkan_data, fitur_prediksi

# Membuat aplikasi FastAPI
app = FastAPI(
    title="API Prediksi Energi Gedung",
    description="Prediksi konsumsi listrik gedung selama 24 jam",
    version="1.0"
)

# Menentukan lokasi folder utama proyek
ROOT = Path(__file__).resolve().parents[2]

# Lokasi file
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "metadata.json"
DATA_PATH = ROOT / "data" / "raw.csv"

# Membaca model dan metadata
model = joblib.load(MODEL_PATH)

with open(METADATA_PATH, "r", encoding="utf-8") as file:
    metadata = json.load(file)

kolom_fitur = metadata["features"]

class InputPrediksi(BaseModel):
    tanggal: date
    suhu: float = Field(ge=-10, le=50)
    okupansi: int = Field(ge=0, le=10000)
    hari_libur: int = Field(default=0, ge=0, le=1)

@app.get("/")
def halaman_utama():
    return {
        "pesan": "API Prediksi Energi Gedung berjalan",
        "dokumentasi": "/docs"
    }

@app.get("/health")
def cek_kesehatan():
    return {
        "status": "ready",
        "model": metadata["model"],
        "jumlah_fitur": len(kolom_fitur),
        "dataset_tersedia": DATA_PATH.exists()
    }

@app.post("/predict")
def prediksi(data_input: InputPrediksi):

    # 1. Memastikan dataset tersedia
    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="File data/raw.csv tidak ditemukan"
        )

    try:
        # 2. Membaca dan membersihkan dataset
        data = pd.read_csv(DATA_PATH)
        data_bersih = bersihkan_data(data)

        # 3. Menyiapkan 24 baris fitur
        X_besok = fitur_prediksi(
            data=data_bersih,
            tanggal=data_input.tanggal,
            suhu=data_input.suhu,
            okupansi=data_input.okupansi,
            hari_libur=data_input.hari_libur
        )

        # 4. Menyesuaikan urutan fitur
        X_besok = X_besok[kolom_fitur]

        # 5. Melakukan prediksi dengan model
        hasil = model.predict(X_besok)

        # 6. Memastikan konsumsi tidak negatif
        hasil = np.clip(hasil, 0, None)

        # 7. Membuat tabel hasil prediksi
        tabel = pd.DataFrame({
            "waktu": X_besok.index.strftime("%Y-%m-%d %H:%M"),
            "prediksi_kWh": np.round(hasil, 2)
        })

        # 8. Menghitung total konsumsi
        total = float(np.sum(hasil))

        # 9. Mengirim hasil ke pengguna
        return {
            "tanggal": str(data_input.tanggal),
            "total_kWh": round(total, 2),
            "jumlah_jam": len(tabel),
            "prediksi": tabel.to_dict(orient="records")
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediksi gagal: {error}"
        )
