import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import boto3
from dotenv import load_dotenv
import os
load_dotenv()

s3 = boto3.client('s3')
bucket_name = os.getenv("BUCKET_NAME")

def retrieve_from_s3():
    """retrieve data from s3 and store in folder 'downloads/' """
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
def app():
    """Load datasets"""
    last_five_form = pd.read_csv('downloads/last_five_form.csv')
    team_standings = pd.read_csv('downloads/team_standings.csv')
    upcoming_fixtures = pd.read_csv('downloads/upcoming_fixtures.csv')

    """Merge datasets"""
    data = pd.merge(last_five_form, team_standings, on="team", how="left")

    """Feature Engineering"""
    
    data['recent_points_avg'] = data[['form_1', 'form_2', 'form_3', 'form_4', 'form_5']].mean(axis=1)

    """Normalize rank """
    data['rank_scaled'] = 1 / data['rank']

    """Define target variable"""
    data['target'] = data['form_1'].apply(lambda x: 1 if x == 1 else 0)

    """Select features"""
    features = [
        'points_avg', 'xg_diff_per90', 'goal_diff', 'xg_for', 'xg_against',
        'games', 'wins', 'ties', 'losses', 'recent_points_avg', 'rank_scaled'
    ]
    X = data[features]
    y = data['target']

    """Split data into training and testing sets"""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    """Train models"""
    models = {
        'Random Forest': RandomForestClassifier(random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'XGBoost': XGBClassifier(random_state=42),
        'SVM': SVC(random_state=42)
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"{name} Accuracy: {acc:.2f}")

        """Predict upcoming matches"""
        upcoming_data = pd.merge(upcoming_fixtures, team_standings, left_on='home_team', right_on='team', how='left')
        upcoming_data = pd.merge(upcoming_data, last_five_form, left_on='home_team', right_on='team', how='left')
        upcoming_data = upcoming_data.fillna(0)  

        """Compute upcoming features"""
        upcoming_data['recent_points_avg'] = upcoming_data[['form_1', 'form_2', 'form_3', 'form_4', 'form_5']].mean(axis=1)
        upcoming_data['rank_scaled'] = 1 / upcoming_data['rank']

        """Select same features as training data"""
        upcoming_features = upcoming_data[features]
        upcoming_predictions = model.predict(upcoming_features)

        upcoming_fixtures[f'predicted_{name}'] = upcoming_predictions

    """Save predictions"""
    #upcoming_fixtures.to_csv('predictions.csv', index=False)
    print(upcoming_fixtures[['home_team', 'away_team'] + [f'predicted_{name}' for name in models]])

   
def main():
    retrieve_from_s3()
    app()

if __name__ == "__main__":
    main()