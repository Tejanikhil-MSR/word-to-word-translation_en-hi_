import pandas as pd
import os
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="DataAggregator")

    parser.add_argument("--input_folder", type=str, default=".", help="Path of the datasets folder")
    parser.add_argument("--output_path", type=str, default=".", help="Name of the file")

    args = parser.parse_args()

    files = os.listdir(args.input_folder)

    with open(args.output_path, 'w', encoding='utf-8') as f:
        for file in files:
            file_path = os.path.join(args.input_folder, file)
            if os.path.isfile(file_path) and file.endswith('.csv'):
                df = pd.read_csv(file_path)
                
                # Replace 'column_name' with your actual column
                if 'content' in df.columns:
                    for item in df['content']:
                        f.write(str(item) + '\n')


# run it using 
# python ./aggregate.py --input_folder "./en" --output_path "../Training/TrainingReadyEnglishText.txt"
# python ./aggregate.py --input_folder "./hi" --output_path "../Training/TrainingReadyHindiText.txt"