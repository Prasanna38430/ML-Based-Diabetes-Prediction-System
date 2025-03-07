import pandas as pd
import os
 
input_file = './airflow/data/diabetes_dataset.csv'
 
base_name = os.path.splitext(os.path.basename(input_file))[0]
 
df = pd.read_csv(input_file)
 
raw_data_folder = './airflow/data/raw_data'
 
os.makedirs(raw_data_folder, exist_ok=True)
 
num_files = 4000  
 
# Calculate the chunk size based on the number of files
chunk_size = len(df) // num_files
if len(df) % num_files != 0:
    chunk_size += 1  # Ensure the last file contains any remaining rows
 
# Split the DataFrame into the desired number of files
chunk_files = []
for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i+chunk_size]
    output_file = os.path.join(raw_data_folder, f'{base_name}_chunk_{i//chunk_size + 1}.csv')
    chunk.to_csv(output_file, index=False)
    chunk_files.append(output_file)  # Keep track of the file paths
    print(f"Saved: {output_file}")
 
