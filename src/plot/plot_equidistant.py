import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Get the project root directory
current_file = Path(__file__).resolve()
project_root = current_file.parents[1]

plot_data_name = 'blocked_rate'

# Define file paths
file_paths = [
    project_root / 'result' / f'summary_{plot_data_name}_0.csv',
    project_root / 'result' / f'summary_{plot_data_name}_1.csv',
    project_root / 'result' / f'summary_{plot_data_name}_2.csv',
    project_root / 'result' / f'summary_{plot_data_name}_100.csv'
]

# Define marker styles and colors
marker_styles = ['o', 's', '^', 'D']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

# Define custom labels for each line
labels = [
    "1+1 protection",
    r"TC-SSPR $\beta$=1",
    r"TC-SSPR $\beta$=2",
    "maximum shared",
]

# Plot the results with error bars
plt.figure(figsize=(8, 8))

for i, file_path in enumerate(file_paths):
    # Load the CSV data
    data = pd.read_csv(file_path)
    avg_flow_nums = data['Avg Flow Num']
    mean_blocked_rate = data['Mean Blocked Rate (%)']  # Corrected column name
    std_blocked_rate = data['Std Dev Blocked Rate (%)']  # Corrected column name

    # Plot with different colors, marker styles, and individual labels
    plt.errorbar(avg_flow_nums, mean_blocked_rate, yerr=std_blocked_rate, fmt=marker_styles[i % len(marker_styles)] + '-',
                 color=colors[i % len(colors)], capsize=5, label=labels[i])

plt.xlabel('Average Flow Number', fontsize=14)
plt.ylabel('Blocked Rate (%)', fontsize=14)  # Updated label to match the data
plt.legend()
plt.grid(True)

# Save the plot with reduced white space
plt.savefig(project_root / 'plot' / 'blocked_rate.svg', format='svg', bbox_inches='tight')

plt.show()
