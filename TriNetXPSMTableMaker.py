import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🧾 TriNetX Table Formatter for Copy-Paste into Word")

# Upload CSV
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

# ✅ Deduplicate column names (safe method)
def deduplicate_columns(cols):
    seen = {}
    new_cols = []
    for col in cols:
        if col not in seen:
            seen[col] = 0
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")
    return new_cols

df_clean.columns = deduplicate_columns(df_clean.columns)

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

# ✅ Fixed merge_rows_html
def merge_rows_html(df, font_size, align):
    align_css = {"left": "left", "center": "center", "right": "right"}[align]
    html = f'''
    <style>
        td, th {{
            font-size: {font_size}pt;
            text-align: {align_css};
            padding: 6px;
            border: 1px solid #888;
            border-collapse: collapse;
        }}
    </style>
    '''
    html += '<table style="border-collapse: collapse; width: 100%;">'

    # Header row
    html += "<tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr>"

    # Precompute merge flags and spans
    n_rows, n_cols = df.shape
    skip_cell = [[False] * n_cols for _ in range(n_rows)]
    merge_span = [[1] * n_cols for _ in range(n_rows)]

    for col in range(n_cols):
        for row in range(1, n_rows):
            if df.iloc[row, col] == df.iloc[row - 1, col]:
                merge_span[row - 1][col] += 1
                skip_cell[row][col] = True
                merge_span[row][col] = 0

    # Build HTML rows
    for row in range(n_rows):
        html += "<tr>"
        for col in range(n_cols):
            if not skip_cell[row][col]:
                value = df.iloc[row, col]
                span = merge_span[row][col]
                rowspan_attr = f' rowspan="{span}"' if span > 1 else ""
                html += f"<td{rowspan_attr}>{value}</td>"
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
