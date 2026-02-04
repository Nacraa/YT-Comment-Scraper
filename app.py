from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter
from langdetect import detect
import streamlit as st
import pandas as pd
import numpy as np

# API
API_KEY = st.secrets["API_KEY"]
youtube = build("youtube", "v3", developerKey=st.secrets["API_KEY"])

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# Header
st.markdown('<div class="header"><h1>YOUTUBE COMMENT SCRAPPER</h1>' 
            '<h6>Progam untuk mengambil, menganalisis, dan memvisualisasikan komentar Youtube secara otomatis</h6></div>',unsafe_allow_html=True)
st.write(" ")

# Input Video ID
Video_ID = st.text_input("Masukkan Video ID:")

# Popup filter kata
@st.dialog("Filter Kata (Opsional)")
def filter_dialog():
    st.markdown('<div style="font-style: italic; font-size: 13px; opacity: 0.7; text-align: center;">Masukkan kata ke dalam text field untuk tidak menghitungnya di list 10 kata terbanyak.</div>' ,unsafe_allow_html=True)
    st.session_state.filterchoose = st.text_input(" ", placeholder="Contoh: jelek keren sulit").lower().split()

    if st.button("Lanjutkan", key="submit2"):
        st.session_state.pressed = True
        st.rerun()

# Menengahkan tombol Tampilkan komentar
col1, col2, col3 = st.columns([1,1,1])
with col2:
    # Tombol Tampilkan komentar
    if st.button("Tampilkan Komentar", key="submit"):
        if "pressed" not in st.session_state:
            st.session_state.pressed = False
        filter_dialog()
    st.markdown("<br>",unsafe_allow_html=True)

#Langkah memasukkan Video ID
step1, step2, step3 = st.columns([1,1,1], gap="large")

with step1:
    st.markdown('<div class="step">1. Ambil ID dari URL video Youtube</div>', unsafe_allow_html=True)
    st.image("1.png")

with step2:
    st.markdown('<div class="step">2. Letakkan ID kedalam text field</div>', unsafe_allow_html=True)
    st.image("2.png")

with step3:
    st.markdown('<div class="step">3. Klik tombol "Tampilkan Komentar"</div>', unsafe_allow_html=True)
    st.image("3.png")

# Dialog Filter Kata
if "filterchoose" not in st.session_state:
    st.session_state.filterchoose = []

if "pressed" not in st.session_state:
    st.session_state.pressed = False

if "APIerror" not in st.session_state:
    st.session_state.APIerror = True

# Fungsi menghitung 10 kata terbanyak
def top_10_words(komentar_list):
    text = " ".join(komentar_list).lower()
    words = text.split()

    # Filter Kata Default
    stopwords = {
        # Bahasa Indonesia
        "dan", "yang", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
        "pada", "adalah", "saya", "kamu", "dia", "kami", "kita", "nya",

        # Bahasa Inggris
        "the", "a", "an", "is", "are", "to", "of", "in", "this", "and", "that", 
        "was", "but", "for", "just", "with", "when", "have", "the"
    }

    stopwords = stopwords.union(set(st.session_state.filterchoose))

    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    return Counter(filtered_words).most_common(10)

# Fungsi Mendeteksi Bahasa Komentar
def detect_language_gis(komentar_list):
    language_map = {
        "id": ("Indonesia", -2.5489, 118.0149),
        "en": ("United States", 37.0902, -95.7129),
        "ja": ("Japan", 36.2048, 138.2529),
        "ko": ("South Korea", 35.9078, 127.7669),
        "es": ("Spain", 40.4637, -3.7492),
    }

    locations = []

    for text in komentar_list:
        try:
            lang = detect(text)
            if lang in language_map:
                country, lat, lon = language_map[lang]
                locations.append({
                    "Negara": country,
                    "Latitude": lat,
                    "Longitude": lon
                })
        except:
            pass

    return pd.DataFrame(locations)

# Menampilkan Hasil
def process():
        comments = []

        if Video_ID.strip() == "":
            st.error("Video ID tidak boleh kosong!")

        else:
            try:
                # Request awal
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=Video_ID.strip(),
                    maxResults=100,
                    textFormat="plainText"
                )

                # Loop pagination
                while request:
                    response = request.execute()

                    for komentar in response["items"]:
                        snippet = komentar["snippet"]["topLevelComment"]["snippet"]
                        comments.append({
                            "Username": snippet["authorDisplayName"],
                            "Tanggal": snippet["publishedAt"],
                            "Komentar": snippet["textDisplay"]
                        })

                    request = youtube.commentThreads().list_next(request, response)

                # Tampilkan hasil komentar
                if comments:
                    df = pd.DataFrame(comments)
                    st.session_state.df = df
                    komentar_list = df["Komentar"].tolist()
                    top_words = top_10_words(komentar_list)

                    st.markdown("<hr>",unsafe_allow_html=True)
                    st.success(f"Berhasil mengambil {len(df)} komentar")
                    st.markdown(f'<div class = "thumbnail"><img src="https://img.youtube.com/vi/{Video_ID}/maxresdefault.jpg"></div>', unsafe_allow_html=True) # Memperlihatkan Thumbnail

                    # Table 10 Kata yang Sering Muncul
                    st.subheader("10 Kata yang Paling Sering Muncul")
                    top_df = pd.DataFrame(top_words, columns=["Kata", "Frekuensi"])
                    top_df.index = np.arange(1, len(top_df) + 1) # Mengubah index tabel agar dimulai dari 1

                    col_table, col_chart = st.columns(2, gap="small")

                    with col_table:
                        st.table(top_df)

                    with col_chart:
                        st.bar_chart(
                            data=top_df.set_index("Kata"),
                            use_container_width=True
                        )

                    # GIS Berdasarkan Hasil Komentar
                    st.markdown("<hr>",unsafe_allow_html=True)
                    st.subheader("GIS Berdasarkan Bahasa Komentar")

                    gis_df = detect_language_gis(komentar_list)
                    

                    if not gis_df.empty:
                        country_count = gis_df["Negara"].value_counts().reset_index()
                        country_count.columns = ["Negara", "Jumlah Komentar"]
                        country_count.index = np.arange(1, len(country_count) + 1) # Mengubah index tabel agar dimulai dari 1

                        st.markdown("**Distribusi Komentar Berdasarkan Estimasi Negara**")
                        st.table(country_count)

                        st.markdown("**Peta Estimasi Lokasi Komentar**")
                        st.map(
                            gis_df,
                            latitude="Latitude",
                            longitude="Longitude"
                        )

                        st.session_state.APIerror = False
                    else:
                        st.warning("Tidak dapat mendeteksi bahasa komentar untuk GIS.")
                else:
                    st.warning("Tidak ada komentar yang ditemukan.")

            except HttpError:
                st.error(f"Terjadi error API. Tolong masukka Video ID valid!")
                st.session_state.APIerror = True

# Halaman list semua komentar
if st.session_state.pressed:
    process()
    if Video_ID.strip() != "" and st.session_state.APIerror == False:
        if st.button("List semua komentar", key="list"):
            st.switch_page("pages/allcomments.py")
