import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import os

# Read the output Excel file
input_file = r"C:\Users\Swapnali\Desktop\Stages (HEC-HMS)\Time Series Chart Generator for Dependable Yield Data\combined_output_for_all_years_ulhas.xlsx"
# '75_Percent_Dependable_FULL.xlsx'
df = pd.read_excel(input_file, sheet_name='global_summary')

# Convert Date column to datetime format for better plotting
df['Date'] = pd.to_datetime(df['Date'], format='%d-%b')

print(f"\n{'='*80}")
print(f"GENERATING INDIVIDUAL CHARTS FOR EACH JUNCTION")
print(f"{'='*80}")
print(f"Input file: {input_file}")
print(f"Total junctions: {len(df.columns) - 1}")
print(f"Total dates: {len(df)}")
print(f"{'='*80}\n")

# Create output directory for charts
output_dir = "junction_charts_FULL"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}\n")

# Get junction columns (exclude 'Date')
junction_columns = [col for col in df.columns if col != 'Date']

# Generate individual chart for each junction
for idx, junction in enumerate(junction_columns, 1):
    print(f"[{idx}/{len(junction_columns)}] Creating chart for: {junction}")
    
    # Create figure with larger width to accommodate all dates
    fig, ax = plt.subplots(figsize=(24, 8))
    
    # Plot the line with markers
    ax.plot(df['Date'], df[junction], 
            marker='o', 
            linewidth=2, 
            markersize=4,
            color='#2E86AB',
            markerfacecolor='#A23B72',
            markeredgecolor='white',
            markeredgewidth=1,
            label=f'{junction}')
    
    # Formatting
    ax.set_xlabel('Date (2024)', fontsize=14, fontweight='bold')
    ax.set_ylabel('75% Dependable Yield (in units)', fontsize=14, fontweight='bold')
    ax.set_title(f'75% Dependable Yield - {junction}\n(Based on all available years: 1975-2024)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    # Format X-axis to show EVERY date
    # Set all dates as major ticks
    ax.set_xticks(df['Date'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    
    # Rotate x-axis labels vertically for readability with all dates
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='center', fontsize=7)
    ax.tick_params(axis='y', labelsize=11)
    
    # Adjust x-axis to fit all data points
    ax.set_xlim(df['Date'].min(), df['Date'].max())
    
    # Add value range as text
    min_val = df[junction].min()
    max_val = df[junction].max()
    mean_val = df[junction].mean()
    
    textstr = f'Min: {min_val:.4f}\nMax: {max_val:.4f}\nMean: {mean_val:.4f}'
    ax.text(0.02, 0.98, textstr, 
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7, edgecolor='gray'))
    
    # Set background color
    ax.set_facecolor('#FAFAFA')
    
    # Adjust layout to prevent label cutoff
    fig.tight_layout()
    
    # Save the chart with sanitized filename
    safe_filename = junction.replace('/', '').replace('\\', '').replace(':', '').replace(' ', '')
    output_file = os.path.join(output_dir, f"{safe_filename}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    
    # Close the figure to free memory
    plt.close()
    
    print(f"    Saved: {output_file}")

print(f"\n{'='*80}")
print(f"[SUCCESS] ALL CHARTS CREATED!")
print(f"{'='*80}")
print(f"\nTotal charts generated: {len(junction_columns)}")
print(f"Location: ./{output_dir}/")
print(f"\nFiles created:")
for junction in junction_columns[:5]:
    safe_filename = junction.replace('/', '').replace('\\', '').replace(':', '_')
    print(f"  - {safe_filename}.png")
if len(junction_columns) > 5:
    print(f"  ... and {len(junction_columns) - 5} more")
print(f"\n{'='*80}\n")