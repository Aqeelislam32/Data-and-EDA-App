import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
from ydata_profiling import ProfileReport
import openpyxl
import base64







st.set_page_config(page_title = "EDA", 
                    page_icon = ":bar_chart:",
                    layout = "wide",
                    initial_sidebar_state= "expanded",
                    )

st.markdown(
    f"""
    <style>
    /* Main content area background */
    .stApp {{
        background-color: lightgray;
    }}
    /* Sidebar background */
    [data-testid="stSidebar"] {{
        background-color: skyblue;
    }}
    /* Buttons */
    .stButton>button {{
        background-color: orange;
        color: white; /* Ensure text is visible on orange */
        border: none; /* Remove default border */
        padding: 10px 20px; /* Add some padding */
        border-radius: 5px; /* Slightly rounded corners */
    }}
    .stButton>button:hover {{
        background-color: darkorange; /* Darker shade on hover */
        color: white;
    }}
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            </style>
            """,
    unsafe_allow_html=True
)
st.title(":red[EDA]")
st.text("A data analytics tool to make EDA simpler than ever!")









def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    filename = uploaded_file.name.split(".")[0]
    if filename.startswith("cleaned"):
        filename = filename.split("cleaned_")[1]
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download ="cleaned_{filename}.csv">Download csv file</a>'
    return href

def load_data():
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(
                uploaded_file, 
                na_values=[
                    'NULL', 'null', 'None', 'none', 'NaN', 'nan', '', ' '
                ], 
                keep_default_na=True
            )
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine = "openpyxl")
        elif uploaded_file.name.endswith('.pkl'):
            df = pd.read_pickle(uploaded_file)
        
        # Convert potential string-none values to actual NA
        df = df.replace(["None", "null", "NULL", "nan", "NaN", ""], pd.NA)
        return df

if not st.sidebar.checkbox("Begin the EDA-venture", label_visibility='visible'):
    st.session_state['df'] = None
    if st.button("What is EDA?"):
          st.info("  EDA stands for Exploratory Data Analysis \n- Exploration: EDA is about exploring data to understand it better\n- Patterns: It helps find patterns or trends in the data.\n- Questions: EDA helps ask and answer questions about the data.\n- Understanding: EDA helps gain a deeper understanding of the dataset before further analysis.\n- Detective work: It's like being a detective, looking for clues and insights in the data.\n ")
else:
    with st.expander("Upload a file"):
        uploaded_file = st.file_uploader("", type=["csv", "xlsx","pkl"])
        st.markdown("**Note:** Only .csv, .xlsx and .pkl files are supported.")
        if uploaded_file and ('df' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name):
            loaded_df = load_data()
            st.session_state['df'] = loaded_df
            st.session_state['df_original'] = loaded_df.copy() if loaded_df is not None else None
            st.session_state['last_uploaded'] = uploaded_file.name

df = st.session_state.get('df')

# Show persistent cleaning messages
if 'cleaning_msg' in st.session_state:
    st.success(st.session_state['cleaning_msg'])
    del st.session_state['cleaning_msg']


