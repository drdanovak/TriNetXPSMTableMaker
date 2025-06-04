import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📊 TriNetX Journal-Style Table Formatter with Row Reordering")

uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# Load and clean CSV
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# Sidebar Controls
st.sidebar.header("🛠️ Table Settings")
font_size = st.sidebar.slider("Font Size", 6, 18, 10)
h_align = st.sidebar.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
v_align = st.sidebar.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
journal_style = st.sidebar.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
decimal_places = st.sidebar.slider("Round numerical values to:", 0, 5, 2)
group_input = st.sidebar.text_input("Group header row numbers (comma-separated)", "")

# Column selection and renaming
with st.sidebar.expander("📋 Column Selection and Renaming", expanded=True):
    all_columns = list(df_data.columns)
    selected_columns = st.multiselect("Select columns to include", all_columns, default=all_columns)
    rename_dict = {}
    for col in selected_columns:
        rename_dict[col] = st.text_input(f"Rename '{col}'", col, key=f"rename_{col}")

# Clean and rename
df_trimmed = df_data[selected_columns].copy()
df_trimmed.rename(columns=rename_dict, inplace=True)
df_trimmed.fillna("", inplace=True)

# Round numeric columns
for col in df_trimmed.columns:
    try:
        df_trimmed[col] = df_trimmed[col].astype(float).round(decimal_places)
    except:
        continue

# Replace "0" with "p<.001" for p-values
for col in df_trimmed.columns:
    if "p-Value" in col:
        df_trimmed[col] = df_trimmed[col].apply(lambda x: "p<.001" if str(x).strip() == "0" else x)

# Deduplicate first column
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

# Drag-and-drop via AgGrid
st.subheader("🖱️ Drag and Reorder Table")
gb = GridOptionsBuilder.from_dataframe(df_trimmed)
gb.configure_default_column(editable=True, resizable=True)
gb.configure_grid_options(rowDragManaged=True, animateRows=True)
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gridOptions = gb.build()

grid_response = AgGrid(
    df_trimmed,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MANUAL,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    allow_unsafe_jscode=True,
    height=500,
    reload_data=True
)

df_ordered = pd.DataFrame(grid_response["data"])

# Parse group headers
group_indices = set()
try:
    if group_input.strip():
        group_indices = set(int(i.strip()) for i in group_input.split(","))
except:
    st.sidebar.error("❌ Invalid row numbers")

# CSS style generator
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

# HTML Table Renderer
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

# Final table
html_table = generate_html_table(df_ordered, group_indices, journal_style, font_size, h_align, v_align)
st.markdown("### 🧾 Copy-Ready Table")
st.markdown(html_table, unsafe_allow_html=True)

# Copy button
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
