import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# ==========================================
# PHASE 1: BUSINESS UNDERSTANDING
# ==========================================
"""
Goal:
Generate synthetic linear data with noise, recover the underlying linear relationship
via linear regression, and identify the points that deviate the most from this line
(outlier detection).
"""

# ==========================================
# PHASE 2: DATA UNDERSTANDING
# ==========================================
"""
Data-Generating Process:
- We generate n data points (x, y) where:
  - x is uniformly distributed between -100 and 100.
  - y = a * x + b + N(0, var) where N(0, var) is a normal distribution with mean 0
    and variance `var`. Standard deviation is sqrt(var).
- True parameters chosen randomly (if not specified):
  - Slope 'a' is randomly selected in the range [-50, 50].
  - Intercept 'b' is randomly selected in the range [0, 100].
  - Variance 'var' is randomly selected in the range [0, 300].
- Parameter 'n' represents the number of points (default: 200).
- An adjustable random seed ensures reproducibility.
"""

def generate_true_parameters(seed=None):
    """
    Randomly generates true parameters (a, b, var) according to specs.
    """
    if seed is not None:
        np.random.seed(seed)
    
    a = np.random.uniform(-50, 50)
    b = np.random.uniform(0, 100)
    var = np.random.uniform(0, 300)
    
    return a, b, var


# ==========================================
# PHASE 3: DATA PREPARATION
# ==========================================
def prepare_data(n=200, a=None, b=None, var=None, seed=None):
    """
    Generates synthetic dataset, reshapes arrays for modeling,
    and returns a pandas DataFrame along with the true parameters used.
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Generate true parameters if not provided
    if a is None or b is None or var is None:
        random_a, random_b, random_var = generate_true_parameters(seed=seed)
        a = a if a is not None else random_a
        b = b if b is not None else random_b
        var = var if var is not None else random_var
        
    # Generate independent variable x
    x = np.random.uniform(-100, 100, n)
    
    # Generate noise with standard deviation equal to sqrt(var)
    std_dev = np.sqrt(var)
    noise = np.random.normal(0, std_dev, n)
    
    # Generate dependent variable y
    y = a * x + b + noise
    
    # Create pandas DataFrame
    df = pd.DataFrame({
        'x': x,
        'y': y
    })
    
    return df, a, b, var


# ==========================================
# PHASE 4: MODELING
# ==========================================
def build_model(df):
    """
    Applies linear regression (least squares) to estimate slope a and intercept b.
    """
    # Reshape features to 2D array as required by scikit-learn
    X = df[['x']].values
    y = df['y'].values
    
    # Initialize and fit the model
    model = LinearRegression()
    model.fit(X, y)
    
    # Extract estimated slope and intercept
    est_a = model.coef_[0]
    est_b = model.intercept_
    
    return model, est_a, est_b


# ==========================================
# PHASE 5: EVALUATION
# ==========================================
def evaluate_model(df, model, true_a, true_b, true_var):
    """
    Reports metrics (R2, RMSE), compares parameters, computes residuals,
    and returns the top 10 outliers.
    """
    X = df[['x']].values
    y_actual = df['y'].values
    y_pred = model.predict(X)
    
    # Calculate evaluation metrics
    r2 = r2_score(y_actual, y_pred)
    mse = mean_squared_error(y_actual, y_pred)
    rmse = np.sqrt(mse)
    
    # Compute residuals: absolute difference between actual and predicted
    residuals = np.abs(y_actual - y_pred)
    
    # Add predicted values and residuals to the DataFrame
    df_eval = df.copy()
    df_eval['y_pred'] = y_pred
    df_eval['residual'] = residuals
    df_eval['squared_residual'] = residuals ** 2
    
    # Retrieve top 10 outliers (largest residuals)
    outliers = df_eval.nlargest(10, 'residual').copy()
    outliers['rank'] = range(1, 11)
    
    # Print results
    print("=" * 75)
    print(" EVALUATION RESULTS")
    print("=" * 75)
    print(f"True Slope (a):      {true_a:10.4f}  |  Estimated Slope (a):      {model.coef_[0]:10.4f}")
    print(f"True Intercept (b):  {true_b:10.4f}  |  Estimated Intercept (b):  {model.intercept_:10.4f}")
    print(f"True Variance (var): {true_var:10.4f}  |  Estimated Var (MSE):      {mse:10.4f}")
    print("-" * 75)
    print(f"R-squared (R^2):      {r2:10.6f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:10.6f}")
    print("-" * 75)
    print("\nTOP 10 OUTLIERS (Ranked by Residual, Showing Variance Contribution):")
    # Display table formatted nicely
    print(outliers[['rank', 'x', 'y', 'y_pred', 'residual', 'squared_residual']].to_string(index=False))
    print("=" * 75)
    
    return df_eval, outliers, mse


# ==========================================
# PHASE 6: DEPLOYMENT
# ==========================================
def deploy_visualization(df_eval, outliers, true_a, true_b, true_var, est_a, est_b, est_var, save_path="regression_plot.png"):
    """
    Produces and displays/saves the final visual plot.
    """
    plt.figure(figsize=(12, 7))
    
    # 1. Scatter plot of all points (blue)
    plt.scatter(df_eval['x'], df_eval['y'], color='blue', alpha=0.5, label='Data Points')
    
    # 2. Regression line (red)
    x_range = np.linspace(-100, 100, 500)
    y_line = est_a * x_range + est_b
    plt.plot(x_range, y_line, color='red', linewidth=2.5, label=f'Regression Line (y = {est_a:.2f}x + {est_b:.2f})')
    
    # 3. Highlight top 10 outliers (orange)
    plt.scatter(outliers['x'], outliers['y'], color='orange', edgecolor='black', s=120, marker='o', label='Top 10 Outliers')
    
    # Annotate outliers with their rank order and squared residual (variance contribution)
    for _, row in outliers.iterrows():
        rank = int(row['rank'])
        plt.annotate(f"#{rank}\n(Var Contrib={row['squared_residual']:.1f})", 
                     (row['x'], row['y']), 
                     textcoords="offset points", 
                     xytext=(0, 12), 
                     ha='center', 
                     fontsize=8, 
                     fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="wheat", alpha=0.8, edgecolor='orange'))
        
    # Set titles and labels
    plt.title(f"Linear Regression & Outlier Detection (CRISP-DM)\nTrue Var: {true_var:.2f} | Est Var (MSE): {est_var:.2f}", fontsize=14, fontweight='bold')
    plt.xlabel("X (Independent Variable)", fontsize=12)
    plt.ylabel("Y (Dependent Variable)", fontsize=12)
    
    # Add a legend
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"\nVisualization saved successfully to: {save_path}")
    plt.show()


# ==========================================
# MAIN EXECUTION PIPELINE
# ==========================================
if __name__ == "__main__":
    # Choose random seed for reproducibility
    seed = 42
    n_points = 200
    
    print("Starting CRISP-DM Linear Regression Pipeline...\n")
    
    # Phase 3: Data Preparation
    df, true_a, true_b, true_var = prepare_data(n=n_points, seed=seed)
    
    # Phase 4: Modeling
    model, est_a, est_b = build_model(df)
    
    # Phase 5: Evaluation
    df_eval, outliers, est_var = evaluate_model(df, model, true_a, true_b, true_var)
    
    # Phase 6: Deployment
    deploy_visualization(df_eval, outliers, true_a, true_b, true_var, est_a, est_b, est_var)
