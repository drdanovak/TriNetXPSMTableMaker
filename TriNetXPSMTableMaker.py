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
add_column_grouping = st.sidebar.checkbox("📌 Add Before/After PSM Column Separators")
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

# Preset grouping checkboxes
st.sidebar.subheader("🧩 Preset Group Rows")
preset_groups = ["Demographics", "Conditions", "Lab Values", "Medications"]
group_labels = []
grouped_rows = []

for label in preset_groups:
    if st.sidebar.checkbox(label):
        group_row = pd.Series([label] + ["" for _ in range(len(df_trimmed.columns) - 1)], index=df_trimmed.columns)
        group_row["Characteristic Name"] = label
        grouped_rows.append(group_row)

if grouped_rows:
    df_trimmed = pd.concat([pd.DataFrame(grouped_rows), df_trimmed], ignore_index=True)

if merge_duplicates:
    for merge_col in [col for col in df_trimmed.columns if col.strip() in ["Characteristic ID", "Characteristic Name"]]:
        prev = None
        new_col = []
        for val in df_trimmed[merge_col]:
            if val == prev:
                new_col.append("")
            else:
                new_col.append(val)
                prev = val
        df_trimmed[merge_col] = new_col

if add_column_grouping:
    try:
        col_names = list(df_trimmed.columns)
        grouped_cols = col_names[:3] + ["Before Propensity Score Matching"] * 7 + ["After Propensity Score Matching"] * 7
        if len(grouped_cols) == len(col_names):
            df_trimmed.columns = grouped_cols
    except Exception as e:
        st.error(f"Error applying column grouping: {e}")

if reset_table:
    df_trimmed = original_df[filtered_columns].copy()

# Editable table
if edit_toggle:
    st.subheader("📋 Editable Table")
    df_trimmed.insert(0, "Drag", "⇅")
    gb = GridOptionsBuilder.from_dataframe(df_trimmed)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_column("Drag", header_name="", rowDrag=True, pinned="left", editable=False, width=50)
    gb.configure_grid_options(rowDragManaged=True, animateRows=True)

    group_row_style = JsCode("""
    function(params) {
        if (params.data && ['Demographics', 'Conditions', 'Lab Values', 'Medications'].includes(params.data['Characteristic Name'])) {
            return {
                'fontWeight': 'bold',
                'backgroundColor': '#e6e6e6',
                'textAlign': 'left'
            }
        }
    }
    """)
    gb.configure_grid_options(getRowStyle=group_row_style)

    gridOptions = gb.build()
    grid_response = AgGrid(
        df_trimmed,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        height=500,
        reload_data=True
    )
    df_trimmed = pd.DataFrame(grid_response["data"]).drop(columns=["Drag"], errors="ignore")

    # Refresh table preview after edits
    html_table = generate_html_table(df_trimmed, journal_style, font_size, h_align, v_align)
    st.markdown("### 🧾 Formatted Table Preview")
    st.markdown(html_table, unsafe_allow_html=True)
else:
    html_table = generate_html_table(df_trimmed, journal_style, font_size, h_align, v_align)
    st.markdown("### 🧾 Formatted Table Preview")
    st.markdown(html_table, unsafe_allow_html=True)

copy_button_html = f"""
<div id="copy-container">
  <div id="copySource" contenteditable="true" style="position: absolute; left: -9999px;">
    {html_table}
  </div>
  <button onclick="copyTableToClipboard()" style="padding:6px 12px; font-size:14px;">📋 Copy Table to Clipboard</button>
</div>
<script>
function copyTableToClipboard() {{
  const range = document.createRange();
  const copySource = document.getElementById("copySource");
  range.selectNodeContents(copySource);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand("copy");
  sel.removeAllRanges();
  alert("✅ Table copied to clipboard!");
}}
</script>
"""

st.sidebar.subheader("📎 Copy Table to Clipboard")
components.html(copy_button_html, height=130)
