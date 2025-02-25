import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import boto3
from dotenv import load_dotenv
import os
load_dotenv()

s3 = boto3.client('s3')
bucket_name = os.getenv("BUCKET_NAME")

def app():
    
    files =['upcoming_fixtures.csv','team_standings.csv','last_five_form.csv']
    for file in files:
        try:
            download_path = f'downloads/{file}'
            s3.download_file(
                bucket_name,
                file,
                download_path
            )
            print(f"Downloaded file into downloads/{file}")
            
        except Exception as e:
            print(f'error: {e}')

def main():
    app()

if __name__ == "__main__":
    main()