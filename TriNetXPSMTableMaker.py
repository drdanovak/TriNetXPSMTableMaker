import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📊 TriNetX Journal-Style Table Formatter")

uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean CSV
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# Store original for reset
original_df = df_data.copy()

# Sidebar Settings
st.sidebar.header("🛠️ Table Settings")
font_size = st.sidebar.slider("Font Size", 6, 18, 10)
h_align = st.sidebar.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
v_align = st.sidebar.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
journal_style = st.sidebar.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
decimal_places = st.sidebar.slider("Round numerical values to", 0, 5, 2)
edit_toggle = st.sidebar.checkbox("✏️ Edit Table (with drag-and-drop)")
merge_duplicates = st.sidebar.checkbox("🔁 Merge duplicate row titles")
add_column_grouping = st.sidebar.checkbox("📌 Add Before/After PSM Column Separators (with headers)")
reset_table = st.sidebar.button("🔄 Reset Table to Default")

# Updated default columns and order with group markers
default_columns = [
    "Characteristic Name", "Characteristic ID", "Category",
    "Cohort 1 Before: Patient Count", "Cohort 1 Before: % of Cohort", "Cohort 1 Before: Mean", "Cohort 1 Before: SD",
    "Cohort 2 Before: Patient Count", "Cohort 2 Before: % of Cohort", "Cohort 2 Before: Mean", "Cohort 2 Before: SD", "Before: p-Value", "Before: Standardized Mean Difference",
    "Cohort 1 After: Patient Count", "Cohort 1 After: % of Cohort", "Cohort 1 After: Mean", "Cohort 1 After: SD",
    "Cohort 2 After: Patient Count", "Cohort 2 After: % of Cohort", "Cohort 2 After: Mean", "Cohort 2 After: SD", "After: p-Value", "After: Standardized Mean Difference"
]

available_columns = list(df_data.columns)
filtered_columns = [col for col in default_columns if col in available_columns]
df_trimmed = df_data[filtered_columns].copy()

with st.sidebar.expander("📋 Column Selection and Renaming", expanded=False):
    selected_columns = st.multiselect("Select columns to include", available_columns, default=filtered_columns)
    rename_dict = {}
    for col in selected_columns:
        rename_dict[col] = st.text_input(f"Rename '{col}'", col, key=f"rename_{col}")

df_trimmed = df_data[selected_columns].copy()
df_trimmed.rename(columns=rename_dict, inplace=True)
df_trimmed.fillna("", inplace=True)

for col in df_trimmed.columns:
    try:
        df_trimmed[col] = df_trimmed[col].astype(float).round(decimal_places)
    except:
        pass

for col in df_trimmed.columns:
    if "p-Value" in col:
        df_trimmed[col] = df_trimmed[col].apply(lambda x: "p<.001" if str(x).strip() == "0" else x)

st.markdown("### 🧾 Formatted Table Preview")

html_table = """
<div id="copySource" contenteditable="true">
""" + df_trimmed.to_html(index=False, escape=False) + """
</div>
<button onclick="copyTableToClipboard()">📋 Copy Table</button>
<button onclick="copyToWord()">📄 Export to Word</button>
"""

copy_script = """
<script>
function copyTableToClipboard() {
  const range = document.createRange();
  const copySource = document.getElementById("copySource");
  range.selectNodeContents(copySource);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand("copy");
  sel.removeAllRanges();
  alert("✅ Table copied to clipboard!");
}

function copyToWord() {
  const tableHTML = document.getElementById("copySource").innerHTML;
  const blob = new Blob(['<html><head><meta charset=\"utf-8\"></head><body>' + tableHTML + '</body></html>'], {
    type: 'application/msword'
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'TriNetX_Table.doc';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  alert("✅ Word-compatible file generated and downloaded.");
}
</script>
"""

st.markdown(html_table + copy_script, unsafe_allow_html=True)
