from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import boto3
from soccer_data_api import SoccerDataAPI
from collections import defaultdict
import os
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3')
bucket_name = os.getenv("BUCKET_NAME")
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

"""Testing for multi league functionality, currently set for the spanish league"""

league="laliga"
country="spain"
sport="soccer"
week = 26



def get_standings():
    
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options)
    URL = "https://fbref.com/en/comps/12/La-Liga-Stats"
    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    teams = []
    team_form = []
    for team in soup.select("table.stats_table tbody tr")[:20]:
        team_data = {}
        team_data["rank"] = team.find("th", {"data-stat": "rank"}).text
        team_name_tag = team.find("td", {"data-stat": "team"})
        if team_name_tag and team_name_tag.a:  
            team_data["team"] = team_name_tag.a.text.strip()
        stats = [
            "games", "wins", "ties", "losses", "goals_for", "goals_against", 
            "goal_diff", "points", "points_avg", "xg_for", "xg_against", 
            "xg_diff", "xg_diff_per90"
        ]
        for stat in stats:
            stat_tag = team.find("td", {"data-stat": stat})
            team_data[stat] = stat_tag.text.strip() if stat_tag else None

        
        team_form.append({"team":team_name_tag.a.text.strip(),"form":team.find("td",{"data-stat":"last_5"}).text})
        
        teams.append(team_data)
    team_form_df=pd.DataFrame(team_form)
    
    mapping = {
        "W": 1,
        "D": 0,
        "L": -1
    }
    team_form_df["form_list"] = team_form_df["form"].str.split()
    team_form_df["encoded_form"] = team_form_df["form_list"].apply(
        lambda outcomes: [mapping[result] for result in outcomes]
    )
  
    
    form_df = pd.DataFrame(team_form_df["encoded_form"].tolist(),columns=["form_1","form_2","form_3","form_4","form_5"])
    form_df = pd.concat([team_form_df["team"],form_df], axis =1)
    form_df = form_df.sort_values(by=["team"])

    csv_buffer = StringIO()
    df = pd.DataFrame(teams)
    df = df.sort_values(by=['team'])
    df.to_csv(csv_buffer, index=False)
    """S3 bucket initialization"""
    #print(df)
    file_name = 'team_standings.csv' 
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")
    csv_buffer2 = StringIO()
    form_df.to_csv(csv_buffer2,index=False)
    
    file_name = 'last_five_form.csv' 
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer2.getvalue(),
        ContentType='text/csv'
    )

    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")
   
def get_fixtures():
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options) 
    standingsURL = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    driver.get(standingsURL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    teams = []

    """Scrape upcoming matches for all teams"""
  
    for j in range(300,311):
        match = soup.find("tr",{"data-row": f"{j}"})
        if match:
            home_team = match.find("td",{"data-stat":"home_team"})
            home_team_text = home_team.text.strip() if home_team else "N/A"
            away_team = match.find("td",{"data-stat":"away_team"})
            away_team_text = away_team.text.strip() if away_team else "N/A"
            teams.append({"home_team":home_team_text,"away_team":away_team_text})

        
    
    df = pd.DataFrame(teams)
    df = df.drop(index=3).reset_index(drop=True)
    print(df)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=True)
    
    """S3 bucket initialization"""
    
    file_name = 'upcoming_fixtures.csv' 
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")


def main():
    
    #teams = get_standings()
    next_fixtures = get_fixtures()

if __name__ == "__main__":
    main()