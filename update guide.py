#!/usr/bin/env python3
"""
Updates the guide.
Takes the data from botc.txt
Injects the appropriate HTML tags and tries to make it pretty.
Output is an updated BotC Guide.html file
"""

from bs4 import BeautifulSoup
import re
import json
import sys
 
import os
import shutil
from datetime import datetime

# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pip install yattag
from yattag import indent as yattag_indent



def check_file_format(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()

            # Extract file name from the path
            file_name = file_path.split("/")[-1]

            # Initialize an empty string to store first letters
            first_letters = ""

            for line_number, line in enumerate(lines, start=1):

                # Check if the line is not empty
                if line:
                    first_char = line[0]

                    # Skip lines that don't start with Q or A
                    if first_char not in {'Q', 'A'}:
                        continue

                    # Check for incorrect formatting
                    if first_char == 'A' and 'Q' not in first_letters:
                        print(f"{file_name} is incorrectly formatted: 'A' detected before 'Q' on line {line_number}.")
                        return False
                    elif first_letters and first_char == first_letters[-1]:
                        print(f"{file_name} is incorrectly formatted: '{first_char}' detected after another '{first_char}' on line {line_number}.")
                        return False

                    # Add the first character to the string
                    first_letters += first_char

            # Check if the last letter is 'A'
            if first_letters and first_letters[-1] == 'A':
                print(f"{file_name} is correctly formatted.")
                return True
            else:
                print(f"{file_name} is incorrectly formatted: Missing 'A' at the end.")
                return False

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False


def manage_backups(filename):
    # Define the original and backup file names
    #html_file = "foo.html"
    max_backups = 5

    # Check if foo.html exists
    if os.path.exists(filename):
        print(f"{filename} exists.")

        # Get the list of existing backup files
        backup_files = [f for f in os.listdir() if f.startswith(f"Back up of {filename.split('.')[0]}")]

        # Check the number of existing backup files
        if len(backup_files) >= max_backups:
            # Sort backup files by creation time and delete the oldest one
            backup_files.sort(key=lambda x: os.path.getctime(x))
            oldest_backup = backup_files[0]
            os.remove(oldest_backup)
            print(f"Deleted the oldest backup file: {oldest_backup}")

        # Create a new backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"Back up of {filename.split('.')[0]}-{timestamp}.html"



        # Make a copy of foo.html with the new backup filename
        shutil.copy(filename, backup_filename)
        print(f"Created backup: {backup_filename}")

    else:
        print(f"{filename} does not exist.")



# Surround keywords with <span class='character'></span>
def surround_keywords_with_span(html_content, keywords, character_type):
    soup = BeautifulSoup(html_content, 'html.parser')

    for keyword in keywords:
        print("Highlighting: " + keyword + "                               ", end='\r')
        # Find all occurrences of the keyword in the HTML content
        matches = soup.find_all(string=re.compile(r'\b' + re.escape(keyword) + r'\b'))

        # Loop through each match and surround with <span class='character'>
        for match in matches:
            content = str(match)
            replaced_content = re.sub(r'\b' + re.escape(keyword) + r'\b', f'<span class="{character_type}">{keyword}</span>', content)
            #print(replaced_content)
            match.replace_with(BeautifulSoup(replaced_content, 'html.parser'))
    return str(soup)


def botc_to_nodes(input_path, output_path):
    output_lines = []

    answer_mode = False
    in_list = False
    in_ordered_list = False
    in_list_item = False
    first_question = True
    id = 0
    with open(input_path, 'r', encoding="utf-8") as file:
        for line in file:
            # blank lines separate question and answer blocks and list items so need to handle this
            if line.strip() == '':
                if in_list:
                    output_lines.append(  '</ul>' )
                    in_list = False
                    continue
                elif in_ordered_list:
                    output_lines.append(  '</ol>' )
                    in_ordered_list = False
                    continue

                if not answer_mode:
                    continue
                else:
                    # Answers are divided into paragraphs for clarity
                    output_lines.append('        </div>\n')   # close paragraph
                    output_lines.append('        <div>')      # open paragraph


            # question time (or pair or jinx or hate jinx for now)
            if line.startswith('Q ') or line.startswith('P ') or line.startswith('H ') or line.startswith('J '):
                if first_question:
                    first_question = False
                else:
                    output_lines.append('        </div>\n')   # close paragraph
                    output_lines.append('      </div>\n')     # close answer
                    output_lines.append('    </div>\n')       # close node

                answer_mode = False
                
                id += 1

                output_lines.append('    <div class="node">\n')  # open node
                if line.startswith('Q '):
                    line = '      <div class="question">' + line[2:]   # open question
                elif line.startswith('P '):
                    line = '      <div class="question interesting-interaction">' + line[2:] # open interaction
                elif line.startswith('H '):
                    line = '      <div class="question hate-jinx">' + line[2:] # open interaction
                else:
                    line = '      <div class="question jinx">' + line[2:] # open interaction
            elif line.startswith('A '):
                answer_mode = True
                output_lines.append('      </div>\n')              # close question
                line = '      <div class="answer">\n        <div>' + line[2:]     # open answer and open first paragraph
            elif line.startswith('I '):
                answer_mode = True
                output_lines.append('      </div>\n')               # close interaction 
                line = '      <div class="answer interaction-description">\n        <div>' + line[2:]  # open description and first paragraph
            elif line.startswith('D '):
                answer_mode = True
                output_lines.append('      </div>\n')               # close interaction 
                line = '      <div class="answer jinx-description">\n        <div>' + line[2:]  # open description and first paragraph

            # skip comments
            elif line.startswith('=') or line.startswith('--') or line.startswith(':'):
                line = ''

            # ordered_list
            elif line.strip().startswith('#'):
                if not in_ordered_list:
                    output_lines.append('<ol><li>')
                    in_ordered_list = True
                    in_list_item = True
                elif in_list_item:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("#","",1)+"<br>")
            
            # unordered list
            elif line.strip().startswith('*'):
                if not in_list:
                    output_lines.append('<ul><li>')
                    in_list = True
                    in_list_item = True
                elif in_list_item:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("*","",1)+"<br>")
                
            # handle paragraphing within lists
            elif in_list:
                output_lines.append(line)
                output_lines.append("<br>")
            elif in_ordered_list:
                output_lines.append(line)
                output_lines.append("<br>")

            if not in_list:
                if not in_ordered_list:
                    output_lines.append(line)

    print("Processed " + str(id) + " nodes")
    print("Cleaning up blank lines")
    cleaned_lines = []
    prev_line_empty = False
    for line in output_lines:
        if line.strip() == '':
            if not prev_line_empty:
                cleaned_lines.append(line)
            prev_line_empty = True
        else:
            cleaned_lines.append(line)
            prev_line_empty = False

    output_lines = []
    i = 0
    while i < len(cleaned_lines):
        if cleaned_lines[i].strip() == '' and i + 1 < len(cleaned_lines) and cleaned_lines[i + 1].strip() == '</div>':
            i += 0
        else:
            output_lines.append(cleaned_lines[i])
        i += 1


    with open(output_path, 'w', encoding="utf-8") as file:
        file.writelines(output_lines)


