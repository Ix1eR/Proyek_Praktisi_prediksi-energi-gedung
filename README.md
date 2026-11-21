# Proyek Praktisi Energi Gedung · Tim 18

**Kasus:** [2 Energi Gedung](https://github.com/nurhikam/mkb-ml-project/blob/main/kasus/02-energi-gedung/brief.md) · **Aplikasi:** [tautan aplikasi](https://proyekpraktisiprediksi-energi-gedung-66kdo84jnq5wr5g8gfioxw.streamlit.app/) · **Video:** [Tautan Video](https://youtu.be/JA7z6u8EDkE)

| Anggota | NIM | Bagian yang dikerjakan |
|---|---|---|
| Rafa Mouzaqy Haniebu | 2406097 | API, Aplikasi, UI Streamlit, Model, Revisi Model, Uji Aplikasi, Data, Laporan, Video Editting |
| Evandri Nur Fawwaz | [NIM] | Video SHooting, Laporan |

## Masalah dan pengguna

Pengguna utama model ini adalah Pengelola gedung yang  membutuhkan perkiraan konsumsi listrik besok untuk membantu merencanakan penggunaan energi, termasuk pengoperasian pendingin gedung. Proyek ini memprediksi konsumsi listrik per jam selama 24 jam berikutnya berdasarkan kalender, riwayat konsumsi, serta informasi suhu dan okupansi. Hasilnya berupa grafik, tabel prediksi, dan total energi harian yang dapat menjadi bahan pertimbangan pengelola, bukan keputusan pengoperasian otomatis.

## Data dan pembersihan

| Masalah yang ditemukan | Jumlah baris | Cara menangani |
|---|---|---|
| Baris sama persis | 78 | Menghapus duplikat dan mempertahankan satu catatan untuk setiap waktu |
| Konsumsi negatif | 19 | Mengubah target menjadi nilai kosong |
| Konsumsi berkode kesalahan 99999 | 19 | Mengubah target menjadi nilai kosong |
| Suhu kosong sebelum pembersihan | 95 | Nilai kosong pada fitur turunannya diisi median melalui pipeline model |
| Kelembapan kosong sebelum pembersihan | 95 | Diperiksa saat pembersihan, tetapi tidak digunakan sebagai fitur model |
| Okupansi kosong sebelum pembersihan | 203 | Nilai kosong pada fitur turunannya diisi median melalui pipeline model |
| Jam yang hilang | 120 jam | Melengkapi indeks per jam menggunakan `reindex` agar lag sesuai selisih waktu |
| Tanggal tidak terbaca setelah mencoba format yang tersedia | 0 | Membaca format ISO, format tanggal Indonesia dengan jam bertitik, dan format dengan detik |

## Hasil

| Model | MAE *validation* (kWh) | MAE *test* (kWh) |
|---|---|---|
| *Baseline*: konsumsi pada jam yang sama minggu lalu, lag168 | 22,8108 | 24,8253 |
| *Final Model*: **HistGradientBoosting, 15 daun (HistGB_15)** | **10,3168** | **10,0532** |

Model final dipilih berdasarkan MAE validation terkecil, kemudian dilatih ulang pada train dan validation. Pengaturan modelnya adalah 200 iterasi, maksimal 15 daun, regularisasi L2 sebesar 10, `early_stopping=False`, dan `random_state=18`. MAE test turun sekitar **59,50%** terhadap baseline. Persentase ini merupakan penurunan kesalahan prediksi, bukan persentase penghematan energi.

*Threshold* yang dipakai: **tidak ada**, karena tugas ini merupakan regresi dengan keluaran angka kWh. Hasil prediksi dibatasi minimum nol menggunakan `clip(min=0)`, bukan threshold klasifikasi.

## Cara menjalankan

```bash
pip install -r requirements.txt
uvicorn app.api.main:app --reload       # API
streamlit run app/ui/streamlit_app.py   # aplikasi
```

## Struktur repositori

```
notebooks/      notebook dari EDA sampai penyimpanan model
data/           data mentah (dan data bersih jika perlu)
src/features.py fungsi pembuat fitur, dipakai saat pelatihan dan saat prediksi
artifacts/      model.joblib + metadata.json
app/            API (FastAPI) dan antarmuka (Streamlit)
```

## Keterbatasan

- Dataset bersifat sintetis. Hasil belum membuktikan kemampuan model pada gedung nyata.
- Suhu dan okupansi minggu sebelumnya menjadi proksi saat pelatihan. Kualitas prediksi dapat berubah ketika memakai prakiraan nyata.
- Antarmuka saat ini memakai satu nilai suhu dan okupansi sepanjang hari. Pola perubahan keduanya per jam belum dapat dimasukkan pengguna.
- Prediksi membutuhkan riwayat yang sesuai. Dataset bawaan hanya mendukung demo hari setelah akhir riwayat, yaitu 1 Juli 2026.
- Evaluasi test dilakukan sebagai simulasi harian bergulir. Riwayat aktual hari sebelumnya boleh menjadi fitur hari berikutnya, tetapi model tidak dilatih ulang selama test. Hasil ini bukan prediksi dua bulan sekaligus tanpa pembaruan riwayat.
- Koneksi lewat tunnel bergantung pada server backend dan tunnel yang terus berjalan. Ketersediaan halaman Streamlit saja belum menjamin prediksi dapat diproses.
- MAE mengukur kesalahan energi per jam, bukan kesalahan total harian, akurasi persentase, atau penghematan biaya listrik.

