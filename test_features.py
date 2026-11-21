import pandas as pd

from src.features import bersihkan_data, buat_fitur, fitur_prediksi

# 1. Membaca dataset
data = pd.read_csv("data/raw.csv")
print("Jumlah data mentah:", len(data))

# 2. Membersihkan dataset
data_bersih = bersihkan_data(data)
print("Jumlah data setelah pembersihan:", len(data_bersih))

# 3. Membuat fitur
fitur = buat_fitur(data_bersih)
print("\nDaftar fitur:")
print(fitur.columns.tolist())

# 4. Membuat contoh prediksi 1 Juli 2026
riwayat = data_bersih.loc[:"2026-06-30 23:00"]

X_besok = fitur_prediksi(
    data=riwayat,
    tanggal="2026-07-01",
    suhu=25,
    okupansi=100,
    hari_libur=0
)

print("\nFitur untuk 24 jam besok:")
print(X_besok)

print("\nJumlah baris:", len(X_besok))
print("Jumlah fitur:", len(X_besok.columns))
