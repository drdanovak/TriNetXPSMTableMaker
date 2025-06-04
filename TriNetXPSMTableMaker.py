import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🧾 TriNetX Table Formatter for Copy-Paste into Word")

# Upload
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean
df_raw = pd.read_csv(uploaded_file)

def extract_clean_table(df):
    for i, row in df.iterrows():
        if "Characteristic" in str(row[0]):
            start = i
            break
    df_clean = df.iloc[start:].reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]
    df_clean = df_clean[1:].reset_index(drop=True)
    return df_clean

df_clean = extract_clean_table(df_raw)

# Sidebar formatting
st.sidebar.header("🛠️ Display Options")
font_size = st.sidebar.slider("Font Size (pt)", 6, 18, 10)
alignment = st.sidebar.selectbox("Text Alignment", ["left", "center", "right"])
merge_rows = st.sidebar.checkbox("Merge Repeated Row Labels", value=True)

# Optional rounding
decimals = st.sidebar.slider("Decimal Places", 0, 5, 2)
df_display = df_clean.copy()
for col in df_display.columns:
    try:
        df_display[col] = df_display[col].astype(float).round(decimals)
    except:
        pass

# Merge repeated labels
def merge_rows_html(df, font_size, align):
    align_css = {"left": "left", "center": "center", "right": "right"}[align]
    html = f'<style>td, th {{ font-size: {font_size}pt; text-align: {align_css}; padding: 6px; border: 1px solid #888; border-collapse: collapse; }}</style>'
    html += '<table style="border-collapse: collapse; width: 100%;">'

    # Headers
    html += "<tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr>"

    # Body with merged rows
    last_seen = [""] * len(df.columns)
    rowspan = [1] * len(df.columns)
    skip_cell = [[False]*len(df.columns) for _ in range(len(df))]

    for col in range(len(df.columns)):
        for row in range(1, len(df)):
            if df.iloc[row, col] == df.iloc[row-1, col]:
                rowspan[row - rowspan[col]][col] += 1
                skip_cell[row][col] = True
            else:
                rowspan[row][col] = 1

    for row in range(len(df)):
        html += "<tr>"
        for col in range(len(df.columns)):
            if not skip_cell[row][col]:
                cell = df.iloc[row, col]
                span = rowspan[row][col]
                if span > 1:
                    html += f'<td rowspan="{span}">{cell}</td>'
                else:
                    html += f"<td>{cell}</td>"
        html += "</tr>"

    html += "</table>"
    return html

# Choose merge or not
if merge_rows:
    html = merge_rows_html(df_display, font_size, alignment)
else:
    html = df_display.to_html(index=False, border=1, escape=False)

# Output
st.markdown("### 🧾 Copy This Table Below and Paste into Word")
st.markdown(html, unsafe_allow_html=True)
