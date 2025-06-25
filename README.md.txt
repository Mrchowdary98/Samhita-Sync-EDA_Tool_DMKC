# 📊 Samhita Sync – Your EDA Powerhouse

**Samhita Sync** is a powerful, no-code **Exploratory Data Analysis (EDA)** tool built with **Streamlit**.  
It enables users to analyze, visualize, and transform their data — performing **80–90% of the EDA process** automatically through an intuitive interface.

---

## 🚀 Key EDA Features

- ✅ **Upload Any Dataset**  
  Supports `.csv`, `.xlsx`, `.xls`, `.json`, `.parquet`, `.tsv`, `.txt`, `.pkl` formats.

- 📈 **Descriptive Statistics (EDA Core)**  
  Summarize numeric and categorical columns with:
  - Mean, Std, Skewness, Kurtosis, Missing %, Unique Count, Mode

- 🔍 **Data Quality Assessment**  
  Detect:
  - Missing values
  - Duplicates
  - Constant or high-cardinality features
  - Outliers (via IQR)

- 📊 **Visual EDA Components**  
  Interactive plots for:
  - Distributions
  - Categorical frequency
  - Correlations
  - Bivariate scatter plots
  - Time series

- 💡 **Automated EDA Insights**  
  Samhita Sync intelligently highlights:
  - Highly skewed columns
  - Imbalanced classes
  - Highly correlated variable pairs
  - Outlier-heavy features
  - Missing value warnings

- 🧪 **Statistical Hypothesis Testing (EDA + Inference)**  
  Choose and run:
  - Normality Tests (Shapiro-Wilk, KS)
  - Independent T-Test
  - Chi-Square Test
  - Correlation Matrix & Heatmap

- 🛠️ **Feature Engineering**  
  Data preparation during EDA:
  - Numerical scaling (log, z-score, min-max)
  - Categorical encoding (label, one-hot, frequency)
  - Datetime decomposition (year, month, weekday, etc.)
  - Binning & column deletion
  - Preview updated DataFrame
  - Download modified dataset

- 📅 **Time Series EDA**  
  Understand your temporal data:
  - Time-value trend plots
  - Date range, frequency, mean, std analysis

---

## 📁 File Format Support

- `.csv`, `.xlsx`, `.xls`
- `.json`, `.parquet`, `.pkl`
- `.tsv`, `.txt`

---

## ▶️ How to Use

```bash
git clone https://github.com/Dadipavan/EDA.git
cd Samhita Sync
pip install -r requirements.txt
streamlit run eda_app.py
