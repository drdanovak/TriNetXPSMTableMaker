import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📊 TriNetX NEJM/AMA-Style Table Formatter")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean data
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# Sidebar controls
st.sidebar.header("🛠️ Table Configuration")
columns = list(df_data.columns)
selected_columns = st.sidebar.multiselect("Select columns to include", columns, default=columns[:10])
font_size = st.sidebar.slider("Font Size (pt)", 6, 18, 10)
alignment = st.sidebar.selectbox("Text Alignment", ["left", "center", "right"])
journal_style = st.sidebar.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])

# Rename headers
st.sidebar.markdown("✍️ **Rename Headers**")
renamed_columns = {}
for col in selected_columns:
    new_name = st.sidebar.text_input(f"Rename '{col}'", value=col)
    renamed_columns[col] = new_name

# Data prep
df_trimmed = df_data[selected_columns].copy()
df_trimmed.fillna("", inplace=True)
df_trimmed.rename(columns=renamed_columns, inplace=True)

# Manual group row control
group_input = st.sidebar.text_input("Row numbers for group headers (comma-separated)", "")
group_indices = set()
try:
    if group_input.strip():
        group_indices = set(int(i.strip()) for i in group_input.split(","))
except:
    st.sidebar.error("❌ Invalid row numbers.")

# Journal styling CSS
def get_journal_css(style, font_size, alignment):
    align_css = {"left": "left", "center": "center", "right": "right"}[alignment]
    if style in ["NEJM", "AMA", "APA", "JAMA"]:
        return f"""
        <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: {font_size}pt;
            text-align: {align_css};
        }}
        th, td {{
            border: 1px solid black;
            padding: 6px;
            vertical-align: top;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .group-row {{
            background-color: #e6e6e6;
            font-weight: bold;
            text-align: left;
        }}
        </style>
        """
    else:
        return f"""
        <style>
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: {font_size}pt;
            font-family: Arial, sans-serif;
        }}
        th, td {{
            border: 1px solid #888;
            padding: 6px;
            text-align: {align_css};
            vertical-align: middle;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .group-row {{
            background-color: #e6e6e6;
            font-weight: bold;
            text-align: left;
        }}
        </style>
        """

# HTML rendering
def generate_html_table(df, group_rows, style, font_size, alignment):
    css = get_journal_css(style, font_size, alignment)
    html = css + "<table><tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
    for i, row in df.iterrows():
        if i in group_rows:
            html += f'<tr class="group-row"><td colspan="{len(df.columns)}">{row.iloc[1]}</td></tr>'
        else:
            html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

# Generate HTML
html_table = generate_html_table(df_trimmed, group_indices, journal_style, font_size, alignment)

# Main display
st.markdown("### 🧾 Copy This Table Below and Paste into Word")
st.markdown(html_table, unsafe_allow_html=True)

# Sidebar: Copy to clipboard button
copy_button_html = f"""
<div style="display:none;" id="copySource" contenteditable="true">
    {html_table}
</div>
<button onclick="copyTableToClipboard()" style="padding:6px 12px; font-size:14px;">📋 Copy HTML Table to Clipboard</button>
<script>
function copyTableToClipboard() {{
    var range = document.createRange();
    var selection = window.getSelection();
    var copyNode = document.getElementById("copySource");
    range.selectNodeContents(copyNode);
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand("copy");
    selection.removeAllRanges();
    alert("✅ Table copied to clipboard!");
}}
</script>
"""

st.sidebar.subheader("📎 Copy Table to Clipboard")
components.html(copy_button_html, height=130)
