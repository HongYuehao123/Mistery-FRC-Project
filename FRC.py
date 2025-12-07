import numpy as np
import requests

def computeOPR(games, weighted = False):
    """
    Compute Offensive Power Rating (OPR) for FRC teams from match data.
    
    Parameters
    ----------
    games : list
        A list where each element is [blue_alliance, red_alliance, [blue_score, red_score]]
        Example:
        [
            [["254","1678","1323"], ["2056","1114","118"], [120, 115]],
            [["1678","2056","971"], ["254","1114","148"], [135, 125]]
        ]
    
    Returns
    -------
    dict
        Dictionary mapping each team -> OPR (float)
    """
    # 1. Collect all unique teams
    teams = sorted(set(sum([g[0] + g[1] for g in games], [])))
    team_index = {team: i for i, team in enumerate(teams)}
    n_teams = len(teams)
    n_matches = len(games) * 2  # each match contributes two alliance entries
    
    # 2. Build matrix A and score vector s
    A = np.zeros((n_matches, n_teams))
    s = np.zeros(n_matches)
    
    row = 0
    for blue, red, (blue_score, red_score) in games:
        for team in blue:
            A[row, team_index[team]] = 1
        s[row] = blue_score
        row += 1
        for team in red:
            A[row, team_index[team]] = 1
        s[row] = red_score
        row += 1
    
    if weighted:
        # We have n_matches (blue + red rows), but they come in pairs from the same game.
        # We want the game index to drive the weight.
        game_weights = np.linspace(1.0, 3.0, len(games))
    else:
        game_weights = np.ones(len(games))

    row = 0
    for i, (blue, red, (blue_score, red_score)) in enumerate(games):
        # Calculate the square root of the weight for the least squares transform
        # (Weighted Least Squares solves sqrt(W) * A * x = sqrt(W) * s)
        w = np.sqrt(game_weights[i])
        
        # Blue Alliance Row
        for team in blue:
            A[row, team_index[team]] = 1 * w
        s[row] = blue_score * w
        row += 1
        
        # Red Alliance Row
        for team in red:
            A[row, team_index[team]] = 1 * w
        s[row] = red_score * w
        row += 1
    
    
    # 3. Solve least squares A x = s
    x, _, _, _ = np.linalg.lstsq(A, s, rcond=None)
    
    # 4. Map results back to teams
    opr = {team: x[i] for team, i in team_index.items()}
    
    return opr

def get_event_scores(event_key, auth_key):
    url = f"https://www.thebluealliance.com/api/v3/event/{event_key}/matches"
    headers = {"X-TBA-Auth-Key": auth_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def totalScoreForGames(matches):
    games = []
    for m in matches:
        if m["comp_level"] != "qm":
            continue
        
        blue = [t[3:] for t in m["alliances"]["blue"]["team_keys"]]  # remove 'frc'
        red = [t[3:] for t in m["alliances"]["red"]["team_keys"]]
        blue_score = m["alliances"]["blue"]["score"] - m["score_breakdown"]["blue"]["foulPoints"]
        red_score = m["alliances"]["red"]["score"] - m["score_breakdown"]["blue"]["foulPoints"]
        if blue_score != -1 and red_score != -1:  # ignore unplayed matches
            games.append([blue, red, [blue_score, red_score]])
    return games

def teleopScoreForGames(matches):
    games = []
    for m in matches:
        if m["comp_level"] != "qm":
            continue

        blue = [t[3:] for t in m["alliances"]["blue"]["team_keys"]]  # remove 'frc'
        red = [t[3:] for t in m["alliances"]["red"]["team_keys"]]
        blue_score = m["score_breakdown"]["blue"]["teleopCoralPoints"]
        red_score = m["score_breakdown"]["red"]["teleopCoralPoints"]
        if blue_score != -1 and red_score != -1:  # ignore unplayed matches
            games.append([blue, red, [blue_score, red_score]])
    return games

def autoScoreForGames(matches):
    games = []
    for m in matches:
        if m["comp_level"] != "qm":
            continue
        
        blue = [t[3:] for t in m["alliances"]["blue"]["team_keys"]]  # remove 'frc'
        red = [t[3:] for t in m["alliances"]["red"]["team_keys"]]
        blue_score = m["score_breakdown"]["blue"]["autoPoints"]
        red_score = m["score_breakdown"]["red"]["autoPoints"]
        if blue_score != -1 and red_score != -1:  # ignore unplayed matches
            games.append([blue, red, [blue_score, red_score]])
    return games

def getOPR(match, weighted): 
    matches = get_event_scores(match, auth_key)
    totalScores = totalScoreForGames(matches)
    teleopScores = teleopScoreForGames(matches)
    autoScores = autoScoreForGames(matches)
    #Unweighted
    if not weighted:
        totalOPR = computeOPR(totalScores)
        teleopOPR = computeOPR(teleopScores)
        autoOPR = computeOPR(autoScores)
        print('uw')

    #Weighted
    else:
        totalOPR = computeOPR(totalScores, True)
        teleopOPR = computeOPR(teleopScores, True)
        autoOPR = computeOPR(autoScores, True)
        print('w')
    
    return totalOPR, teleopOPR, autoOPR

match = "2025paca"
auth_key = 'utzEfVnhAbe9j7VlhxMggWg1XNvII1LZ6wBZm3mKwsBiBCfBimG8htWdQTAqIVU3'

try:
    totalOPR, teleopOPR, autoOPR = getOPR(match, True)

    for team, score in sorted(totalOPR.items(), key=lambda x: -x[1]):
        totalScore = totalOPR.get(team, 0)
        teleopScore = teleopOPR.get(team, 0)
        autoScore = autoOPR.get(team, 0)
        print(f"Team {team}: totalOPR = {totalScore:.2f}, teleopOPR = {teleopScore:.2f}, autoOPR = {autoScore:.2f}")

except Exception as e:
    print(f"Error: {e}")
    print("Please ensure you have entered a valid TBA API Key and Event Key.")