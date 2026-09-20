import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. Ketetapan Sistem Kata Laluan (Password)
# Tukar 'pakabu123' kepada kata laluan pilihan anda sendiri
PASSWORD_RAHSIA = "haziq501"

def semak_kata_laluan():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        
    if not st.session_state["auth"]:
        st.title("🔒 Akses Disekat")
        pwd = st.text_input("Masukkan Kata Laluan Peribadi Anda:", type="password")
        if st.button("Masuk"):
            if pwd == PASSWORD_RAHSIA:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Kata laluan salah! Cuba lagi.")
        return False
    return True

# Jalankan sekatan login. Jika belum login, kod di bawah tidak akan berjalan.
if semak_kata_laluan():

    # 2. Sambungan ke Database SQLite
    conn = sqlite3.connect("kewangan.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarikh TEXT,
            jenis TEXT,
            jumlah REAL,
            kategori TEXT,
            nota TEXT
        )
    ''')
    conn.commit()

    # 3. Reka Bentuk Antaramuka (UI)
    st.set_page_config(page_title="Penjejak Duit HAZIQ", page_icon="💰", layout="centered")
    st.title("📱 Penjejak Kewangan Peribadi")
    
    # Butang Logout ringkas di penjuru
    if st.sidebar.button("🔒 Log Keluar"):
        st.session_state["auth"] = False
        st.rerun()

    # Borang Input Data
    with st.form("borang_kewangan", clear_on_submit=True):
        st.subheader("📝 Tambah Transaksi Baru")
        tarikh = st.date_input("Tarikh", datetime.now()).strftime('%Y-%m-%d')
        jenis = st.selectbox("Jenis Aliran", ["Duit Masuk", "Duit Keluar"])
        jumlah = st.number_input("Jumlah (RM)", min_value=0.01, step=0.01, format="%.2f")
        kategori = st.selectbox("Kategori", ["Gaji", "Makanan", "Keperluan Rumah", "Simpanan", "Hiburan", "Transport", "Lain-lain"])
        nota = st.text_input("Nota / Catatan (Opsional)")
        
        hantar = st.form_submit_button("Simpan Transaksi")

    if hantar:
        c.execute('''
            INSERT INTO transaksi (tarikh, jenis, jumlah, kategori, nota)
            VALUES (?, ?, ?, ?, ?)
        ''', (tarikh, jenis, jumlah, kategori, nota))
        conn.commit()
        st.success(f"Berjaya menyimpan {jenis}: RM{jumlah:.2f}!")

    st.divider()

    # 4. Ambil Data Terkini & Proses Maklumat Graf
    df = pd.read_sql_query("SELECT tarikh, jenis, jumlah, kategori, nota FROM transaksi ORDER BY id DESC", conn)

    if not df.empty:
        # Kira Ringkasan Duit
        total_masuk = df[df['jenis'] == 'Duit Masuk']['jumlah'].sum()
        total_keluar = df[df['jenis'] == 'Duit Keluar']['jumlah'].sum()
        baki_bersih = total_masuk - total_keluar

        # Papar Kad Ringkasan (Metrics)
        st.subheader("📊 Ringkasan Poket Anda")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Masuk", f"RM{total_masuk:,.2f}")
        col2.metric("💸 Total Keluar", f"RM{total_keluar:,.2f}")
        col3.metric("📈 Baki Bersih", f"RM{baki_bersih:,.2f}")

        st.divider()

        # 📊 PENJANAAN CARTA PAI (PIE CHART) YANG 'REAL'
        st.subheader("🍕 Agihan Duit Keluar Mengikut Kategori")
        df_keluar = df[df['jenis'] == 'Duit Keluar']

        if not df_keluar.empty:
            # Kumpulkan data mengikut kategori
            df_kategori = df_keluar.groupby('kategori')['jumlah'].sum().reset_index()
            
            # Buat Carta Pai Plotly interaktif yang mesra telefon
            fig = px.pie(
                df_kategori, 
                values='jumlah', 
                names='kategori', 
                hole=0.4, # Membuat bentuk donut chart supaya nampak moden
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            
            # Papar graf di Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data 'Duit Keluar' untuk dijana sebagai Carta Pai.")

        st.divider()

        # 📜 Papar Jadual Sejarah Transaksi
        st.subheader("📜 Sejarah Transaksi")
        df.columns = ["Tarikh", "Jenis Aliran", "Jumlah (RM)", "Kategori", "Nota/Catatan"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada transaksi disimpan. Sila masukkan data pertama anda di atas!")
