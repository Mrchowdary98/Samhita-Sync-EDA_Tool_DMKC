import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from scipy import stats
from sklearn.preprocessing import LabelEncoder
import io
import base64

warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Samhita Sync",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .info-box {
    background-color: #ffffff;
    padding: 1.5rem;
    border-left: 5px solid #004080; /* deep blue */
    margin: 1.5rem 0;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07);
    font-family: 'Segoe UI', sans-serif;
    transition: transform 0.2s ease;
}

.info-box:hover {
    transform: scale(1.01);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.info-box h4,p {
    font-size: 1.7rem;
    margin: 0 0 0.5rem 0;
    color: #004080;
    font-weight: 600;
}

.info-box strong {
    color: #e67e22; /* orange highlight */
}

</style>
""", unsafe_allow_html=True)

def load_data(file):
    """Load and decode file content based on its extension"""
    try:
        file_name = file.name
        file_content = file.read()
        file_extension = file_name.lower().split('.')[-1]

        file_obj = io.BytesIO(file_content)

        if file_extension == 'csv':
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for enc in encodings:
                try:
                    file_obj.seek(0)
                    df = pd.read_csv(file_obj, encoding=enc, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("CSV decoding failed with all known encodings.")

        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')

        elif file_extension == 'json':
            df = pd.read_json(file_obj)

        elif file_extension == 'parquet':
            df = pd.read_parquet(file_obj)

        elif file_extension == 'tsv':
            df = pd.read_csv(file_obj, sep='\t', low_memory=False)

        elif file_extension == 'txt':
            file_obj.seek(0)
            sample = file_obj.read(1024).decode('utf-8', errors='ignore')
            file_obj.seek(0)

            if '\t' in sample:
                df = pd.read_csv(file_obj, sep='\t', low_memory=False)
            elif ';' in sample:
                df = pd.read_csv(file_obj, sep=';', low_memory=False)
            elif '|' in sample:
                df = pd.read_csv(file_obj, sep='|', low_memory=False)
            else:
                df = pd.read_csv(file_obj, low_memory=False)

        elif file_extension in ['db', 'sqlite']:
            st.error("SQLite files not supported directly. Please export tables to CSV.")
            return None

        elif file_extension == 'pkl':
            df = pd.read_pickle(file_obj)

        else:
            st.error(f"Unsupported file format: .{file_extension}")
            st.info("Supported formats: CSV, TSV, TXT, Excel, JSON, Parquet, Pickle")
            return None

        # Optional: optimize memory usage if needed
        if 'optimize_memory_usage' in globals():
            df = optimize_memory_usage(df)

        return df

    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def optimize_memory_usage(df):
    """Downcast numeric columns to reduce memory"""
    for col in df.select_dtypes(include=['float']):
        df[col] = pd.to_numeric(df[col], downcast='float')
    for col in df.select_dtypes(include=['int']):
        df[col] = pd.to_numeric(df[col], downcast='integer')
    for col in df.select_dtypes(include=['object']):
        num_unique = df[col].nunique()
        num_total = len(df[col])
        if num_unique / num_total < 0.5:
            df[col] = df[col].astype('category')
    return df



def basic_info(df):
    """Display basic information about the dataset"""
    st.markdown('<div class="section-header">📋 Dataset Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Rows", f"{df.shape[0]:,}")
    with col2:
        st.metric("Columns", f"{df.shape[1]:,}")
    with col3:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    with col4:
        st.metric("Duplicate Rows", f"{df.duplicated().sum():,}")
    
    # Dataset info
    st.markdown('<div class="section-header">📊 Column Information</div>', unsafe_allow_html=True)
    
    col_info = []
    for col in df.columns:
        col_info.append({
            'Column': col,
            'Data Type': str(df[col].dtype),
            'Non-Null Count': df[col].count(),
            'Null Count': df[col].isnull().sum(),
            'Null %': f"{(df[col].isnull().sum() / len(df)) * 100:.2f}%",
            'Unique Values': df[col].nunique(),
            'Memory (KB)': f"{df[col].memory_usage(deep=True) / 1024:.2f}"
        })
    
    info_df = pd.DataFrame(col_info)
    st.dataframe(info_df, use_container_width=True)

def data_quality_assessment(df):
    """Assess data quality issues"""
    st.markdown('<div class="section-header">🔍 Data Quality Assessment</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Missing Values Analysis")
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df)) * 100
        
        if missing_data.sum() > 0:
            missing_df = pd.DataFrame({
                'Column': missing_data.index,
                'Missing Count': missing_data.values,
                'Missing %': missing_percent.values
            }).sort_values('Missing Count', ascending=False)
            
            missing_df = missing_df[missing_df['Missing Count'] > 0]
            st.dataframe(missing_df, use_container_width=True)
            
            # Missing values heatmap
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(df.isnull(), cbar=True, ax=ax, cmap='viridis')
            plt.title('Missing Values Heatmap')
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.success("No missing values found!")
    
    with col2:
        st.subheader("Data Quality Issues")
        
        issues = []
        
        # Check for duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"🔴 {duplicates:,} duplicate rows found")
        
        # Check for constant columns
        constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
        if constant_cols:
            issues.append(f"🟡 {len(constant_cols)} constant columns: {', '.join(constant_cols)}")
        
        # Check for high cardinality categorical columns
        high_card_cols = []
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() > len(df) * 0.5:
                high_card_cols.append(col)
        if high_card_cols:
            issues.append(f"🟡 High cardinality columns: {', '.join(high_card_cols)}")
        
        # Check for potential outliers in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_cols = []
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)][col]
            if len(outliers) > 0:
                outlier_cols.append(f"{col} ({len(outliers)} outliers)")
        
        if outlier_cols:
            issues.append("🟡 Columns with outliers: ")
            issues.append(f"\n {', '.join(outlier_cols[:3])}{'...' if len(outlier_cols) > 3 else ''}")
        
        if not issues:
            st.success("No major data quality issues detected!")
        else:
            for issue in issues:
                st.write(issue)

def feature_engineering(df):
    st.subheader("")
    st.markdown('<div class="section-header">🛠️ Feature Engineering</div>', unsafe_allow_html=True)

    # Initialize session state copy of df
    if 'engineered_df' not in st.session_state:
        st.session_state['engineered_df'] = df.copy()

    new_df = st.session_state['engineered_df']
    
    numeric_cols = new_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = new_df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = new_df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()

    feature_type = st.selectbox(
        "Select feature engineering type:",
        ["Numerical Transformations", "Categorical Encoding", "DateTime Features", "Binning"]
    )

    # 1️⃣ Numerical Transformations
    if feature_type == "Numerical Transformations" and numeric_cols:
        selected_col = st.selectbox("Select numeric column:", numeric_cols, key="num_col")
        transformation = st.selectbox("Transformation:", ["Log", "Square Root", "Standardization", "Normalization"], key="num_transform")

        if st.button("Apply Numeric Transformation"):
            try:
                col_data = new_df[selected_col].dropna()
                if transformation == "Log":
                    if (col_data > 0).all():
                        new_df[selected_col + "_log"] = np.log(new_df[selected_col])
                        st.success(f"Added: {selected_col}_log")
                    else:
                        st.error("Log requires all values > 0")
                elif transformation == "Square Root":
                    if (col_data >= 0).all():
                        new_df[selected_col + "_sqrt"] = np.sqrt(new_df[selected_col])
                        st.success(f"Added: {selected_col}_sqrt")
                    else:
                        st.error("Square Root requires values ≥ 0")
                elif transformation == "Standardization":
                    new_df[selected_col + "_zscore"] = (new_df[selected_col] - new_df[selected_col].mean()) / new_df[selected_col].std()
                    st.success(f"Added: {selected_col}_zscore")
                else:
                    new_df[selected_col + "_norm"] = (new_df[selected_col] - new_df[selected_col].min()) / (new_df[selected_col].max() - new_df[selected_col].min())
                    st.success(f"Added: {selected_col}_norm")
            except Exception as e:
                st.error(f"Error: {e}")

    # 2️⃣ Categorical Encoding
    elif feature_type == "Categorical Encoding" and categorical_cols:
        selected_col = st.selectbox("Select categorical column:", categorical_cols, key="cat_col")
        encoding_type = st.selectbox("Encoding Type:", ["Label Encoding", "One-Hot Encoding", "Frequency Encoding"], key="enc_type")

        if st.button("Apply Encoding"):
            try:
                if encoding_type == "Label Encoding":
                    le = LabelEncoder()
                    new_df[selected_col + "_label"] = le.fit_transform(new_df[selected_col].astype(str))
                    st.success(f"Added: {selected_col}_label")
                elif encoding_type == "One-Hot Encoding":
                    dummies = pd.get_dummies(new_df[selected_col], prefix=selected_col)
                    new_df = pd.concat([new_df, dummies], axis=1)
                    st.session_state['engineered_df'] = new_df  # update since concat returns new df
                    st.success(f"Added {dummies.shape[1]} One-Hot columns")
                else:
                    freq_map = new_df[selected_col].value_counts().to_dict()
                    new_df[selected_col + "_freq"] = new_df[selected_col].map(freq_map)
                    st.success(f"Added: {selected_col}_freq")
            except Exception as e:
                st.error(f"Error: {e}")

    # 3️⃣ DateTime Feature Extraction
    elif feature_type == "DateTime Features" and datetime_cols:
        selected_col = st.selectbox("Select datetime column:", datetime_cols, key="dt_col")
        features = st.multiselect("Select features:", ["Year", "Month", "Day", "Hour", "Quarter", "Day of Week", "Is Weekend"], key="dt_features")

        if st.button("Extract DateTime Features"):
            try:
                for f in features:
                    if f == "Year":
                        new_df[selected_col + "_year"] = new_df[selected_col].dt.year
                    elif f == "Month":
                        new_df[selected_col + "_month"] = new_df[selected_col].dt.month
                    elif f == "Day":
                        new_df[selected_col + "_day"] = new_df[selected_col].dt.day
                    elif f == "Hour":
                        new_df[selected_col + "_hour"] = new_df[selected_col].dt.hour
                    elif f == "Quarter":
                        new_df[selected_col + "_quarter"] = new_df[selected_col].dt.quarter
                    elif f == "Day of Week":
                        new_df[selected_col + "_dow"] = new_df[selected_col].dt.dayofweek
                    elif f == "Is Weekend":
                        new_df[selected_col + "_is_weekend"] = new_df[selected_col].dt.dayofweek >= 5
                st.success(f"Extracted {len(features)} features from {selected_col}")
            except Exception as e:
                st.error(f"Error: {e}")

    # 4️⃣ Binning
    elif feature_type == "Binning" and numeric_cols:
        selected_col = st.selectbox("Select column for binning:", numeric_cols, key="bin_col")
        method = st.selectbox("Binning Method:", ["Equal Width", "Equal Frequency"], key="bin_method")
        bins = st.slider("Number of bins:", min_value=2, max_value=20, value=5, key="bin_count")

        if st.button("Apply Binning"):
            try:
                if method == "Equal Width":
                    new_df[selected_col + "_bin"] = pd.cut(new_df[selected_col], bins=bins, labels=False)
                else:
                    new_df[selected_col + "_bin"] = pd.qcut(new_df[selected_col], q=bins, labels=False, duplicates='drop')
                st.success(f"Binned column added: {selected_col}_bin")
            except Exception as e:
                st.error(f"Error: {e}")
    
     # 🧹 Column drop section
    st.markdown("### 🧹 Drop Unwanted Columns")
    cols_to_drop = st.multiselect(
        "Select columns to drop from the final dataset:",
        options=st.session_state['engineered_df'].columns.tolist()
    )
    if cols_to_drop:
        if st.button("Delete Selected Columns"):
            st.session_state['engineered_df'].drop(columns=cols_to_drop, inplace=True)
            st.success(f"Dropped columns: {', '.join(cols_to_drop)}")


    # ✅ Show preview after all operations
    st.markdown("### 👁️ Preview Transformed Data (First 5 Rows)")
    st.dataframe(st.session_state['engineered_df'].head(), use_container_width=True)


    # ✅ Download Button
    st.markdown("### 📥 Download Transformed Dataset")
    csv = st.session_state['engineered_df'].to_csv(index=False)
    st.download_button("Download CSV", csv, "engineered_dataset.csv", mime="text/csv")


def time_series_analysis(df):
    """Time series analysis for datetime columns"""
    st.subheader("Time Series Analysis")
    
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if not datetime_cols:
        st.warning("No datetime columns found in the dataset.")
        return
    
    selected_date_col = st.selectbox("Select datetime column:", datetime_cols)
    
    if selected_date_col:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_value_col = st.selectbox("Select value column:", numeric_cols)
            
            if selected_value_col:
                # Prepare time series data
                ts_data = df[[selected_date_col, selected_value_col]].copy()
                ts_data = ts_data.dropna()
                ts_data = ts_data.sort_values(selected_date_col)
                
                # Time series plot
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(ts_data[selected_date_col], ts_data[selected_value_col])
                ax.set_xlabel(selected_date_col)
                ax.set_ylabel(selected_value_col)
                ax.set_title(f'Time Series: {selected_value_col} over {selected_date_col}')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
                # Basic time series statistics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Time Series Statistics:**")
                    st.write(f"- Start Date: {ts_data[selected_date_col].min()}")
                    st.write(f"- End Date: {ts_data[selected_date_col].max()}")
                    st.write(f"- Duration: {(ts_data[selected_date_col].max() - ts_data[selected_date_col].min()).days} days")
                    st.write(f"- Data Points: {len(ts_data)}")
                
                with col2:
                    st.write("**Value Statistics:**")
                    st.write(f"- Mean: {ts_data[selected_value_col].mean():.3f}")
                    st.write(f"- Std Dev: {ts_data[selected_value_col].std():.3f}")
                    st.write(f"- Min: {ts_data[selected_value_col].min():.3f}")
                    st.write(f"- Max: {ts_data[selected_value_col].max():.3f}")


@st.cache_data
def get_statistical_summary(df):
    """Get statistical summary - cached and optimized"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    summaries = {}
    
    if numeric_cols:
        summaries['numeric'] = df[numeric_cols].describe()
        
        # Additional statistics - vectorized
        additional_stats = []
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                additional_stats.append({
                    'Variable': col,
                    'Skewness': f"{col_data.skew():.3f}",
                    'Kurtosis': f"{col_data.kurtosis():.3f}",
                    'Variance': f"{col_data.var():.3f}",
                    'Coefficient of Variation': f"{(col_data.std() / col_data.mean()):.3f}" if col_data.mean() != 0 else "N/A",
                    'Range': f"{col_data.max() - col_data.min():.3f}"
                })
        summaries['additional_numeric'] = additional_stats
    
    if categorical_cols:
        cat_summary = []
        for col in categorical_cols[:20]:  # Limit for performance
            value_counts = df[col].value_counts()
            if len(value_counts) > 0:
                cat_summary.append({
                    'Variable': col,
                    'Unique Values': df[col].nunique(),
                    'Most Frequent': value_counts.index[0],
                    'Frequency of Most Common': value_counts.iloc[0],
                    'Least Frequent': value_counts.index[-1] if len(value_counts) > 1 else value_counts.index[0],
                    'Entropy': f"{stats.entropy(value_counts.values):.3f}" if len(value_counts) > 1 else "0.000"
                })
        summaries['categorical'] = cat_summary
    
    if datetime_cols:
        dt_summary = []
        for col in datetime_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                dt_summary.append({
                    'Variable': col,
                    'Min Date': col_data.min(),
                    'Max Date': col_data.max(),
                    'Date Range (Days)': (col_data.max() - col_data.min()).days
                })
        summaries['datetime'] = dt_summary
    
    return summaries

def statistical_summary(df):
    """Display statistical summary - optimized"""
    st.markdown('<div class="section-header">📈 Statistical Summary</div>', unsafe_allow_html=True)
    
    with st.spinner('Computing statistical summary...'):
        summaries = get_statistical_summary(df)
    
    if 'numeric' in summaries:
        st.subheader("Numerical Variables Summary")
        st.dataframe(summaries['numeric'], use_container_width=True)
        
        if 'additional_numeric' in summaries:
            st.subheader("Additional Statistical Measures")
            additional_df = pd.DataFrame(summaries['additional_numeric'])
            st.dataframe(additional_df, use_container_width=True)
    
    if 'categorical' in summaries:
        st.subheader("Categorical Variables Summary")
        cat_df = pd.DataFrame(summaries['categorical'])
        st.dataframe(cat_df, use_container_width=True)
    
    if 'datetime' in summaries:
        st.subheader("DateTime Variables Summary")
        dt_df = pd.DataFrame(summaries['datetime'])
        st.dataframe(dt_df, use_container_width=True)


def statistical_tests(df):
    """Statistical tests for various hypotheses"""
    
    st.markdown('<div class="section-header">📈 Statistical Tests</div>', unsafe_allow_html=True)

    test_type = st.selectbox(
        "Select statistical test:",
        ["Normality Test", "T-Test", "Chi-Square Test", "Correlation Test"]
    )

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # 1️⃣ Normality Test
    if test_type == "Normality Test" and numeric_cols:
        selected_col = st.selectbox("Select column for normality test:", numeric_cols)

        if selected_col and st.button("Run Normality Test"):
            col_data = df[selected_col].dropna()

            if len(col_data) >= 3:
                shapiro_stat, shapiro_p = stats.shapiro(col_data.sample(min(5000, len(col_data))))
                ks_stat, ks_p = stats.kstest(col_data, 'norm', args=(col_data.mean(), col_data.std()))

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Shapiro-Wilk Test:**")
                    st.write(f"- Statistic: {shapiro_stat:.4f}")
                    st.write(f"- P-value: {shapiro_p:.4f}")
                    st.write(f"- Normal: {'Yes' if shapiro_p > 0.05 else 'No'}")

                with col2:
                    st.write("**Kolmogorov-Smirnov Test:**")
                    st.write(f"- Statistic: {ks_stat:.4f}")
                    st.write(f"- P-value: {ks_p:.4f}")
                    st.write(f"- Normal: {'Yes' if ks_p > 0.05 else 'No'}")

                fig, ax = plt.subplots(figsize=(8, 6))
                stats.probplot(col_data, dist="norm", plot=ax)
                ax.set_title(f'Q-Q Plot for {selected_col}')
                st.pyplot(fig)
                plt.close()

    # 2️⃣ T-Test
    elif test_type == "T-Test" and numeric_cols and categorical_cols:
        st.write("**Independent T-Test (Numeric by Categorical):**")
        numeric_col = st.selectbox("Select numeric column:", numeric_cols, key="ttest_num")
        categorical_col = st.selectbox("Select categorical column:", categorical_cols, key="ttest_cat")

        if numeric_col and categorical_col and st.button("Run T-Test"):
            categories = df[categorical_col].dropna().unique()

            if len(categories) == 2:
                group1 = df[df[categorical_col] == categories[0]][numeric_col].dropna()
                group2 = df[df[categorical_col] == categories[1]][numeric_col].dropna()

                if len(group1) > 0 and len(group2) > 0:
                    t_stat, p_value = stats.ttest_ind(group1, group2)

                    st.write(f"**T-Test Results:**")
                    st.write(f"- T-statistic: {t_stat:.4f}")
                    st.write(f"- P-value: {p_value:.4f}")
                    st.write(f"- Significant difference: {'Yes' if p_value < 0.05 else 'No'}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Group: {categories[0]}**")
                        st.write(f"- Count: {len(group1)}")
                        st.write(f"- Mean: {group1.mean():.3f}")
                        st.write(f"- Std: {group1.std():.3f}")
                    with col2:
                        st.write(f"**Group: {categories[1]}**")
                        st.write(f"- Count: {len(group2)}")
                        st.write(f"- Mean: {group2.mean():.3f}")
                        st.write(f"- Std: {group2.std():.3f}")
                else:
                    st.error("One or both groups have no data")
            else:
                st.warning("T-Test requires exactly 2 categories.")

    # 3️⃣ Chi-Square Test
    elif test_type == "Chi-Square Test" and len(categorical_cols) >= 2:
        cat1 = st.selectbox("Select first categorical column:", categorical_cols, key="chi1")
        other_cats = [col for col in categorical_cols if col != cat1]

        if other_cats:
            cat2 = st.selectbox("Select second categorical column:", other_cats, key="chi2")

            if st.button("Run Chi-Square Test"):
                contingency = pd.crosstab(df[cat1], df[cat2])
                if contingency.shape[0] > 1 and contingency.shape[1] > 1:
                    chi2, p, dof, expected = stats.chi2_contingency(contingency)

                    st.write("**Chi-Square Test Results:**")
                    st.write(f"- Chi-square Statistic: {chi2:.4f}")
                    st.write(f"- Degrees of Freedom: {dof}")
                    st.write(f"- P-value: {p:.4f}")
                    st.write(f"- Associated: {'Yes' if p < 0.05 else 'No'}")

                    st.write("Contingency Table:")
                    st.dataframe(contingency)
                else:
                    st.warning("Contingency table is too small to perform the test.")
        else:
            st.warning("Need at least two different categorical columns.")

    # 4️⃣ Correlation Test
    elif test_type == "Correlation Test" and len(numeric_cols) >= 2:
        col1 = st.selectbox("Select first numeric column:", numeric_cols, key="corr1")
        other_nums = [c for c in numeric_cols if c != col1]

        if other_nums:
            col2 = st.selectbox("Select second numeric column:", other_nums, key="corr2")

            if st.button("Run Correlation Test"):
                col1_data = df[col1].dropna()
                col2_data = df[col2].dropna()

                if len(col1_data) > 2 and len(col2_data) > 2:
                    corr_coef, p_corr = stats.pearsonr(col1_data, col2_data)

                    st.write("**Correlation Test Results:**")
                    st.write(f"- Correlation Coefficient: {corr_coef:.4f}")
                    st.write(f"- P-value: {p_corr:.4f}")
                    st.write(f"- Significant: {'Yes' if p_corr < 0.05 else 'No'}")

                    # Calculate correlation matrix
                    corr_matrix = df[numeric_cols].corr()

                    st.write("**Correlation Matrix:**")
                    st.dataframe(corr_matrix.round(2), use_container_width=True)

                    # Heatmap using seaborn
                    left, center, right = st.columns([1, 2, 1])
                    fig, ax = plt.subplots(figsize=(8, 4))
                    sns.heatmap(corr_matrix, annot=True, cmap='RdPu', fmt=".2f", center=0)
                    ax.set_title("Correlation Heatmap", fontsize=12)
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.warning("Not enough data in selected columns.")
        else:
            st.warning("No second numeric column available for correlation test.")


def create_visualizations(df):
    """Create various visualizations"""
    st.markdown('<div class="section-header">📊 Data Visualizations</div>', unsafe_allow_html=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Correlation Analysis
    if len(numeric_cols) > 1:
        st.subheader("Correlation Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Correlation heatmap
            fig, ax = plt.subplots(figsize=(10, 8))
            correlation_matrix = df[numeric_cols].corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, ax=ax, fmt='.2f')
            plt.title('Correlation Heatmap')
            st.pyplot(fig)
        
        with col2:
            # High correlations
            st.write("**High Correlations (|r| > 0.7):**")
            high_corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        high_corr_pairs.append({
                            'Variable 1': correlation_matrix.columns[i],
                            'Variable 2': correlation_matrix.columns[j],
                            'Correlation': f"{corr_val:.3f}"
                        })
            
            if high_corr_pairs:
                high_corr_df = pd.DataFrame(high_corr_pairs)
                st.dataframe(high_corr_df, use_container_width=True)
            else:
                st.write("No high correlations found.")
    
    # Distribution Analysis
    if numeric_cols:
        st.subheader("Distribution Analysis")
        
        selected_numeric = st.selectbox("Select numeric variable for distribution analysis:", numeric_cols)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Histogram
            fig = px.histogram(df, x=selected_numeric, nbins=30, 
                             title=f'Distribution of {selected_numeric}')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Box plot
            fig = px.box(df, y=selected_numeric, 
                        title=f'Box Plot of {selected_numeric}')
            st.plotly_chart(fig, use_container_width=True)
        
        # Q-Q plot for normality check
        fig, ax = plt.subplots(figsize=(8, 6))
        stats.probplot(df[selected_numeric].dropna(), dist="norm", plot=ax)
        ax.set_title(f'Q-Q Plot for {selected_numeric}')
        st.pyplot(fig)
    
    # Categorical Analysis
    if categorical_cols:
        st.subheader("Categorical Analysis")
        
        selected_categorical = st.selectbox("Select categorical variable:", categorical_cols)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Value counts
            value_counts = df[selected_categorical].value_counts().head(10)
            fig = px.bar(x=value_counts.index, y=value_counts.values,
                        title=f'Top 10 Categories in {selected_categorical}')
            fig.update_xaxes(title=selected_categorical)
            fig.update_yaxes(title='Count')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart
            value_counts = df[selected_categorical].value_counts().head(8)
            fig = px.pie(values=value_counts.values, names=value_counts.index,
                        title=f'Distribution of {selected_categorical}')
            st.plotly_chart(fig, use_container_width=True)
    
    # Bivariate Analysis
    if len(numeric_cols) >= 2:
        st.subheader("Bivariate Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            x_var = st.selectbox("Select X variable:", numeric_cols, key='x_var')
        with col2:
            y_var = st.selectbox("Select Y variable:", numeric_cols, key='y_var')
        
        if categorical_cols:
            color_var = st.selectbox("Select color variable (optional):", 
                                   ['None'] + categorical_cols)
            color_var = None if color_var == 'None' else color_var
        else:
            color_var = None
        
        fig = px.scatter(df, x=x_var, y=y_var, color=color_var,
                        title=f'{y_var} vs {x_var}')
        st.plotly_chart(fig, use_container_width=True)

def generate_insights(df):
    """Generate automated insights"""
    st.markdown('<div class="section-header">💡 Automated Insights</div>', unsafe_allow_html=True)
    
    insights = []
    
    # Dataset size insights
    if df.shape[0] > 100000:
        insights.append("📊 Large dataset detected - Consider sampling for faster analysis")
    elif df.shape[0] < 100:
        insights.append("📊 Small dataset - Results may not be statistically significant")
    
    # Missing data insights
    missing_percent = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
    if missing_percent > 20:
        insights.append(f"⚠️ High missing data rate ({missing_percent:.1f}%) - Consider data cleaning")
    elif missing_percent > 5:
        insights.append(f"🟡 Moderate missing data rate ({missing_percent:.1f}%) - Review missing data patterns")
    
    # Numeric column insights
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        skewness = df[col].skew()
        if abs(skewness) > 2:
            insights.append(f"📈 '{col}' is highly skewed (skewness: {skewness:.2f}) - Consider transformation")
        
        # Check for potential outliers
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
        if len(outliers) > len(df) * 0.05:  # More than 5% outliers
            insights.append(f"🔍 '{col}' has many outliers ({len(outliers)} values) - Investigate further")
    
    # Categorical insights
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.8:
            insights.append(f"🏷️ '{col}' has high cardinality - May need grouping or encoding")
        
        # Check for imbalanced categories
        value_counts = df[col].value_counts()
        if len(value_counts) > 1:
            imbalance_ratio = value_counts.iloc[0] / value_counts.iloc[-1]
            if imbalance_ratio > 10:
                insights.append(f"⚖️ '{col}' is imbalanced - Consider sampling techniques")
    
    # Correlation insights
    if len(numeric_cols) > 1:
        correlation_matrix = df[numeric_cols].corr()
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                if abs(correlation_matrix.iloc[i, j]) > 0.8:
                    high_corr_pairs.append((
                        correlation_matrix.columns[i], 
                        correlation_matrix.columns[j], 
                        correlation_matrix.iloc[i, j]
                    ))
        
        if high_corr_pairs:
            insights.append(f"🔗 Found {len(high_corr_pairs)} highly correlated pairs - Consider dimensionality reduction")
    
    if insights:
        for insight in insights:
            st.write(f"• {insight}")
    else:
        st.success("No major issues detected in your dataset!")

def export_report(df):
    """Generate downloadable report"""
    st.markdown('<div class="section-header">📄 Export Report</div>', unsafe_allow_html=True)
    
    if st.button("Generate EDA Report"):
        report = io.StringIO()
        
        report.write("# Exploratory Data Analysis Report\n\n")
        report.write(f"**Dataset Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n")
        
        report.write("## Column Information\n")
        for col in df.columns:
            report.write(f"- **{col}**: {df[col].dtype}, {df[col].count()} non-null values\n")
        
        report.write("\n## Statistical Summary\n")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report.write(df[numeric_cols].describe().to_string())
        
        report.write("\n\n## Missing Values\n")
        missing_data = df.isnull().sum()
        for col, missing in missing_data.items():
            if missing > 0:
                report.write(f"- {col}: {missing} missing values ({missing/len(df)*100:.2f}%)\n")
        
        report_content = report.getvalue()
        
        st.download_button(
            label="Download EDA Report",
            data=report_content,
            file_name="eda_report.md",
            mime="text/markdown"
        )

def main():
    """Main application function"""
    st.markdown('<div class="main-header">🔍 Advanced EDA Tool</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h4>Welcome to the Advanced EDA Tool!</h4>
    <p>Upload your dataset and get comprehensive insights including statistical summaries, 
    data quality assessment, visualizations, and automated insights and much more....</p>
    
    <strong>Supported formats: CSV,TSV, Excel (.xlsx, .xls), JSON, Parquet, Pickle </strong><br>
    <strong>Trustworthy and efficient EDA workflow</strong>
    </div>
                
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 EDA Options")
    uploaded_file = st.sidebar.file_uploader(
        "Choose a file", 
        type=['csv', 'xlsx', 'xls', 'json', 'parquet'],
        help="Upload your dataset file"
    )
    
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            df = load_data(uploaded_file)
        
        if df is not None:
            st.success(f"✅ Successfully loaded {uploaded_file.name}")
            
            # Sidebar options
            st.sidebar.subheader("Analysis Options")
            show_raw_data = st.sidebar.checkbox("Show Raw Data", value=False)
            show_basic_info = st.sidebar.checkbox("Basic Information", value=True)
            show_quality = st.sidebar.checkbox("Data Quality Assessment", value=True)
            show_time_series = st.sidebar.checkbox("Time Series Analysis")
            show_stats = st.sidebar.checkbox("Statistical Summary", value=True)
            show_viz = st.sidebar.checkbox("Visualizations", value=True)
            show_insights = st.sidebar.checkbox("Automated Insights", value=True)
            show_stat_tests = st.sidebar.checkbox("Statistical Tests")
            show_feature_eng = st.sidebar.checkbox("Feature Engineering", value=True)


            
            # Sample size for large datasets
            if len(df) > 10000:
                sample_size = st.sidebar.slider(
                    "Sample size for analysis", 
                    min_value=1000, 
                    max_value=min(50000, len(df)), 
                    value=min(10000, len(df)),
                    help="Use sampling for faster analysis of large datasets"
                )
                if sample_size < len(df):
                    df_sample = df.sample(n=sample_size, random_state=42)
                    st.info(f"Using sample of {sample_size:,} rows for analysis")
                else:
                    df_sample = df
            else:
                df_sample = df
            
            # Display raw data
            if show_raw_data:
                st.markdown('<div class="section-header">📋 Raw Data Preview</div>', unsafe_allow_html=True)
                st.dataframe(df.head(100), use_container_width=True)
            
            # Analysis sections
            if show_basic_info:
                basic_info(df)
            
            if show_quality:
                data_quality_assessment(df)
            
            if show_time_series:
                time_series_analysis(df_sample)
                
            if show_stats:
                statistical_summary(df_sample)
            
            if show_viz:
                create_visualizations(df_sample)
            
            if show_insights:
                generate_insights(df)

            if show_stat_tests:
                statistical_tests(df_sample)

            if show_feature_eng:
                feature_engineering(df_sample)

            

            
            # Export functionality
            export_report(df)
    
    else:
        st.info("👆 Please upload a file to begin the EDA process")
        
        # Sample data option
        st.subheader("🎯 Try with Sample Data")
        if st.button("Load Sample Dataset (Titanic)"):
            # Create sample Titanic dataset
            np.random.seed(42)
            sample_data = {
                'Age': np.random.normal(30, 12, 891),
                'Fare': np.random.exponential(20, 891),
                'Sex': np.random.choice(['male', 'female'], 891),
                'Survived': np.random.choice([0, 1], 891),
                'Pclass': np.random.choice([1, 2, 3], 891),
                'Embarked': np.random.choice(['S', 'C', 'Q'], 891)
            }
            
            df = pd.DataFrame(sample_data)
            # Add some missing values
            df.loc[np.random.choice(df.index, 100, replace=False), 'Age'] = np.nan
            df.loc[np.random.choice(df.index, 10, replace=False), 'Embarked'] = np.nan
            
            st.session_state['sample_df'] = df
            st.success("Sample dataset loaded! Scroll down to see the analysis.")
            
            # Run analysis on sample data
            basic_info(df)
            data_quality_assessment(df)
            statistical_summary(df)
            create_visualizations(df)
            generate_insights(df)

if __name__ == "__main__":
    main()
