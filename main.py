from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import boto3
from soccer_data_api import SoccerDataAPI
from collections import defaultdict

s3 = boto3.client('s3')

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


def get_form():
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options)
    URL = f"https://www.flashscoreusa.com/{sport}/{country}/{league}/results/"
    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    matches = []
    team_form = defaultdict(list)
    """Scrape all information of team form for past 5 days"""

    for match in soup.find_all("div", class_="event__match event__match--withRowLink event__match--static event__match--twoLine"):
        home_team = match.find("div", class_="wcl-participant_7lPCX event__homeParticipant").text
        away_team = match.find("div", class_="wcl-participant_7lPCX event__awayParticipant").text
        home_score= match.find("div", class_="event__score event__score--home").text
        away_score = match.find("div", class_="event__score event__score--away").text
        home_team = ''.join(filter(str.isalpha,home_team))
        away_team = ''.join(filter(str.isalpha, away_team))
        matches.append({"home_team": home_team, "away_team": away_team, "home_score": home_score,"away_score":away_score})
        #print(f'{home_team} {home_score} - {away_score} {away_team}')
        if home_score > away_score:
            home_result, away_result = 1, -1
        elif home_score < away_score:
            home_result, away_result = -1, 1
        else:
            home_result, away_result = 0, 0
        
        #print(f"{home_team}, {away_team}")
        team_form[home_team].append(home_result)
        team_form[away_team].append(away_result)
        team_form[home_team] = team_form[home_team][:5]
        team_form[away_team] = team_form[away_team][:5]
    
    #print(matches)

    """convert to panda"""
    df = pd.DataFrame.from_dict(team_form,orient="index")
    
    df=df.sort_index()

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=True, header=False)
    
    """S3 bucket initializer"""
    bucket_name = 'soccer-predictor-web-scrape' 
    file_name = 'last_five_form.csv' 
    
    
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")
    #print(df)

def get_standings():
    
    standings = SoccerDataAPI()
    
    teams = standings.la_liga()
    
    df = pd.DataFrame(teams)
    
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    """S3 bucket initialization"""
    bucket_name = 'soccer-predictor-web-scrape' 
    file_name = 'team_standings.csv' 
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )

    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")
   
def get_fixtures():
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options) 
    standingsURL = f"https://www.flashscoreusa.com/{sport}/{country}/{league}/fixtures/"
    driver.get(standingsURL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    teams = []

    """Scrape upcoming matches for all teams"""
    for match in soup.find_all("div","event__match event__match--withRowLink event__match--static event__match--scheduled event__match--twoLine")[:10]:
       
        home_team = match.find("div","wcl-participant_7lPCX event__homeParticipant").text 
        away_team = match.find("div","wcl-participant_7lPCX event__awayParticipant").text
        teams.append({"home_team":home_team, "away_team":away_team})
    df = pd.DataFrame(teams)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    
    """S3 bucket initialization"""
    bucket_name = 'soccer-predictor-web-scrape' 
    file_name = 'upcoming_fixtures.csv' 
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    print(f"Successfully uploaded to s3://{bucket_name}/{file_name}")


def main():
    posts = get_form()
    teams = get_standings()
    next_fixtures = get_fixtures()

if __name__ == "__main__":
    main()