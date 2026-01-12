from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter
import streamlit as st
import pandas as pd

# API
API_KEY = st.secrets["API_KEY"]
youtube = build("youtube", "v3", developerKey=st.secrets["API_KEY"])

st.title("Tampilan Komentar YouTube (Streamlit)")

# Input Video ID dan Kata yang di-filter
Video_ID = st.text_input("Masukkan Video ID:")
filterchoose = st.text_input("Masukkan kata yang ingin di filter:").split()

# Fungsi menghitung 10 kata terbanyak
def top_10_words(komentar_list):
    text = " ".join(komentar_list).lower()
    words = text.split()

    stopwords = {
        "dan", "yang", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
        "pada", "adalah", "saya", "kamu", "dia", "kami", "kita",
        "the", "a", "an", "is", "are", "to", "of", "in"
    }

    stopwords = stopwords.union(set(filterchoose))

    filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
    return Counter(filtered_words).most_common(10)

# Tombol ambil komentar
if st.button("Tampilkan Komentar"):
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
                st.success(f"Berhasil mengambil {len(df)} komentar")
                st.dataframe(df, use_container_width=True)

                # ===== TOP 10 KATA TERBANYAK =====
                komentar_list = df["Komentar"].tolist()
                top_words = top_10_words(komentar_list)

                st.subheader("10 Kata yang Paling Sering Muncul")
                top_df = pd.DataFrame(top_words, columns=["Kata", "Frekuensi"])
                st.table(top_df)
            else:
                st.warning("Tidak ada komentar yang ditemukan.")

        except HttpError as e:
            st.error(f"Terjadi error API: {e}")
