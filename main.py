import os
import functions_framework
from dotenv import load_dotenv
import requests
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.auth import default

load_dotenv()

RIOT_API = os.getenv("RIOT_API")
SPREADSHEET_ID= os.getenv("SPREADSHEET_ID")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_player_matches(puuid, count, queueType):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queueType}&type=ranked&start=0&count={count}&api_key={RIOT_API}"
    response = requests.get(url)

    return response.json()

def get_match_data(matchId):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{matchId}?api_key={RIOT_API}"
    response = requests.get(url)

    return response.json()

def convert_puuid_to_name(puuid):
    if puuid == "y7RTO_ECjXKFmpO6Ssw0cAbSMXuUPx_SB0-XzjatRIrcPvESu0lm2aukanE9AO4GStuXB95sVKGV7w":
        return "Emil"
    elif puuid == "B-tHVanUdin_WuXhXLv1XnOHeNz3Yl3sh7IRBIQDgEzzHUSlGoH3PzBN6B2bdAZzjHCyTKHnx2OG8Q":
        return "Erste"
    elif puuid == "rBOd_qwBPrwO1Ns_wghrUYEaENhEeEfA7wk0FJ9UJQK7sSVGZ2Qnn8czdv84KlIN-vS4KiaLFgUTNw":
        return "Ollie"

def filter_match_data(puuid, matchData):
    playerData = matchData["info"]["participants"]

    filteredMatchData = {}
    filteredMatchData["date"] = matchData["info"]["gameCreation"]
    filteredMatchData["gameLength"] = matchData["info"]["gameDuration"]
    for x in playerData:
        if x["puuid"] == puuid:
            filteredMatchData["puuid"] = x["puuid"]
            filteredMatchData["name"] = x["riotIdGameName"]
            filteredMatchData["champion"] = x["championName"]
            filteredMatchData["role"] = x["teamPosition"]
            filteredMatchData["result"] = x["win"]
            filteredMatchData["team"] = x["teamId"]
            filteredMatchData["kills"] = x["kills"]
            filteredMatchData["deaths"] = x["deaths"]
            filteredMatchData["assists"] = x["assists"]

            filteredMatchData["cs"] = x["totalMinionsKilled"] + x["neutralMinionsKilled"]
            break
           
           
           
    for x in playerData:
        if filteredMatchData["role"] == x["teamPosition"] and filteredMatchData["team"] != x["teamId"]:
            filteredMatchData["opponentChampion"] = x["championName"]
        if x["teamPosition"] == "JUNGLE" and filteredMatchData["team"] == x["teamId"]:
            filteredMatchData["jungler"] = x["championName"]
        if x["teamPosition"] == "BOTTOM" and filteredMatchData["team"] == x["teamId"]:
            filteredMatchData["bottom"] = x["championName"]
        if x["teamPosition"] == "UTILITY" and filteredMatchData["team"] == x["teamId"]:
            filteredMatchData["support"] = x["championName"]

        if x["teamPosition"] == "JUNGLE" and filteredMatchData["team"] != x["teamId"]:
            filteredMatchData["opponentJungler"] = x["championName"]
        if x["teamPosition"] == "BOTTOM" and filteredMatchData["team"] != x["teamId"]:
            filteredMatchData["opponentBottom"] = x["championName"]
        if x["teamPosition"] == "UTILITY" and filteredMatchData["team"] != x["teamId"]:
            filteredMatchData["opponentSupport"] = x["championName"]

    return filteredMatchData

def get_sheets():
    # creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

    creds, _ = default(scopes=SCOPES)
    # service = build("sheets", "v4", credentials=creds)

    client = gspread.authorize(creds)
    workbook = client.open_by_key(SPREADSHEET_ID)
    return workbook

def write_data_to_sheet(puuid, data):
    name = convert_puuid_to_name(puuid)
    name = name + "_data"

    time = (datetime.fromtimestamp(data["date"]//1000)
      .strftime('%d-%m-%Y'))

    workbook = get_sheets()
    sheet = workbook.worksheet(name)

    row = 2
    while(sheet.acell(f"A{row}").value):
        row += 1

    cellList = sheet.range(f"A{row}:P{row}")
    cellList[0].value = data["date"]
    cellList[1].value = data["result"]
    cellList[2].value = data["champion"]
    cellList[3].value = data["opponentChampion"]
    cellList[4].value = data["kills"]
    cellList[5].value = data["deaths"]
    cellList[6].value = data["assists"]
    cellList[7].value = data["jungler"]
    cellList[8].value = data["bottom"]
    cellList[9].value = data["support"]
    cellList[10].value = data["opponentJungler"]
    cellList[11].value = data["opponentBottom"]
    cellList[12].value = data["opponentSupport"]
    cellList[13].value = data["cs"]
    cellList[14].value = data["gameLength"]
    cellList[15].value = data["role"]
    sheet.update_cells(cellList)

def get_last_cell_date(puuid):
    name = convert_puuid_to_name(puuid)
    name = name + "_data"

    workbook = get_sheets()
    sheet = workbook.worksheet(name)
    row = 2
    while(sheet.acell(f"A{row+1}").value):
        row += 1
    
    return sheet.acell(f"A{row}").value

NAMES = {
    "Emil": "y7RTO_ECjXKFmpO6Ssw0cAbSMXuUPx_SB0-XzjatRIrcPvESu0lm2aukanE9AO4GStuXB95sVKGV7w",
    "Erste": "B-tHVanUdin_WuXhXLv1XnOHeNz3Yl3sh7IRBIQDgEzzHUSlGoH3PzBN6B2bdAZzjHCyTKHnx2OG8Q",
    "Ollie": "rBOd_qwBPrwO1Ns_wghrUYEaENhEeEfA7wk0FJ9UJQK7sSVGZ2Qnn8czdv84KlIN-vS4KiaLFgUTNw"
}

def main(name):
    matches = get_player_matches(NAMES[name], 6, 420)
    if matches:
        print(matches)
        matches.reverse()
    last = get_last_cell_date(NAMES[name])
    if last == None:
        last = 0
    for match in matches:
        data = get_match_data(match)
        if data["info"]["gameCreation"] <= int(last): 
            continue
        filteredData = filter_match_data(NAMES[name], data)
        write_data_to_sheet(NAMES[name], filteredData)

@functions_framework.http
def run_http(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "name" in request_json:
        name = request_json["name"]
    elif request_args and "name" in request_args:
        name = request_args["name"]
    else:
        name = 'World'

    if name == "Emil" or name == "Erste" or name == "Ollie":
        print("____________________________________")
        print(RIOT_API)
        main(name)

    if name == "Check":
        name = RIOT_API

    return 'Hello {}!'.format(name)