def replace_nodes(original, replacement, output_path):
    print("Finding existing version of guide")
    with open(original, 'r', encoding="utf-8") as file:
        html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        vault = soup.find('div', id='vault')
    
    # Read the content of the replacement html
    with open(replacement, 'r', encoding="utf-8") as file:
        replacement_content = file.read()

    # Parse the replacement content and remove empty paragraphs
    print("Removing empty divs")
    replacement_soup = BeautifulSoup(replacement_content, 'html.parser')
    for p_tag in replacement_soup.find_all('div'):
        if not p_tag.text.strip():  # Check if the paragraph has only whitespace
            p_tag.extract()  # Remove the empty paragraph

    print("Updating HTML")
    if vault:
        vault.clear()
        vault.append(replacement_soup)

    with open(output_path, 'w', encoding="utf-8") as file:
        file.write(str(soup))

def highlight_roles(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        current_contents = file.read()

    # Update the HTML content with keyword replacements
    current_contents = surround_keywords_with_span(current_contents, Fabled, "Fabled")
    current_contents = surround_keywords_with_span(current_contents, Townsfolk, "Townsfolk")
    current_contents = surround_keywords_with_span(current_contents, Outsider, "Outsider")
    current_contents = surround_keywords_with_span(current_contents, Minion, "Minion")
    current_contents = surround_keywords_with_span(current_contents, Demon, "Demon")
    current_contents = surround_keywords_with_span(current_contents, Traveller, "Traveller")

    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(current_contents)

def update_index(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script')

    # Extract the JavaScript code from the <script> tag
    javascript_code = script_tag.string.strip()

    # Locate the 'keywords' dictionary in the JavaScript code
    start_index = javascript_code.find("var keywords = {") + len("var keywords = {")
    end_index = javascript_code.find("};", start_index) + 1
    roles_dict_str = javascript_code[start_index-1:end_index]



    sorted_keywords = {}



    # Sort names by first letter and populate the dictionary
    for name in sorted(all_the_words):
        first_letter = name[0].upper()
        if first_letter not in sorted_keywords:
            sorted_keywords[first_letter] = [name]
        else:
            sorted_keywords[first_letter].append(name)

    for key in sorted_keywords:
        sorted_keywords[key] = sorted(sorted_keywords[key])
     
    new_keyword_count = 0
    for key, value in sorted_keywords.items():
        new_keyword_count += len(value)


#
    print(f"Added {new_keyword_count} keywords to index")

    # Print the sorted dictionary
    #for key, value in sorted_keywords.items():
    #    print(f"{key}: {value}")
    
    # Convert the new dictionary to a JSON string
    new_keywords_dict_str = json.dumps(sorted_keywords, indent=2)

    # Replace the old 'roles' dictionary string with the new one
    javascript_code = javascript_code.replace(roles_dict_str, new_keywords_dict_str)

    # Update the <script> tag with the modified JavaScript code
    script_tag.string = javascript_code

    # Write the updated HTML back to the file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

def indent(input_path, output_path):
    with open(input_path, 'r', encoding="utf-8") as file:
        html = file.read()

    nicely_indented = str(yattag_indent(html))
    fixed_spans = nicely_indented.replace("</span><span", "</span> <span")

    with open(output_path, 'w', encoding="utf-8") as file:
        file.write(fixed_spans)

def emphasise(input_file, output_file):
    # Read the HTML file
    with open(input_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Define a regex pattern to find words surrounded by underscores
    pattern = re.compile(r'(_)(\w+)(_)')

    # Replace matched patterns with <em> tags and without underscores
    modified_html = pattern.sub(lambda match: f'<em>{match.group(2)}</em>', html_content)

    # Write the modified HTML to the output file
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(modified_html)






# List of keywords to highlight

Townsfolk =  [ "Steward", "Knight", "Noble", "Investigator", "Chef"]
Townsfolk += [ "Washerwoman", "Clockmaker", "Librarian", "Grandmother"]
Townsfolk += [ "Pixie", "Bounty Hunter", "Empath", "High Priestess", "Sailor"]
Townsfolk += [ "General", "Preacher", "Chambermaid", "Balloonist", "King"]
Townsfolk += [ "Dreamer", "Fortune Teller", "Mathematician", "Snake Charmer"]
Townsfolk += [ "Cult Leader", "Flowergirl", "Town Crier", "Oracle"]
Townsfolk += [ "Undertaker", "Innkeeper", "Gambler", "Monk", "Lycanthrope"]
Townsfolk += [ "Exorcist", "Gossip", "Savant", "Amnesiac", "Juggler"]
Townsfolk += [ "Nightwatchman", "Engineer", "Artist", "Courtier", "Fisherman"]
Townsfolk += [ "Slayer", "Professor", "Seamstress", "Philosopher", "Huntsman",]
Townsfolk += [ "Soldier", "Fool", "Pacifist", "Alchemist", "Tea Lady", "Sage"]
Townsfolk += [ "Farmer", "Magician", "Ravenkeeper", "Choirboy", "Virgin"]
Townsfolk += [ "Poppy Grower", "Minstrel", "Mayor", "Atheist", "Cannibal"]

Outsider  =  [ "Snitch", "Butler", "Goon", "Acrobat"]
Outsider  += [ "Puzzlemaster", "Tinker", "Saint", "Sweetheart"]
Outsider  += [ "Plague Doctor", "Recluse", "Mutant", "Heretic"]
Outsider  += [ "Damsel", "Klutz", "Drunk", "Golem", "Moonchild"]
Outsider  += [ "Barber", "Politician", "Lunatic", "Hatter"]

Minion     = [ "Godfather", "Widow", "Poisoner", "Devil's Advocate"]
Minion    += [ "Harpy", "Witch", "Spy", "Cerenovus", "Fearmonger", "Pit-Hag"]
Minion    += [ "Psychopath", "Assassin", "Baron", "Mezepheles", "Goblin"]
Minion    += [ "Scarlet Woman", "Mastermind", "Evil Twin", "Boomdandy"]
Minion    += [ "Marionette", "Organ Grinder", "Vizier"]

Demon      = [ "Pukka", "Lil Monsta", "Lleech", "No Dashii", "Imp"]
Demon     += [ "Shabaloth", "Po", "Zombuul", "Al-Hadikhia", "Vigormortis"]
Demon     += [ "Fang Gu", "Vortox", "Legion", "Leviathan", "Riot", "Kazali"]

Traveller  = [ "Bureaucrat", "Thief", "Gunslinger", "Scapegoat", "Beggar"]
Traveller += [ "Apprentice", "Matron", "Judge", "Bishop", "Voudon", "Barista"]
Traveller += [ "Harlot", "Butcher", "Deviant", "Bone Collector", "Gangster"]

Fabled     = [ "Revolutionary", "Fiddler", "Toymaker", "Fibbin", "Bootlegger"]
Fabled    += [ "Spirit of Ivory", "Hell's Librarian", "Djinn", "Duchess"]
Fabled    += [ "Storm Catcher", "Sentinel", "Doomsayer", "Angel", "Buddhist"] 
Fabled    += [ "Ferryman", "Gardener"] 



# All the keywords that are not the names of characters
Extra  = [ "poisoned", "drunk", "townsfolk", "outsider", "fabled", "traveller"]
Extra += [ "demon", "minion", "droisoned","good","evil","nomination","execution","preached", "protect"]
Extra += [ "misregister", "sober", "healthy", "alignment", "jinx", "resurrect"]
Extra += [ "madness", "setup", "alive", "dead", "vote" ]
all_the_words = Townsfolk + Outsider + Minion + Demon + Traveller + Fabled + Extra





print("Starting update.")

print("Checking BotC.txt")
if not check_file_format('BotC.txt'):
  sys.exit("..Oh dear!")

manage_backups("BotC Guide.html")

botc_to_nodes('BotC.txt', 'nodefied content.txt')
print("Done nodifying text")

replace_nodes('BotC Guide.html', 'nodefied content.txt', 'nodified content.html')

print("Updating index")
update_index('nodified content.html', 'updated index.html')

print("Highlighting roles")
highlight_roles('updated index.html', 'highlighted.html')
print("Done highlighting.                                                              ")





print("Prettifying ...")
indent('rough.html', 'guide.html')


print("Adding emphasis ...")
emphasise("guide.html", "BotC Guide.html")


print("Done updating.")



