
import pandas as pd
import numpy as np


# 1. Membersihkan data mentah
def bersihkan_data(data):
    data = data.copy()

    # Mengubah kolom waktu menjadi datetime
    teks = data["waktu"].astype(str)
    waktu = pd.to_datetime(teks, format="%Y-%m-%d %H:%M",
                           errors="coerce")

    for fmt in ["%d/%m/%Y %H.%M", "%Y-%m-%d %H:%M:%S"]:
        waktu = waktu.fillna(
            pd.to_datetime(teks, format=fmt, errors="coerce")
        )

    data["waktu"] = waktu
    data = data.dropna(subset=["waktu"])
    data = data.drop_duplicates().sort_values("waktu")
    data = data.drop_duplicates("waktu").set_index("waktu")
    data = data.apply(pd.to_numeric, errors="coerce")

    # Memeriksa nilai yang tidak masuk akal
    salah = (data["konsumsi_kWh"] < 0) | (
        data["konsumsi_kWh"] == 99999
    )
    data.loc[salah, "konsumsi_kWh"] = np.nan

    data.loc[
        ~data["suhu_luar_C"].between(-10, 50),
        "suhu_luar_C"
    ] = np.nan

    data.loc[
        ~data["kelembaban_luar_pct"].between(0, 100),
        "kelembaban_luar_pct"
    ] = np.nan

    data.loc[data["okupansi_orang"] < 0, "okupansi_orang"] = np.nan

    # Memastikan urutan waktunya lengkap per jam
    jam = pd.date_range(
        data.index.min(), data.index.max(),
        freq="h", name="waktu"
    )

    return data.reindex(jam)


# 2. Membuat fitur seperti pada Google Colab
def buat_fitur(data):
    fitur = pd.DataFrame(index=data.index)

    fitur["jam"] = data.index.hour
    fitur["hari"] = data.index.dayofweek
    fitur["bulan"] = data.index.month
    fitur["hari_libur"] = data["hari_libur"]

    fitur["suhu_prakiraan"] = data["suhu_luar_C"].shift(168)
    fitur["okupansi_jadwal"] = data["okupansi_orang"].shift(168)

    for lag in [24, 48, 168]:
        fitur[f"lag{lag}"] = data["konsumsi_kWh"].shift(lag)

    fitur["rerata24"] = (
        data["konsumsi_kWh"]
        .shift(24)
        .rolling(24, min_periods=12)
        .mean()
    )

    return fitur


# 3. Menyiapkan data prediksi 24 jam
def fitur_prediksi(data, tanggal, suhu, okupansi, hari_libur=0):
    tanggal = pd.Timestamp(tanggal).normalize()

    # Riwayat wajib berakhir pada pukul 23.00 kemarin
    waktu_terakhir = tanggal - pd.Timedelta(hours=1)

    if data.index.max() != waktu_terakhir:
        raise ValueError(
            "Riwayat harus berakhir pada pukul 23.00 "
            "sehari sebelum tanggal prediksi."
        )

    if not -10 <= suhu <= 50:
        raise ValueError("Suhu harus antara -10 dan 50 C.")

    if okupansi < 0:
        raise ValueError("Jumlah orang tidak boleh negatif.")

    if hari_libur not in [0, 1]:
        raise ValueError("Hari libur hanya boleh 0 atau 1.")

    # Membuat waktu prediksi selama 24 jam
    jam_besok = pd.date_range(
        tanggal, periods=24, freq="h"
    )

    # Gabungkan riwayat dan jam prediksi
    rentang = pd.date_range(
        data.index.min(), jam_besok[-1], freq="h"
    )
    gabungan = data.reindex(rentang).copy()
    gabungan.loc[jam_besok, "hari_libur"] = hari_libur

    # Membuat fitur berdasarkan riwayat
    fitur = buat_fitur(gabungan).loc[jam_besok].copy()

    # Gunakan prakiraan dan jadwal dari pengguna
    fitur["suhu_prakiraan"] = suhu
    fitur["okupansi_jadwal"] = okupansi

    kolom_lag = ["lag24", "lag48", "lag168"]

    # Memastikan data historis cukup untuk prediksi
    if fitur[kolom_lag].notna().sum().sum() < 36:
        raise ValueError("Data riwayat konsumsi terlalu banyak kosong.")

    return fitur
