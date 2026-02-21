import gradio as gr
import FRC
import FTC

# This is the main function Gradio will call when the button is pressed.
# It takes the values from the GUI elements as parameters.
def calculate_opr(gameType, eventKey, apiKey):
    try:
        if gameType == "FRC":
            # We pass the two inputs to your FRC library
            # Make sure your FRCOPR function returns the list instead of printing it!
            result = FRC.FRCOPR(eventKey, apiKey)
            return result
            
        elif gameType == "FTC":
            # We pass the two inputs to your FTC library
            result = FTC.FTCOPR(eventKey, apiKey)
            return result
            
    except Exception as e:
        # If something goes wrong, display the error in the output box
        return f"An error occurred: {str(e)}"

# Build the Gradio Interface
with gr.Blocks(theme = gr.themes.Soft()) as demo:
    gr.Markdown("# Robotics OPR Calculator")
    gr.Markdown("Select your game and provide the required inputs to calculate the Offensive Power Rating (OPR).")
    
    with gr.Row():
        # A radio button acts as a side-by-side toggle!
        game_toggle = gr.Radio(
            choices = ["FRC", "FTC"], 
            label = "Game Type", 
            value = "FRC" # Default value
        )
        
    with gr.Row():
        # The two inputs you mentioned your program needs
        # You can change the labels to be more specific (e.g., "Team Number", "Event Code")
        eventKeyBox = gr.Textbox(label = "Event Key")
        apiKeyBox = gr.Textbox(label = "API Key")
    
    gr.Markdown("Your data is not preserved. ")
        
    calculate_btn = gr.Button("Calculate", variant="primary")
    
    # The output box to display your lists
    output_display = gr.Textbox(label = "OPR List", lines=20)
    
    # Connect the button to the function, defining what goes in and what comes out
    calculate_btn.click(
        fn = calculate_opr,
        inputs = [game_toggle, eventKeyBox, apiKeyBox],
        outputs = output_display
    )

# Run the application
if __name__ == "__main__":
    demo.launch()