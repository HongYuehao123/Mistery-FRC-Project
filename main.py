import FRC, FTC

def calculateOPR(gameType):
    # 1. Check if the game type is valid FIRST
    if gameType not in ["FRC", "FTC"]:
        # 2. We explicitly RAISE an error here so main() can catch it!
        raise ValueError("Invalid game type")
        
    # Only ask for keys if the game type was valid
    eventKey = input("Enter the Event Key: ")
    apiKey = input("Enter the API Key: ")
    
    if gameType == "FRC":
        return FRC.FRCOPR(eventKey, apiKey)
    elif gameType == "FTC":
        return FTC.FTCOPR(eventKey, apiKey)

def main():
    runningError = 0

    while runningError < 3:
        FTCOrFRC = input("Calculating for FRC or FTC: ")
        
        try:
            result = calculateOPR(FTCOrFRC)
            print(result)
            break 

        except ValueError:
            print("Please make sure you specify which game your are checking.")
            runningError += 1
            
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            runningError += 1

    if runningError == 3:
        print("Wrong for too many times, exiting ...")

main()