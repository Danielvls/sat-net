import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Get the project root directory
current_file = Path(__file__).resolve()
project_root = current_file.parents[1]

# Load the CSV data
csv_filepath1 = project_root / 'result' / 'summary_blocked_rate_data_static.csv'
csv_filepath2 = project_root / 'result' / 'summary_blocked_rate_data_dynamic.csv'

data_static = pd.read_csv(csv_filepath1)
data_dynamic = pd.read_csv(csv_filepath2)

# Plot Mean Blocked Rate vs. Avg Flow Num for each threshold with error bars
plt.figure(figsize=(12, 8))

# Get unique threshold values for static and dynamic data
thresholds_static = data_static['Threshold'].unique()
thresholds_dynamic = data_dynamic['Threshold'].unique()

# Plot static data for each threshold with error bars
for threshold in thresholds_static:
    subset = data_static[data_static['Threshold'] == threshold]
    plt.errorbar(subset['Avg Flow Num'], subset['Mean Blocked Rate (%)'],
                 yerr=subset['Std Dev Blocked Rate (%)'], marker='o', linestyle='-', label=f'Static - Threshold {threshold}', capsize=5)

# Plot dynamic data for each threshold with error bars
for threshold in thresholds_dynamic:
    subset = data_dynamic[data_dynamic['Threshold'] == threshold]
    plt.errorbar(subset['Avg Flow Num'], subset['Mean Blocked Rate (%)'],
                 yerr=subset['Std Dev Blocked Rate (%)'], marker='s', linestyle='--', label=f'Dynamic - Threshold {threshold}', capsize=5)

# Add labels and title
plt.xlabel('Avg Flow Num')
plt.ylabel('Mean Blocked Rate (%)')
plt.title('Mean Blocked Rate vs. Avg Flow Num for Static and Dynamic Thresholds')
plt.legend(title='Type and Threshold')
plt.grid(True)

# Save and show the plot
plt.savefig('block_rate_compare.png', dpi=300)
plt.show()