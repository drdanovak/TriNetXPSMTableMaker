import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

st.set_page_config(layout="wide")
st.title("📊 Novak's TriNetX Journal-Style Table Generator")

uploaded_file = st.file_uploader(
    "📂 Upload your TriNetX CSV file and turn it into a journal-ready table that you can copy and paste into a Word doc or poster. Made by Dr. Daniel Novak at UC Riverside School of Medicine, 2025.",
    type="csv"
)
if not uploaded_file:
    st.stop()

# Load and clean CSV
df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
df_raw.columns = df_raw.iloc[0]
df_data = df_raw[1:].reset_index(drop=True)
original_df = df_data.copy()

# === Sidebar Settings ===
st.sidebar.header("🛠️ Table Settings")
edit_toggle = st.sidebar.checkbox("✏️ Edit Table (with drag-and-drop)")
merge_duplicates = st.sidebar.checkbox("🔁 Merge duplicate row titles")
add_column_grouping = st.sidebar.checkbox("📌 Add Before/After PSM Column Separators (with headers)")
reset_table = st.sidebar.button("🔄 Reset Table to Default")

with st.sidebar.expander("🎛️ Display and Journal Formatting Options", expanded=False):
    font_size = st.slider("Font Size", 6, 18, 10)
    h_align = st.selectbox("Text Horizontal Alignment", ["left", "center", "right"])
    v_align = st.selectbox("Text Vertical Alignment", ["top", "middle", "bottom"])
    journal_style = st.selectbox("Journal Style", ["None", "NEJM", "AMA", "APA", "JAMA"])
    decimal_places = st.slider("Round numerical values to", 0, 5, 2)

with st.sidebar.expander("📋 Column Selection and Renaming", expanded=False):
    default_columns = [
        "Characteristic Name", "Characteristic ID", "Category",
        "Cohort 1 Before: Patient Count", "Cohort 1 Before: % of Cohort", "Cohort 1 Before: Mean", "Cohort 1 Before: SD",
        "Cohort 2 Before: Patient Count", "Cohort 2 Before: % of Cohort", "Cohort 2 Before: Mean", "Cohort 2 Before: SD",
        "Before: p-Value", "Before: Standardized Mean Difference",
        "Cohort 1 After: Patient Count", "Cohort 1 After: % of Cohort", "Cohort 1 After: Mean", "Cohort 1 After: SD",
        "Cohort 2 After: Patient Count", "Cohort 2 After: % of Cohort", "Cohort 2 After: Mean", "Cohort 2 After: SD",
        "After: p-Value", "After: Standardized Mean Difference"
    ]
    available_columns = list(df_data.columns)
    filtered_columns = [col for col in default_columns if col in available_columns]
    selected_columns = st.multiselect("Select columns to include", available_columns, default=filtered_columns)
    rename_dict = {col: st.text_input(f"Rename '{col}'", col, key=f"rename_{col}") for col in selected_columns}

with st.sidebar.expander("🧩 Preset Group Rows", expanded=False):
    preset_groups = ["Demographics", "Conditions", "Lab Values", "Medications"]
    custom_group_input = st.text_input("Add Custom Group Name")
    if custom_group_input:
        preset_groups.append(custom_group_input)
        preset_groups = list(dict.fromkeys(preset_groups))
    selected_groups = [label for label in preset_groups if st.checkbox(label, key=f"group_checkbox_{label}")]

# Table rendering
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
    .group-row td {{
        background-color: #e6e6e6;
        font-weight: bold;
        text-align: left;
    }}
    </style>
    """

def generate_html_table(df, journal_style, font_size, h_align, v_align):
    try:
        css = get_journal_css(journal_style, font_size, h_align, v_align)
        html = css + "<table>"
        if add_column_grouping and isinstance(df.columns, pd.MultiIndex):
            group_levels = df.columns.get_level_values(0)
            col_spans = []
            last = None
            span = 0
            for grp in group_levels:
                if grp == last:
                    span += 1
                else:
                    if last is not None:
                        col_spans.append((last, span))
                    last = grp
                    span = 1
            col_spans.append((last, span))
            group_row = "<tr>" + "".join([f"<th colspan='{span}'>{grp}</th>" for grp, span in col_spans]) + "</tr>"
            subheader_row = "<tr>" + "".join([f"<th>{sub}</th>" for sub in df.columns.get_level_values(1)]) + "</tr>"
            html += group_row + subheader_row
        else:
            html += "<tr>" + "".join([f"<th>{col}</th>" for col in df.columns]) + "</tr>"
        for _, row in df.iterrows():
            col_key = ('', 'Characteristic Name') if isinstance(df.columns, pd.MultiIndex) else 'Characteristic Name'
            char_name = str(row.get(col_key, '')).strip().lower()
            if char_name in [label.strip().lower() for label in selected_groups]:
                html += f"<tr class='group-row'><td colspan='{len(df.columns)}'>{row.get(col_key, '')}</td></tr>"
            else:
                html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row.values]) + "</tr>"
        html += "</table>"
        return html
    except Exception as e:
        st.error(f"Error generating HTML table: {e}")
        return ""
