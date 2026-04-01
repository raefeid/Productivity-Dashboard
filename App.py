import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Team Time Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

with open("clockify-dashboard.html", "r") as f:
    html_content = f.read()

components.html(html_content, height=2000, scrolling=True)