if df is not None:
    st.sidebar.header("Choose your task")
    task = st.sidebar.selectbox("", ["Data Exploration", "Data Cleaning", "Data Visualization", "Data Profiling"])
    if task == "Data Exploration":
        with st.expander(":Show Data"):
            st.dataframe(df)
        st.subheader("Visualise a column:")
        cols = ['None']
        cols.extend(df.columns)
        plot_col = st.selectbox("Select a column", cols)
        if plot_col != 'None':
            st.markdown(f":grey[**Plotting the distribution of : {plot_col}**]")
            st.altair_chart(alt.Chart(df).mark_bar().encode(
        x=alt.X(plot_col, bin=alt.Bin(maxbins=20)),
        y='count()'))
        else:
            st.markdown("**No column selected.**")
        if st.button('Display basic statistic'):
          st.write(df.describe())
    elif task == "Data Cleaning":
        choice = st.sidebar.radio("",["Feature Selection", "Filter Data"])
        if choice == "Feature Selection":
            # multiselect box to chose the columns to remove
            st.subheader("Feature Selection")
            with st.expander("Show correlation matrix"):
                st.info("How does correlation help in feature selection?\n- Features with high correlation are more linearly dependent.\n- Hence have almost the same effect on the dependent variable.\n- When two features have high correlation, we can drop one of the two features.")
                st.markdown("A __*correlation matrix*__ (for all applicable columns) has been provided for reference : ")
                try:
                    # Only select numeric columns to avoid string conversion errors
                    numeric_df = df.select_dtypes(include=['number'])
                    if not numeric_df.empty:
                        matrix = numeric_df.corr()
                        plt.figure(figsize=(16,12))
                        cmap = sns.diverging_palette(250, 15, s=75, l=40, n=9, center="light", as_cmap=True)
                        sns.heatmap(matrix, center=0, annot=True, fmt='.2f', square=True, cmap=cmap)
                        st.pyplot(plt)
                        plt.clf() # Clear figure after plotting
                    else:
                        st.warning("Is dataset mein correlation nikalne ke liye koi numeric columns nahi hain.")
                except Exception as e:
                    st.error(f"Correlation matrix error: {e}")

            cols = df.columns
            columns = list(cols)
            
            cols_to_use = st.multiselect(label = "Select the columns you wish to use for your analysis:", options = df.columns, default = columns)
            if st.button("Filter columns"):
                st.session_state['df'] = df[cols_to_use]
                st.session_state['cleaning_msg'] = "Columns filtered successfully!"
                st.rerun()
                
        elif choice == "Filter Data":
            st.subheader("Filter Data")
            st.markdown("__Note :__ Upload the cleaned dataset and proceed.")
            with st.expander("Show filtered data"):
                st.dataframe(df)
                
            missing_df = pd.DataFrame(df.isna().sum(),columns = ['Count of missing values'])
            with st.expander("Show missing values"):
                st.dataframe(missing_df)
                st.write("Total values in the dataframe:", df.shape[0])

            missing_df = missing_df[missing_df['Count of missing values'] > 0]
            cols = missing_df.index

            columns_missing = ['None']
            for col in cols.values:
                columns_missing.append(col)

            column_selected = st.selectbox("Select columns to filter", columns_missing)

            if column_selected != 'None':
                st.markdown(f"**Filtering the data for : {column_selected}**")
                task = st.radio("Do what with NaN values?",["Fill with mean", "Fill with median", "drop missing value"])
                if task == "Fill with mean":
                    try:
                        mean_val = pd.to_numeric(df[column_selected], errors='coerce').mean()
                        if pd.isna(mean_val):
                            st.error("This column is not numeric, so Mean imputation cannot be applied.")
                        else:
                            st.write(f"Mean value: {mean_val:.2f}")
                            if st.button("Apply Mean Imputation"):
                                st.session_state['df'][column_selected] = df[column_selected].fillna(mean_val)
                                st.session_state['cleaning_msg'] = f"✅ {column_selected} It has been successfully filled using the Mean value."
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

                elif task == "Fill with median":
                    try:
                        median_val = pd.to_numeric(df[column_selected], errors='coerce').median()
                        if pd.isna(median_val):
                            st.error("This column is not numeric, so Median imputation cannot be applied.")
                        else:
                            st.write(f"Median value: {median_val}")
                            if st.button("Apply Median Imputation"):
                                st.session_state['df'][column_selected] = df[column_selected].fillna(median_val)
                                st.session_state['cleaning_msg'] = f"✅ {column_selected} It has been successfully filled using the Medain value."
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

                elif task =="drop missing value":
                    if st.button("Drop Rows"):
                        st.session_state['df'] = df.dropna(subset=[column_selected])
                        st.session_state['cleaning_msg'] = f"✅ {column_selected} Missing values have been successfully removed."
                        st.rerun()

            elif column_selected == 'None':
                # the current dataframe
                st.markdown("### Current Processed Dataset:")
                st.dataframe(df)
                
                st.markdown("**No column selected for cleaning. If you have finished cleaning, you can download the updated file below:**")
                st.markdown(get_table_download_link(df), unsafe_allow_html=True)
            
    elif task == "Data Visualization":
        st.subheader("📊 Data Visualization")

        with st.expander("Show Data"):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Original Data**")
                st.dataframe(st.session_state.get('df_original'))
            with c2:
                st.write("**Updated Data**")
                st.dataframe(df)

        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Original Data Plots")
            if st.button("Generate Plots for Original Data"):
                with st.spinner("Generating plots for Original Data..."):
                    df_orig = st.session_state.get('df_original')
                    if df_orig is not None:
                        numeric_cols = df_orig.select_dtypes(include=['number'])
                        if not numeric_cols.empty:
                            fig, ax = plt.subplots(figsize=(20, 20))
                            numeric_cols.hist(bins=30, ax=ax)
                            plt.tight_layout()
                            st.pyplot(fig)
                            st.balloons()
                        else:
                            st.warning("No numeric columns available in original data.")

        with col2:
            st.write("### Updated Data Plots")
            if st.button("Generate Plots for Updated Data"):
                if df is not None:
                    with st.spinner("Generating plots for Updated Data..."):
                        numeric_cols = df.select_dtypes(include=['number'])
                        if not numeric_cols.empty:
                            fig, ax = plt.subplots(figsize=(20, 20))
                            numeric_cols.hist(bins=30, ax=ax)
                            plt.tight_layout()
                            st.pyplot(fig)
                            st.balloons()
                        else:
                            st.warning("No numeric columns available in updated data.")

    elif task == "Data Profiling":
        st.subheader("📝 Data Profiling")
        
        with st.expander("Show Data"):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Original Data**")
                st.dataframe(st.session_state.get('df_original'))
            with c2:
                st.write("**Updated Data**")
                st.dataframe(df)

        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Original Data Profile")
            if st.button("Generate Report for Original Data"):
                df_orig = st.session_state.get('df_original')
                if df_orig is not None:
                    with st.spinner("Creating Profile for Original Data..."):
                        profile = ProfileReport(df_orig, title="Original Data Profile", explorative=True)
                        filename = "original_data_profile.html"
                        profile.to_file(output_file=filename)
                        st.success("Original Data Profile Generated!")
                        with open(filename, "rb") as file:
                            st.download_button(label="Download Original Profile", data=file, file_name=filename, mime="text/html")

        with col2:
            st.write("### Updated Data Profile")
            if st.button("Generate Report for Updated Data"):
                if df is not None:
                    with st.spinner("Creating Profile for Updated Data..."):
                        profile = ProfileReport(df, title="Updated Data Profile", explorative=True)
                        filename = "updated_data_profile.html"
                        profile.to_file(output_file=filename)
                        st.success("Updated Data Profile Generated!")
                        with open(filename, "rb") as file:
                            st.download_button(label="Download Updated Profile", data=file, file_name=filename, mime="text/html")
