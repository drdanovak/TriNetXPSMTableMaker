import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📊 TriNetX NEJM-Style Table Formatter")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Step 1: Load and clean data
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# Step 2: Column selection
st.sidebar.header("🛠️ Table Configuration")

columns = list(df_data.columns)
selected_columns = st.sidebar.multiselect("Select columns to include", columns, default=columns[:10])
df_trimmed = df_data[selected_columns].copy().fillna("")

# Step 3: Header renaming
st.sidebar.markdown("✍️ **Rename Headers**")
renamed_columns = {}
for col in selected_columns:
    renamed = st.sidebar.text_input(f"Rename '{col}'", value=col)
    renamed_columns[col] = renamed
df_trimmed.rename(columns=renamed_columns, inplace=True)

# Step 4: Manual group header rows
group_input = st.sidebar.text_input("Group header row numbers (comma-separated)", value="")
group_indices = set()
try:
    if group_input.strip():
        group_indices = set(int(i.strip()) for i in group_input.split(","))
except:
    st.sidebar.error("❌ Invalid row numbers. Please enter comma-separated integers.")

# Step 5: NEJM-style HTML rendering
def generate_html_table(df, group_rows):
    html = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 10pt;
        }
        th, td {
            border: 1px solid black;
            padding: 6px;
            text-align: center;
            vertical-align: middle;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .group-row {
            background-color: #e6e6e6;
            font-weight: bold;
            text-align: left;
        }
    </style>
    <table>
        <tr>""" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"

    for i, row in df.iterrows():
        if i in group_rows:
            html += f'<tr class="group-row"><td colspan="{len(df.columns)}">{row.iloc[1]}</td></tr>'
        else:
            html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

nejm_html = generate_html_table(df_trimmed, group_indices)

# Step 6: Show and copy
st.markdown("### 📋 Copy This Table and Paste into Word")
st.markdown(nejm_html, unsafe_allow_html=True)

copy_button_html = f"""
<div style="display:none;" id="copySource" contenteditable="true">
    {nejm_html}
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
