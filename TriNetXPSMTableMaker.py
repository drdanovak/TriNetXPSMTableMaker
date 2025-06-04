import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧾 TriNetX Table Formatter for Copy-Paste into Word")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Read raw data from row 10
df_raw = pd.read_csv(uploaded_file, header=None)

def extract_clean_table(df):
    df_clean = df.iloc[9:].reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]
    df_clean = df_clean[1:].reset_index(drop=True)
    return df_clean

df_clean = extract_clean_table(df_raw)

# Deduplicate columns
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

# Sidebar
st.sidebar.header("🛠️ Display Options")
table_title = st.sidebar.text_input("Table Title", "Formatted TriNetX Table")
font_size = st.sidebar.slider("Font Size (pt)", 6, 18, 10)
alignment = st.sidebar.selectbox("Text Alignment", ["left", "center", "right"])
merge_rows = st.sidebar.checkbox("Merge Repeated Row Labels", value=True)
decimals = st.sidebar.slider("Decimal Places", 0, 5, 2)

# Format data
df_display = df_clean.copy()
for col in df_display.columns:
    try:
        df_display[col] = df_display[col].astype(float).round(decimals)
    except:
        pass
df_display = df_display.fillna("")

# Merge function
def merge_rows_html(df, font_size, align, title=None):
    align_css = {"left": "left", "center": "center", "right": "right"}[align]
    html = f'''
    <style>
        td, th {{
            font-size: {font_size}pt;
            text-align: {align_css};
            padding: 6px;
            border: 1px solid #888;
            border-collapse: collapse;
            vertical-align: top;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
    </style>
    '''
    if title:
        html += f'<h3 style="font-size:{font_size + 2}pt; text-align:{align_css};">{title}</h3>'

    html += '<table>'
    html += "<tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"

    n_rows, n_cols = df.shape

    for row in range(n_rows):
        html += "<tr>"
        for col in range(n_cols):
            if merge_rows:
                value = df.iloc[row, col]
                if row == 0 or df.iloc[row, col] != df.iloc[row - 1, col]:
                    span = 1
                    for next_row in range(row + 1, n_rows):
                        if df.iloc[next_row, col] == value:
                            span += 1
                        else:
                            break
                    rowspan_attr = f' rowspan="{span}"' if span > 1 else ""
                    html += f"<td{rowspan_attr}>{value}</td>"
                else:
                    continue
            else:
                html += f"<td>{df.iloc[row, col]}</td>"
        html += "</tr>"
    html += "</table>"
    return html

# Generate HTML
html = merge_rows_html(df_display, font_size, alignment, table_title)

# Display Table
st.markdown("### 🧾 Copy This Table Below and Paste into Word")
st.markdown(html, unsafe_allow_html=True)

# --- SIDEBAR COPY BUTTON THAT WORKS ---
from html import escape

escaped_html = escape(html)  # Escape <, > for textarea

copy_html_code = f"""
<textarea id="htmlTable" style="width:100%; height:200px;">{escaped_html}</textarea>
<button onclick="copyHTML()">📋 Copy Table to Clipboard</button>
<script>
function copyHTML() {{
  var copyText = document.getElementById("htmlTable");
  copyText.select();
  document.execCommand("copy");
  alert("✅ Table copied to clipboard!");
}}
</script>
"""

st.sidebar.subheader("📋 Copy HTML Table")
components.html(copy_html_code, height=250)

