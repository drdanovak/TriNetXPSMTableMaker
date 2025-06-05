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
        df_trimmed[col] = pd.to_numeric(df_trimmed[col], errors='coerce').round(decimal_places)
    except Exception as e:
        st.warning(f"Could not convert column {col} to numeric: {e}")
    except:
        pass

for col in df_trimmed.columns:
    if "p-Value" in col:
        df_trimmed[col] = df_trimmed[col].apply(lambda x: "p<.001" if str(x).strip() == "0" else x)

# Preset grouping checkboxes
preset_groups = ["Demographics", "Conditions", "Lab Values", "Medications"]
st.sidebar.subheader("🧩 Preset Group Rows")
custom_group_input = st.sidebar.text_input("Add Custom Group Name")
if custom_group_input:
    preset_groups.append(custom_group_input)
    preset_groups = list(dict.fromkeys(preset_groups))  # remove duplicates while preserving order

selected_groups = []
for label in preset_groups:
    if st.sidebar.checkbox(label, key=f"group_checkbox_{label}"):
        selected_groups.append(label)



if selected_groups:
    # Preserve original row order and insert group rows only for newly checked items
    current_rows = df_trimmed.to_dict("records")
    rebuilt_rows = []
    i = 0
    while i < len(current_rows):
        row = current_rows[i]
        name = str(row["Characteristic Name"]).strip()
        if name in selected_groups:
            rebuilt_rows.append(row)  # already a group row
            i += 1
        elif name in preset_groups:
            i += 1  # skip old group rows that are not selected
        else:
            rebuilt_rows.append(row)
            i += 1
    for group in selected_groups:
        if not any(str(row["Characteristic Name"]).strip() == group for row in rebuilt_rows):
            group_row = {col: "" for col in df_trimmed.columns}
            group_row["Characteristic Name"] = group
            rebuilt_rows.insert(0, group_row)  # add new group rows at the top by default
    df_trimmed = pd.DataFrame(rebuilt_rows)

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
        before_cols = [col for col in col_names if 'Before' in col and 'After' not in col]
        after_cols = [col for col in col_names if 'After' in col]
        first_cols = [col for col in col_names if col not in before_cols + after_cols]

        new_order = first_cols + before_cols + after_cols
        df_trimmed = df_trimmed[new_order]

        grouped_labels = ([''] * len(first_cols) +
                          ['Before Propensity Score Matching'] * len(before_cols) +
                          ['After Propensity Score Matching'] * len(after_cols))
        df_trimmed.columns = pd.MultiIndex.from_tuples(zip(grouped_labels, df_trimmed.columns))
    except Exception as e:
        st.error(f"Error applying column grouping headers: {e}")
    except Exception as e:
        st.error(f"Error applying column grouping headers: {e}")

if reset_table:
    df_trimmed = original_df[filtered_columns].copy()

# Editable table
if edit_toggle:
    st.subheader("📋 Editable Table")

    # Flatten df_trimmed if needed for AgGrid compatibility
    aggrid_df = df_trimmed.copy()
    if isinstance(aggrid_df.columns, pd.MultiIndex):
        aggrid_df.columns = [' '.join(col).strip() for col in aggrid_df.columns]

    aggrid_df.insert(0, "Drag", "⇅")
    gb = GridOptionsBuilder.from_dataframe(aggrid_df)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_column("Drag", header_name="⇅ Drag to Reorder (Click Lock to Confirm)", rowDrag=True, pinned="left", editable=False, width=250)
    gb.configure_grid_options(rowDragManaged=True, animateRows=True)

    group_row_style = JsCode("""
    function(params) {
        if (params.data && ['Demographics', 'Conditions', 'Lab Values', 'Medications'].includes(params.data['Characteristic Name'] && params.data['Characteristic Name'].toString().trim())) {
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
        aggrid_df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        height=500,
        reload_data=True
    )
    updated_df = pd.DataFrame(grid_response["data"]).drop(columns=["Drag"], errors="ignore")

    # Manual refresh toggle button
    st.markdown("### 🔁 Refresh Formatted Preview")
    st.session_state["refresh_preview"] = st.button("🔄 Update Preview Table Now")

    # Restore multi-index column structure if grouping was applied
    if add_column_grouping:
        try:
            col_names = list(updated_df.columns)
            before_cols = [col for col in col_names if 'Before' in col and 'After' not in col]
            after_cols = [col for col in col_names if 'After' in col]
            first_cols = [col for col in col_names if col not in before_cols + after_cols]

            new_order = first_cols + before_cols + after_cols
            updated_df = updated_df[new_order]

            grouped_labels = ([''] * len(first_cols) +
                              ['Before Propensity Score Matching'] * len(before_cols) +
                              ['After Propensity Score Matching'] * len(after_cols))
            updated_df.columns = pd.MultiIndex.from_tuples(zip(grouped_labels, updated_df.columns))
        except Exception as e:
            st.error(f"Error restoring column groups after edit: {e}")

    df_trimmed = updated_df



# Final preview (always updated)
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
        if isinstance(df.columns, pd.MultiIndex):
            col_key = ('', 'Characteristic Name')
        else:
            col_key = 'Characteristic Name'

        char_name = str(row.get(col_key, '')).strip().lower()
        if char_name in [label.strip().lower() for label in selected_groups]:
            html += f"<tr class='group-row'><td colspan='{len(df.columns)}'>{row.get(col_key, '')}</td></tr>"
        else:
            
            html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row.values]) + "</tr>"
    html += "</table>"
    return html

html_table = ""
if st.session_state.get("refresh_preview", True):
    html_table = generate_html_table(df_trimmed, journal_style, font_size, h_align, v_align)

copy_button_html = f'''
<div id="copy-container">
  <div id="copySource" contenteditable="true" style="position: absolute; left: -9999px;">
    {html_table}
  </div>
  <button onclick="copyTableToClipboard()" style="padding:6px 12px; font-size:14px;">📋 Copy Table to Clipboard</button>
  <button onclick="copyToWord()" style="padding:6px 12px; font-size:14px; margin-left: 10px;">📄 Copy Table for Word</button>
</div>
'''

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
st.markdown("### 🧾 Formatted Table Preview")
st.markdown(html_table, unsafe_allow_html=True)



st.markdown(copy_script, unsafe_allow_html=True)







st.markdown(copy_button_html, unsafe_allow_html=True)
