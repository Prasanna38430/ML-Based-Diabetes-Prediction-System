import pandas as pd
import os
 
def split_by_num_files(df, output_base_dir, base_name, num_files):
    total_rows = len(df)
    base_chunk_size = total_rows // num_files
    remainder = total_rows % num_files
 
    start_idx = 0
    for chunk_num in range(num_files):
        # Distribute remainder one row per chunk starting from first chunk
        current_chunk_size = base_chunk_size + (1 if chunk_num < remainder else 0)
        end_idx = start_idx + current_chunk_size
 
        chunk = df.iloc[start_idx:end_idx]
 
        output_file = os.path.join(output_base_dir, f'{base_name}_chunk_{chunk_num + 1}.csv')
        chunk.to_csv(output_file, index=False)
        print(f"Saved: {output_file} with {len(chunk)} rows")
 
        start_idx = end_idx
 
# Input files
input_files = [
    ('./airflow/data/generated_errors/diabetes_data_with_errors.csv', 20),
    ('./airflow/data/generated_errors/diabetes_data2_with_errors.csv', 3800)
]
 
output_base_dir = './airflow/data/raw_data'
os.makedirs(output_base_dir, exist_ok=True)
 
for input_file, num_files in input_files:
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    df = pd.read_csv(input_file)
 
    split_by_num_files(df, output_base_dir, base_name, num_files)