import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Page settings
st.set_page_config(
    page_title="CRISP-DM Linear Regression & Outlier App",
    page_icon="📈",
    layout="wide"
)

# App Title & Introduction
st.title("📈 CRISP-DM Linear Regression & Outlier Detection")
st.markdown("""
This interactive Streamlit app demonstrates the **six phases of the CRISP-DM framework** 
applied to a synthetic linear regression problem with custom parameters.
""")

# ==========================================
# SIDEBAR: PARAMETER CONTROL
# ==========================================
st.sidebar.header("🛠️ Model Configuration")

# Read query parameters from URL for defaults
query_params = st.query_params
default_n = int(query_params.get("n", 200))
default_a = float(query_params.get("a", 15.0))
default_b = float(query_params.get("b", 50.0))
default_var = float(query_params.get("var", 200.0))

# Clamp values within slider limits
default_n = min(max(default_n, 10), 1000)
default_a = min(max(default_a, -50.0), 50.0)
default_b = min(max(default_b, 0.0), 100.0)
default_var = min(max(default_var, 0.0), 1000.0)

# Sliders configured with query parameters
n_points = st.sidebar.slider("Number of points (n)", min_value=10, max_value=1000, value=default_n, step=10)
true_a = st.sidebar.slider("True Slope (a)", min_value=-50.0, max_value=50.0, value=default_a, step=1.0)
true_b = st.sidebar.slider("True Intercept (b)", min_value=0.0, max_value=100.0, value=default_b, step=1.0)
true_var = st.sidebar.slider("Noise Variance (var)", min_value=0.0, max_value=1000.0, value=default_var, step=10.0)

# Sync parameters back to URL query parameters
st.query_params.update(n=n_points, a=true_a, b=true_b, var=true_var)

# Optional Seed
use_seed = st.sidebar.checkbox("Use fixed random seed", value=True)
seed_value = st.sidebar.number_input("Seed Value", min_value=0, max_value=9999, value=42) if use_seed else None

# CRISP-DM Phase Selection Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Business Understanding", 
    "2. Data Understanding", 
    "3. Data Preparation", 
    "4. Modeling", 
    "5. Evaluation", 
    "6. Deployment"
])

# ==========================================
# PHASE 1: BUSINESS UNDERSTANDING
# ==========================================
with tab1:
    st.subheader("🎯 Phase 1: Business Understanding")
    st.markdown("""
    ### Objective
    The goal of this project is to:
    1. **Generate synthetic linear data** with controlled noise.
    2. **Recover the underlying linear relationship** via Linear Regression (least squares).
    3. **Detect and analyze outliers**—defined as the data points that deviate most from the fitted regression line.
    
    ### Business Value
    Outlier detection is critical in applications like fraud detection, sensor failures, and market anomaly identification, where deviations from the baseline trend signal important events.
    """)

# ==========================================
# PHASE 2: DATA UNDERSTANDING
# ==========================================
with tab2:
    st.subheader("📊 Phase 2: Data Understanding")
    st.markdown(f"""
    ### Data-Generating Process
    The dataset is synthetically generated according to the following mathematical relationship:
    
    $$y = a \\cdot x + b + \\mathcal{N}(0, \\sigma^2)$$
    
    Where:
    - **$n$**: Number of points = `{n_points}`
    - **$x$**: Uniformly distributed between $-100$ and $100$.
    - **$a$ (Slope)**: `{true_a}`
    - **$b$ (Intercept)**: `{true_b}`
    - **$\\sigma^2$ (Variance)**: `{true_var}` (Standard deviation $\\sigma = {np.sqrt(true_var):.2f}$)
    """)

# ==========================================
# PHASE 3: DATA PREPARATION
# ==========================================
# Generate data
if use_seed:
    np.random.seed(seed_value)

x = np.random.uniform(-100, 100, n_points)
std_dev = np.sqrt(true_var)
noise = np.random.normal(0, std_dev, n_points)
y = true_a * x + true_b + noise

# Reshape & load into DataFrame
df = pd.DataFrame({'x': x, 'y': y})

with tab3:
    st.subheader("🧹 Phase 3: Data Preparation")
    st.markdown("We generate the raw synthetic data, format the inputs, and structure it into a pandas DataFrame.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**First 10 Rows of Prepared Data:**")
        st.dataframe(df.head(10), use_container_width=True)
    with col2:
        st.markdown("**Data Summary Statistics:**")
        st.dataframe(df.describe(), use_container_width=True)

