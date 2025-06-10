# I want to create a cli that helps me add entries to a dataset file using the Dataset class defined in the dataset.py script.
# The cli will be invoked with the command uv run mat-dat add
# where add is the specific command that will start an interactive section with the user. 
# In this section the user will be prompted to insert the required information to add a new entry to the dataset. 
# The input process will be split in two phases: one for inserting the Email Content and one for inserting the expected Action Item. 
# At the end of each phace, the respective object will be built to check the validity of the provided data and a summary of the created object will be shown to the user for confirmation. If the user confirms typing "y" the next phase will start. 
# When the insertion of the Action Item is completed, the new entry is stored in the dataset and the process ends. 
# To implement this feature split it into components according to the solid principles.
# Make the terminal user interface appealing, you could use https://github.com/Textualize/textual to make the ui appealing. 
# Use click for defining the cli script AI!
