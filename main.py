from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import boto3

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

def get_form():
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options)
    URL = f"https://www.flashscoreusa.com/{sport}/{country}/{league}/results/"
    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    matches = []

    """Scrape all information of team form for past 5 days"""

    for match in soup.find_all("div", class_="event__match event__match--withRowLink event__match--static event__match--twoLine"):
        home_team = match.find("div", class_="wcl-participant_7lPCX event__homeParticipant").text
        away_team = match.find("div", class_="wcl-participant_7lPCX event__awayParticipant").text
        home_score= match.find("div", class_="event__score event__score--home").text
        away_score = match.find("div", class_="event__score event__score--away").text
      
        matches.append({"Home Team": home_team, "Away Team": away_team, "Home Score ": home_score,"Away Score":away_score})

    """convert to panda"""
    df = pd.DataFrame(matches)
    #print(df)

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

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
    service = Service("/usr/bin/chromedriver")  
    driver = webdriver.Chrome(service=service, options=options)
    standingsURL = "https://www.flashscoreusa.com/soccer/spain/laliga/standings/#/dINOZk9Q/table/overall"
    driver.get(standingsURL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    teams = []

    """Scrape all the standings information for all teams in the current league web page"""

    for team in soup.find_all("div",class_="ui-table__row"):
        position = team.find("div",class_="tableCellRank").text.rstrip(".")
        name = team.find("a",class_="tableCellParticipant__name").text
        played = team.find_all("span",class_="table__cell table__cell--value")[0].text
        won = team.find_all("span",class_="table__cell table__cell--value")[1].text
        tied  = team.find_all("span",class_="table__cell table__cell--value")[2].text
        lost =  team.find_all("span",class_="table__cell table__cell--value")[3].text
        goals = team.find("span", class_="table__cell table__cell--value table__cell--score").text
        goal_difference = team.find("span", class_="table__cell table__cell--value table__cell--goalsForAgainstDiff").text
        points = team.find("span",class_="table__cell table__cell--value table__cell--points").text
        team_cells = team.find_all("div", class_="tableCellFormIcon wcl-trigger_YhU1j")
        present_form = [team_cells[i].text for i in range(5)]
        teams.append({"Position":position,"Team Name":name,"Played":played,"Won":won,"Tied":tied, "Lost":lost,"Scored:Conceded":goals, "Goal Difference":goal_difference,"Total Points":points, "Form":present_form})
        #print(f"{position},{name},{played},{won},{tied},{lost},{goals},{goal_difference},{points}")
        #return None

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
    #print(df)
def main():
    #posts = get_form()
    teams = get_standings()
    

if __name__ == "__main__":
    main()