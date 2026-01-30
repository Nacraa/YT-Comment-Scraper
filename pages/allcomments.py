import streamlit as st

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

if "df" in st.session_state:
    st.subheader("List Semua Komentar")
    st.dataframe(st.session_state.df, width="content")
else:
    st.warning("Data komentar belum tersedia. Silakan klik 'Tampilkan Komentar' terlebih dahulu.")

if st.button("Kembali ke halaman utama", key="back"):
    st.switch_page("app.py")