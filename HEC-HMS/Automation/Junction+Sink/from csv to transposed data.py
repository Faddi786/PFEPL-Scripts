import os
import pandas as pd

def process_csvs_in_folder(root_folder):
    final_df = pd.DataFrame()
    processed_files = 0  # counter

    print(f"🔍 Scanning folder: {root_folder}\n")

    for filename in os.listdir(root_folder):
        if filename.endswith('.csv'):
            file_path = os.path.join(root_folder, filename)
            print(f"📂 Processing file: {filename} ...")

            try:
                # Read CSV
                df = pd.read_csv(file_path)

                # ✅ Make a proper copy to avoid SettingWithCopyWarning
                # df_filtered = df[df['Type'] == 'Junction'].copy()
                df_filtered = df.copy()


                # Divide Volume (M3) by 1000
                df_filtered.loc[:, 'Volume (M3)'] = df_filtered['Volume (M3)'] / 1000

                # Extract year from filename (e.g., RUN_Run_2_2008.csv → 2008)
                year = filename.split('_')[-1].split('.')[0]
                df_filtered.loc[:, 'Year'] = int(year)

                # Pivot the data
                df_pivot = df_filtered.pivot(
                    index='Year', 
                    columns='Hydrologic Element', 
                    values='Volume (M3)'
                )

                # Append to final DataFrame
                final_df = pd.concat([final_df, df_pivot], axis=0)

                processed_files += 1
                print(f"✅ Successfully processed: {filename}")

            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")

    # After all files processed
    if processed_files > 0:
        final_df.reset_index(inplace=True)
        output_file = 'output_data.xlsx'
        final_df.to_excel(output_file, index=False)
        print(f"\n💾 All done! Saved combined results to '{output_file}'")
        print(f"📊 Total files processed: {processed_files}")
    else:
        print("⚠️ No CSV files were found or processed in this folder.")

# Run the function
root_folder = 'results_csv'
process_csvs_in_folder(root_folder)

