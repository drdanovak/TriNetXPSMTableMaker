import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📊 TriNetX Journal-Style Table Formatter")

# Upload
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# Sidebar controls
st.sidebar.header("🛠️ Table Settings")
font_size = st.sidebar.slider("Font Size", 6, 18, 10)
h_align = st.sidebar.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
v_align = st.sidebar.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
journal_style = st.sidebar.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
group_input = st.sidebar.text_input("Row numbers for group headers (comma-separated)", "")

# Column selection and renaming in sidebar expander
columns = list(df_data.columns)
default_selected = columns[:10]
rename_dict = {}

with st.sidebar.expander("📋 Column Selection and Renaming", expanded=True):
    selected = st.multiselect("Select columns to include", columns, default=default_selected)
    for col in selected:
        new_name = st.text_input(f"Rename '{col}'", value=col, key=f"rename_{col}")
        rename_dict[col] = new_name

# Trim and rename
df_trimmed = df_data[selected].copy()
df_trimmed.rename(columns=rename_dict, inplace=True)
df_trimmed.fillna("", inplace=True)

# Remove repeated row labels in first column
def deduplicate_first_column(df):
    prev = None
    new_col = []
    for val in df.iloc[:, 0]:
        if val == prev:
            new_col.append("")
        else:
            new_col.append(val)
            prev = val
    df.iloc[:, 0] = new_col
    return df

df_trimmed = deduplicate_first_column(df_trimmed)

# Group header parsing
group_indices = set()
try:
    if group_input.strip():
        group_indices = set(int(i.strip()) for i in group_input.split(","))
except:
    st.sidebar.error("❌ Invalid row numbers")

# Journal CSS
def get_journal_css(journal_style, font_size, h_align, v_align):
    return f"""
    <style>
    table {{
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: {font_size}pt;
    }}
    th, td {{
        border: 1px solid black;
        padding: 6px;
        text-align: {h_align};
        vertical-align: {v_align};
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

# Render table
def generate_html_table(df, group_rows, journal_style, font_size, h_align, v_align):
    css = get_journal_css(journal_style, font_size, h_align, v_align)
    html = css + "<table><tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
    for i, row in df.iterrows():
        if i in group_rows:
            html += f'<tr class="group-row"><td colspan="{len(df.columns)}">{row.iloc[1]}</td></tr>'
        else:
            html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

# Generate and show table
html_table = generate_html_table(df_trimmed, group_indices, journal_style, font_size, h_align, v_align)
st.markdown("### 🧾 Copy-Ready Table")
st.markdown(html_table, unsafe_allow_html=True)

# Copy button in sidebar
copy_button_html = f"""
<div style="display:none;" id="copySource" contenteditable="true">
    {html_table}
</div>
<button onclick="copyTableToClipboard()" style="padding:6px 12px; font-size:14px;">📋 Copy Table to Clipboard</button>
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