# ==========================================
# PHASE 4: MODELING
# ==========================================
# Apply linear regression (least squares)
X_model = df[['x']].values
y_model = df['y'].values

model = LinearRegression()
model.fit(X_model, y_model)

est_a = model.coef_[0]
est_b = model.intercept_

with tab4:
    st.subheader("🤖 Phase 4: Modeling")
    st.markdown("""
    Applying ordinary least squares (OLS) linear regression to find the best-fit line.
    
    ```python
    from sklearn.linear_model import LinearRegression
    
    model = LinearRegression()
    model.fit(X, y)
    ```
    """)
    
    col1, col2 = st.columns(2)
    col1.metric("Estimated Slope (a)", f"{est_a:.4f}", f"True: {true_a}")
    col2.metric("Estimated Intercept (b)", f"{est_b:.4f}", f"True: {true_b}")

# ==========================================
# PHASE 5: EVALUATION
# ==========================================
# Calculate evaluation metrics
y_pred = model.predict(X_model)
r2 = r2_score(y_model, y_pred)
mse = mean_squared_error(y_model, y_pred)
rmse = np.sqrt(mse)

# Residuals & top 10 outliers
df_eval = df.copy()
df_eval['y_pred'] = y_pred
df_eval['residual'] = np.abs(df_eval['y'] - df_eval['y_pred'])
df_eval['squared_residual'] = df_eval['residual'] ** 2

outliers = df_eval.nlargest(10, 'residual').copy()
outliers['rank'] = range(1, 11)

with tab5:
    st.subheader("⚖️ Phase 5: Evaluation")
    st.markdown("Compare modeling results and identify the 10 data points with the largest residuals using a 3:1 layout split.")
    
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.markdown("### Top 10 Outliers (Ranked by Residual)")
        st.dataframe(
            outliers[['rank', 'x', 'y', 'y_pred', 'residual', 'squared_residual']],
            use_container_width=True,
            hide_index=True
        )
        
    with col_sidebar:
        st.markdown("### Metrics Summary")
        st.metric("R-squared (R²)", f"{r2:.5f}")
        st.metric("RMSE", f"{rmse:.4f}")
        st.metric("Est. Variance (MSE)", f"{mse:.2f}", f"True Var: {true_var}")

# ==========================================
# PHASE 6: DEPLOYMENT
# ==========================================
with tab6:
    st.subheader("🚀 Phase 6: Deployment")
    st.markdown("Displaying the interactive visualization of the regression line and outliers in a 3:1 aspect ratio layout.")
    
    # Matplotlib Plot with 3:1 Aspect Ratio (15x5)
    fig, ax = plt.subplots(figsize=(15, 5))
    
    # 1. Scatter plot of all points (blue)
    ax.scatter(df_eval['x'], df_eval['y'], color='#3182bd', alpha=0.6, label='Data Points')
    
    # 2. Regression line (red)
    x_range = np.linspace(-100, 100, 500)
    y_line = est_a * x_range + est_b
    ax.plot(x_range, y_line, color='#de2d26', linewidth=2.5, label=f'Regression Line (y = {est_a:.2f}x + {est_b:.2f})')
    
    # 3. Highlight top 10 outliers (orange)
    ax.scatter(outliers['x'], outliers['y'], color='#fec44f', edgecolor='black', s=150, marker='o', zorder=5, label='Top 10 Outliers')
    
    # Annotate outliers
    for _, row in outliers.iterrows():
        rank = int(row['rank'])
        ax.annotate(
            f"#{rank} ({row['squared_residual']:.0f})", 
            (row['x'], row['y']), 
            textcoords="offset points", 
            xytext=(0, 12), 
            ha='center', 
            fontsize=8, 
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffeda0", alpha=0.9, edgecolor='orange')
        )
        
    ax.set_title(f"Linear Regression Fit (n={n_points})\nTrue Var: {true_var:.1f} | Est Var: {mse:.1f}", fontsize=14, fontweight='bold')
    ax.set_xlabel("X", fontsize=12)
    ax.set_ylabel("Y", fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    col_plot, col_info = st.columns([3, 1])
    with col_plot:
        st.pyplot(fig)
    with col_info:
        st.markdown("### Deployment Info")
        st.info("""
        The red line represents the recovered model:
        **y = {:.2f}x + {:.2f}**
        
        The orange circled points are the top 10 outliers contributing the most to the total variance.
        """.format(est_a, est_b))
