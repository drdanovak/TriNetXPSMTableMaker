import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit.components.v1 as components

# --- Page Setup ---
st.set_page_config(layout="wide")
st.title("📊 TriNetX Journal-Style Table Formatter")

# --- File Upload ---
uploaded_file = st.file_uploader("📂 Upload your TriNetX CSV file", type="csv")
if not uploaded_file:
    st.stop()

# --- Load and Clean CSV ---
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)

# --- Default Column Set ---
default_columns = [
    "Characteristic Name", "Characteristic ID", "Category",
    "Cohort 1 Before: Patient Count", "Cohort 1 Before: % of Cohort", "Cohort 1 Before: Mean", "Cohort 1 Before: SD", "Cohort 1 Before: Min", "Cohort 1 Before: Max",
    "Cohort 2 Before: Patient Count", "Cohort 2 Before: % of Cohort", "Cohort 2 Before: Mean", "Cohort 2 Before: SD", "Cohort 2 Before: Min", "Cohort 2 Before: Max",
    "Before: p-Value", "Before: Standardized Mean Difference",
    "Cohort 1 After: Patient Count", "Cohort 1 After: % of Cohort", "Cohort 1 After: Mean", "Cohort 1 After: SD", "Cohort 1 After: Min", "Cohort 1 After: Max",
    "Cohort 2 After: Patient Count", "Cohort 2 After: % of Cohort", "Cohort 2 After: Mean", "Cohort 2 After: SD", "Cohort 2 After: Min", "Cohort 2 After: Max",
    "After: p-Value", "After: Standardized Mean Difference"
]

available_columns = list(df_data.columns)
filtered_columns = [col for col in default_columns if col in available_columns]
df_filtered = df_data[filtered_columns].copy()

# --- Sidebar Settings ---
st.sidebar.header("🛠️ Table Settings")
font_size = st.sidebar.slider("Font Size", 6, 18, 10)
h_align = st.sidebar.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
v_align = st.sidebar.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
journal_style = st.sidebar.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
decimal_places = st.sidebar.slider("Round numerical values to", 0, 5, 2)
show_aggrid = st.sidebar.checkbox("🔽 Enable Drag-and-Drop Reordering")

# --- Column Selection and Renaming ---
with st.sidebar.expander("📋 Column Selection and Renaming", expanded=False):
    selected_columns = st.multiselect("Select columns to include", available_columns, default=filtered_columns)
    rename_dict = {}
    for col in selected_columns:
        rename_dict[col] = st.text_input(f"Rename '{col}'", col, key=f"rename_{col}")

# --- Apply Column Selection and Rename ---
df_trimmed = df_data[selected_columns].copy()
df_trimmed.rename(columns=rename_dict, inplace=True)
df_trimmed.fillna("", inplace=True)

# --- Round Numeric Columns ---
for col in df_trimmed.columns:
    try:
        df_trimmed[col] = df_trimmed[col].astype(float).round(decimal_places)
    except:
        continue

# --- Replace 0 with p<.001 in p-value columns ---
for col in df_trimmed.columns:
    if "p-Value" in col:
        df_trimmed[col] = df_trimmed[col].apply(lambda x: "p<.001" if str(x).strip() == "0" else x)

# --- Display Table with Optional Reordering ---
st.subheader("📋 Editable Table")
if show_aggrid:
    gb = GridOptionsBuilder.from_dataframe(df_trimmed)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_grid_options(rowDragManaged=True, animateRows=True)
    gb.configure_selection(selection_mode="single")
    gridOptions = gb.build()

    grid_response = AgGrid(
        df_trimmed,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        height=500,
        reload_data=True
    )

    df_trimmed = pd.DataFrame(grid_response["data"])

# --- CSS and HTML Generation ---
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
    </style>
    """

def generate_html_table(df, journal_style, font_size, h_align, v_align):
    css = get_journal_css(journal_style, font_size, h_align, v_align)
    html = css + "<table><tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
    for _, row in df.iterrows():
        html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    html += "</table>"
    return html

# --- Render Final Table ---
html_table = generate_html_table(df_trimmed, journal_style, font_size, h_align, v_align)
st.markdown("### 🧾 Formatted Table Preview")
st.markdown(html_table, unsafe_allow_html=True)

# --- Clipboard Copy Button ---
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
components.html(copy_button_html, height=130)  # Display in sidebar
