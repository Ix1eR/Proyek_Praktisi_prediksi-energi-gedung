# Import library dan konfigurasi
import streamlit as st
import pandas as pd
import requests
from datetime import date
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Prediksi Energi Gedung",
    page_icon="⚡",
    layout="wide"
)

# Alamat FastAPI
API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


st.title("⚡ Prediksi Konsumsi Energi Gedung")

st.write(
    "Aplikasi ini digunakan untuk memperkirakan "
    "konsumsi listrik gedung selama 24 jam "
    "berdasarkan suhu, okupansi, dan data historis."
)

st.divider()

st.subheader("Masukkan Data Prediksi")

with st.form("form_prediksi"):

    col1, col2 = st.columns(2)

    with col1:
        tanggal = st.date_input(
            "Tanggal prediksi",
            value=date(2026, 7, 1)
        )

        suhu = st.number_input(
            "Prakiraan suhu luar (°C)",
            min_value=-10.0,
            max_value=50.0,
            value=25.0,
            step=0.5
        )

    with col2:
        okupansi = st.number_input(
            "Perkiraan jumlah orang",
            min_value=0,
            max_value=10000,
            value=150,
            step=1
        )

        hari_libur = st.checkbox(
            "Hari libur nasional"
        )

    tombol = st.form_submit_button(
        "Prediksi Konsumsi Listrik",
        type="primary",
        use_container_width=True
    )
# Mengirim data ke FastAPI
if tombol:

    # Mengumpulkan input dari pengguna
    data_input = {
        "tanggal": str(tanggal),
        "suhu": suhu,
        "okupansi": okupansi,
        "hari_libur": int(hari_libur)
    }

    try:
        with st.spinner("Sedang memproses prediksi..."):

            # Mengirim data ke FastAPI
            response = requests.post(
                f"{API_URL}/predict",
                json=data_input,
                timeout=60
            )

        # Memeriksa respons API
        if response.status_code == 200:
            hasil = response.json()

            st.session_state["hasil_prediksi"] = hasil

        else:
            pesan = response.json().get(
                "detail", "Terjadi kesalahan pada API."
            )
            st.error(f"Prediksi gagal: {pesan}")
            st.session_state.pop("hasil_prediksi", None)

    except requests.exceptions.RequestException:
        st.error(
            "Tidak dapat terhubung ke FastAPI. "
            "Pastikan server FastAPI sudah berjalan."
        )
        st.session_state.pop("hasil_prediksi", None)
# Menampilkan hasil prediksi
if "hasil_prediksi" in st.session_state:

    hasil = st.session_state["hasil_prediksi"]

    # Mengubah hasil JSON menjadi tabel
    tabel = pd.DataFrame(hasil["prediksi"])

    tabel["waktu"] = pd.to_datetime(tabel["waktu"])

    st.divider()
    st.subheader("Hasil Prediksi Konsumsi Listrik")

    # Menampilkan informasi utama
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Konsumsi Listrik",
            f"{hasil['total_kWh']:,.2f} kWh"
        )

    with col2:
        st.metric(
            "Jumlah Jam Prediksi",
            f"{hasil['jumlah_jam']} jam"
        )

    # Membuat grafik
    st.subheader("Grafik Prediksi 24 Jam")

    grafik = tabel.set_index("waktu")["prediksi_kWh"]

    st.line_chart(grafik)

    # Menampilkan tabel
    st.subheader("Tabel Hasil Prediksi")

    st.dataframe(
        tabel,
        use_container_width=True,
        hide_index=True
    )

    # Mengunduh hasil prediksi
    csv = tabel.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Hasil Prediksi CSV",
        data=csv,
        file_name="hasil_prediksi_energi.csv",
        mime="text/csv"
    )