import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV data
csv_filename = 'summary_blocked_rate_data_static.csv'
data = pd.read_csv(csv_filename)

# Plot Mean Blocked Rate vs. Mean Total Flows for each threshold with error bars
plt.figure(figsize=(10, 6))

# Get unique threshold values
thresholds = data['Threshold'].unique()

# Plot data for each threshold with error bars
for threshold in thresholds:
    subset = data[data['Threshold'] == threshold]
    plt.errorbar(subset['Mean Total Flows'], subset['Mean Blocked Rate (%)'],
                 yerr=subset['Std Dev Blocked Rate (%)'], marker='o', label=f'Threshold {threshold}', capsize=5)

# Add labels and title
plt.xlabel('Mean Total Flows')
plt.ylabel('Mean Blocked Rate (%)')
plt.title('Mean Blocked Rate vs. Mean Total Flows for Different Thresholds')
plt.legend(title='Threshold')
plt.grid(True)

# Show plot
plt.show()

