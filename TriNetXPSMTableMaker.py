import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# Constants
DEFAULT_COLUMNS = [
    "Characteristic Name", "Characteristic ID", "Category",
    "Cohort 1 Before: Patient Count", "Cohort 1 Before: % of Cohort",
    "Cohort 1 Before: Mean", "Cohort 1 Before: SD",
    "Cohort 2 Before: Patient Count", "Cohort 2 Before: % of Cohort",
    "Cohort 2 Before: Mean", "Cohort 2 Before: SD",
    "Before: p-Value", "Before: Standardized Mean Difference",
    "Cohort 1 After: Patient Count", "Cohort 1 After: % of Cohort",
    "Cohort 1 After: Mean", "Cohort 1 After: SD",
    "Cohort 2 After: Patient Count", "Cohort 2 After: % of Cohort",
    "Cohort 2 After: Mean", "Cohort 2 After: SD",
    "After: p-Value", "After: Standardized Mean Difference"
]

def load_and_clean_csv(uploaded_file):
    df_raw = pd.read_csv(uploaded_file, header=None, skiprows=9)
    df_raw.columns = df_raw.iloc[0]
    return df_raw[1:].reset_index(drop=True)

def format_numeric_columns(df, decimals):
    for col in df.select_dtypes(include=['float', 'int']):
        df[col] = df[col].round(decimals)
    return df.fillna("")

def apply_pvalue_format(df):
    pvalue_cols = [col for col in df.columns if "p-Value" in col]
    for col in pvalue_cols:
        df[col] = df[col].apply(lambda x: "p<.001" if str(x).strip() == "0" else x)
    return df

def prepare_dataframe(df, selected_columns, rename_dict, decimal_places):
    df_trimmed = df[selected_columns].rename(columns=rename_dict)
    df_trimmed = format_numeric_columns(df_trimmed, decimal_places)
    df_trimmed = apply_pvalue_format(df_trimmed)
    return df_trimmed

def aggrid_editor(df, editable, groups):
    aggrid_df = df.copy()
    aggrid_df.insert(0, "Drag", "⇅")
    gb = GridOptionsBuilder.from_dataframe(aggrid_df)
    gb.configure_default_column(editable=editable, resizable=True)
    gb.configure_column("Drag", header_name="⇅ Drag to Reorder", rowDrag=True, pinned="left", editable=False, width=150)
    gb.configure_grid_options(rowDragManaged=True)
    group_row_style = JsCode("""
    function(params) {
        if (params.data && %s.includes(params.data['Characteristic Name'])) {
            return {'fontWeight':'bold','backgroundColor':'#e6e6e6','textAlign':'left'};
        }
    }""" % groups)
    gb.configure_grid_options(getRowStyle=group_row_style)
    grid_response = AgGrid(
        aggrid_df, gridOptions=gb.build(), update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True, allow_unsafe_jscode=True, height=500)
    return pd.DataFrame(grid_response["data"]).drop(columns=["Drag"], errors="ignore")

def generate_html_table(df, style_css):
    headers = "".join(f"<th>{col}</th>" for col in df.columns)
    rows = ""
    for _, row in df.iterrows():
        rows += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return f"{style_css}<table><tr>{headers}</tr>{rows}</table>"

def get_journal_css(font_size, h_align, v_align):
    return f"""
    <style>
    table {{border-collapse: collapse; width: 100%; font-size:{font_size}pt;}}
    th, td {{border: 1px solid #000; padding:6px; text-align:{h_align}; vertical-align:{v_align};}}
    th {{background:#f2f2f2;}}
    </style>
    """

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Novak's TriNetX Journal-Style Table Generator")

uploaded_file = st.file_uploader("Upload CSV", type="csv")
if not uploaded_file:
    st.stop()

df_data = load_and_clean_csv(uploaded_file)

# Sidebar UI
with st.sidebar.expander("Table Formatting", False):
    font_size = st.slider("Font Size", 6, 18, 10)
    h_align = st.selectbox("Horizontal Align", ["left", "center", "right"])
    v_align = st.selectbox("Vertical Align", ["top", "middle", "bottom"])
    decimal_places = st.slider("Decimals", 0, 5, 2)

selected_columns = st.sidebar.multiselect("Columns", df_data.columns, default=[c for c in DEFAULT_COLUMNS if c in df_data.columns])
rename_dict = {col: st.sidebar.text_input(f"Rename '{col}'", col) for col in selected_columns}

# Prepare DataFrame
df_trimmed = prepare_dataframe(df_data, selected_columns, rename_dict, decimal_places)

# Table editing
editable = st.sidebar.checkbox("Editable Table")
groups = ['Demographics', 'Conditions', 'Lab Values', 'Medications']
if editable:
    df_trimmed = aggrid_editor(df_trimmed, editable=True, groups=groups)

# Display HTML
html_table = generate_html_table(df_trimmed, get_journal_css(font_size, h_align, v_align))
st.markdown("### Formatted Table")
st.markdown(html_table, unsafe_allow_html=True)
