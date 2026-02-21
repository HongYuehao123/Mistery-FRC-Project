import numpy as np
import requests

def computeOPR(games, weighted = False):
    """
    Compute Offensive Power Rating (OPR) for teams.
    
    Parameters
    ----------
    games : list
        A list where each element is [blue_alliance, red_alliance, [blue_score, red_score]]
    """
    # 1. Collect all unique teams
    teams = sorted(set(sum([g[0] + g[1] for g in games], [])))
    team_index = {team: i for i, team in enumerate(teams)}
    n_teams = len(teams)
    n_matches = len(games) * 2
    
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
    
    # Create weights if requested
    # We use a linear scale: First match = 1.0, Last match = 3.0
    # This implies recent matches are 3x more important for the calculation
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
    # TOA API Endpoint
    url = f"https://theorangealliance.org/api/event/{event_key}/matches"
    headers = {
        "X-TOA-Key": auth_key,
        "X-Application-Origin": "OPR-Script"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def parse_toa_teams(match):
    """Helper to extract Red/Blue teams from TOA participant list."""
    blue = []
    red = []
    # TOA Stations: 11, 12 = Red | 21, 22 = Blue
    for p in match.get("participants", []):
        if p["station"] in [11, 12, 13]:
            red.append(p["team_key"])
        elif p["station"] in [21, 22, 23]:
            blue.append(p["team_key"])
    return blue, red

def totalScoreForGames(matches):
    games = []
    for m in matches:
        # Filter for Qualification matches (usually logic is simpler in TOA, checking names or levels)
        # Assuming all returned matches are valid or filtering by simple property if needed
        # Often TOA returns all, check 'match_name' contains 'Qual' or similar if strictly needed.
        # For simplicity, we process all that have scores.
        
        blue_teams, red_teams = parse_toa_teams(m)
        
        # TOA standard fields
        blue_score = m.get("blue_score", 0) - m.get('blue_penalty', 0)
        red_score = m.get("red_score", 0) - m.get('red_penalty', 0)
        
        # Basic validation to ensure match was played
        if blue_score is not None and red_score is not None and len(blue_teams) > 0:
            games.append([blue_teams, red_teams, [blue_score, red_score]])
    return games

def teleopScoreForGames(matches):
    games = []
    for m in matches:
        blue_teams, red_teams = parse_toa_teams(m)
        
        # FTC specific fields (common names, verify for specific season)
        # usually 'blue_tele_score' or 'blue_teleop_score'
        blue_score = m.get("blue_tele_score", 0)
        red_score = m.get("red_tele_score", 0)
        
        # Added check for >= 0 to handle TOA returning -1 for missing data
        if blue_score is not None and red_score is not None and blue_score >= 0 and red_score >= 0 and len(blue_teams) > 0:
            games.append([blue_teams, red_teams, [blue_score, red_score]])
    return games

def autoScoreForGames(matches):
    games = []
    for m in matches:
        blue_teams, red_teams = parse_toa_teams(m)
        
        # FTC specific fields
        blue_score = m.get("blue_auto_score", 0)
        red_score = m.get("red_auto_score", 0)
        
        if blue_score is not None and red_score is not None and len(blue_teams) > 0:
            games.append([blue_teams, red_teams, [blue_score, red_score]])
    return games

def getOPR(match, weighted, auth_key): 
    matches = get_event_scores(match, auth_key)
    
    # Filter out unplayed matches (score -1 or null) here if preferred,
    # or inside the specific ScoreForGames functions.
    
    totalScores = totalScoreForGames(matches)
    teleopScores = teleopScoreForGames(matches)
    autoScores = autoScoreForGames(matches)
    
    # For now, weighted logic is placeholder/identical as requested
    if not weighted:
        totalOPR = computeOPR(totalScores)
        teleopOPR = computeOPR(teleopScores)
        autoOPR = computeOPR(autoScores)
        print('uw')
    else:
        # Placeholder for weighted logic if different
        totalOPR = computeOPR(totalScores, True)
        teleopOPR = computeOPR(teleopScores, True)
        autoOPR = computeOPR(autoScores, True)
        print('w')
    
    return totalOPR, teleopOPR, autoOPR

def FTCOPR(match, auth_key):
    try:
        totalOPR, teleopOPR, autoOPR = getOPR(match, True, auth_key)
        result = ""

        for team, score in sorted(totalOPR.items(), key=lambda x: -x[1]):
            totalScore = totalOPR.get(team, 0)
            teleopScore = teleopOPR.get(team, 0)
            autoScore = autoOPR.get(team, 0)
            result += f"Team {team}: totalOPR = {totalScore:.2f}, teleopOPR = {teleopScore:.2f}, autoOPR = {autoScore:.2f} \n"

        return result

    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure you have entered a valid TOA API Key and Event Key.")