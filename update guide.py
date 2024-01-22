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

 
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pip install yattag
from yattag import indent






# Function to surround keywords with <span class='character'></span>
def surround_keywords_with_span(html_content, keywords, character_type):
    soup = BeautifulSoup(html_content, 'html.parser')

    for keyword in keywords:
        print("Highlighting: " + keyword)
        # Find all occurrences of the keyword in the HTML content
        matches = soup.find_all(string=re.compile(r'\b' + re.escape(keyword) + r'\b'))

        # Loop through each match and surround with <span class='character'>
        for match in matches:
            content = str(match)
            replaced_content = re.sub(r'\b' + re.escape(keyword) + r'\b', f'<span class="{character_type}">{keyword}</span>', content)
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
                    in_list = False;
                    continue
                elif in_ordered_list:
                    output_lines.append(  '</ol>' )
                    in_ordered_list = False;
                    continue

                if not answer_mode:
                    continue
                else:
                    # Answers are divided into paragraphs for clarity
                    output_lines.append('        </div>\n')   # close paragraph
                    output_lines.append('        <div>')      # open paragraph


            # question time
            if line.startswith('Q ') or line.startswith('P ') or line.startswith('H ') or line.startswith('J '):
                if first_question:
                    first_question = False
                    print("First:" + line)
                else:
                    output_lines.append('        </div>\n')   # close paragraph
                    output_lines.append('      </div>\n')     # close answer
                    output_lines.append('    </div>\n')       # close node

                answer_mode = False;
                
                id += 1
                print("Node " + str(id))
                output_lines.append('    <div class="node" id="' + str(id) + '">\n')  # open node
                if line.startswith('Q '):
                    line = '      <div class="question">' + line[2:]   # open question
                elif line.startswith('P '):
                    line = '      <div class="question interesting-interaction">' + line[2:] # open interaction
                elif line.startswith('H '):
                    line = '      <div class="question hate-jinx">' + line[2:] # open interaction
                else:
                    line = '      <div class="question jinx">' + line[2:] # open interaction
            elif line.startswith('A '):
                answer_mode = True;
                output_lines.append('      </div>\n')              # close question
                line = '      <div class="answer">\n        <div>' + line[2:]     # open answer and open first paragraph
            elif line.startswith('I '):
                answer_mode = True;
                output_lines.append('      </div>\n')               # close interaction 
                line = '      <div class="answer interaction-description">\n        <div>' + line[2:]  # open description and first paragraph
            elif line.startswith('D '):
                answer_mode = True;
                output_lines.append('      </div>\n')               # close interaction 
                line = '      <div class="answer jinx-description">\n        <div>' + line[2:]  # open description and first paragraph


            elif line.startswith('='):
                line = ''
            elif line.startswith('--'):
                line = ''
            elif line.startswith(':'):
                line = ''
            # in_ordered_list
            elif line.strip().startswith('#'):
                if not in_ordered_list:
                    output_lines.append('<ol><li>')
                    in_ordered_list = True
                    in_list_item = True
                elif in_list_item:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("#","",1)+"<br>")
            elif line.strip().startswith('*'):
                if not in_list:
                    output_lines.append('<ul><li>')
                    in_list = True
                    in_list_item = True
                elif in_list_item:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("*","",1)+"<br>")
            elif in_list:
                output_lines.append(line)
                output_lines.append("<br>")
            elif in_ordered_list:
                output_lines.append(line)
                output_lines.append("<br>")
            if not in_list:
                if not in_ordered_list:
                    output_lines.append(line)

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



botc_to_nodes('BotC.txt', 'nodefied content.txt')
print("")
print("Done nodifying text")


print("Finding existing version of guide")
with open('BotC Guide.html', 'r', encoding="utf-8") as file:
    html_content = file.read()


soup = BeautifulSoup(html_content, 'html.parser')
vault = soup.find('div', id='vault')


# Read the content of the replacement html
with open('nodefied content.txt', 'r', encoding="utf-8") as file:
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


with open('nodified content.html', 'w', encoding="utf-8") as file:
    file.write(str(soup))






# List of keywords to search for
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


file_path = 'nodified content.html'
with open(file_path, 'r', encoding='utf-8') as file:
    current_contents = file.read()

# Update the HTML content with keyword replacements
current_contents = surround_keywords_with_span(current_contents, Townsfolk, "Townsfolk")
current_contents = surround_keywords_with_span(current_contents, Outsider, "Outsider")
current_contents = surround_keywords_with_span(current_contents, Minion, "Minion")
current_contents = surround_keywords_with_span(current_contents, Demon, "Demon")
current_contents = surround_keywords_with_span(current_contents, Traveller, "Traveller")
current_contents = surround_keywords_with_span(current_contents, Fabled, "Fabled")



file_path = 'highlighted.html'
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(current_contents)



# Replace 'input.txt' and 'output.txt' with your file names
input_path = 'highlighted.html'
output_path = 'rough.html'
#process_text(input_filename, output_filename)

# Load the HTML file
with open(input_path, 'r', encoding='utf-8') as file:
    html_content = file.read()


# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Find the <script> tag containing the JavaScript code
script_tag = soup.find('script')

# Extract the JavaScript code from the <script> tag
javascript_code = script_tag.string.strip()

# Locate the 'keywords' dictionary in the JavaScript code
start_index = javascript_code.find("var keywords = {") + len("var keywords = {")
end_index = javascript_code.find("};", start_index) + 1
roles_dict_str = javascript_code[start_index-1:end_index]


# Keywords
Extra  = [ "poisoned", "drunk", "townsfolk", "outsider", "fabled", "traveller"]
Extra += [ "demon", "minion", "droisoned","good","evil","nomination","execution","preached", "protect"]
Extra += [ "misregister", "sober", "healthy", "alignment", "jinx", "resurrect"]
Extra += [ "madness", "setup" ]
all_the_words = Townsfolk + Outsider + Minion + Demon + Traveller + Fabled + Extra
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
 
# Print the sorted dictionary
for key, value in sorted_keywords.items():
    print(f"{key}: {value}")

print("Wow! What an impressive set of key words")

# Convert the new dictionary to a JSON string
new_keywords_dict_str = json.dumps(sorted_keywords, indent=2)

# Replace the old 'roles' dictionary string with the new one
javascript_code = javascript_code.replace(roles_dict_str, new_keywords_dict_str)

# Update the <script> tag with the modified JavaScript code
script_tag.string = javascript_code

# Write the updated HTML back to the file
with open(output_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))



print("Prettifying HTML")
input_path = 'rough.html'
output_path = 'BotC Guide.html'

with open(input_path, 'r', encoding="utf-8") as file:
    html = file.read()

nicely_indented = str(indent(html))
fixed_spans = nicely_indented.replace("</span><span", "</span> <span")

with open(output_path, 'w', encoding="utf-8") as file:
    file.write(fixed_spans);
    
print("Done")

