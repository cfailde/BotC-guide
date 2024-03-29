#!/usr/bin/env python3
"""
Updates the guide.
Takes the data from BotC.txt.
Injects the appropriate HTML tags and tries to make it pretty.
Output is an updated BotC Guide.html file.
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


BOTC_DATA_FILE = "BotC.txt"
RESULT_FILE = "BotC Guide.html"
DEBUG_MODE = False
MAX_BACKUPS = 5


def debug(data: str, output_path: str) -> None:
    if not DEBUG_MODE:
        return

    print("  - Saving interim results to " + output_path)
    with open(output_path, 'w', encoding="utf-8") as file:
        file.writelines(data)


def sanity_check():
    for f in [BOTC_DATA_FILE, RESULT_FILE]:
        if os.path.exists(f):
            print(f"  {f} exists.")
        else:
            print(f"  File not found: {f}")
            return False
    return True


def check_file_format(file_path: str) -> bool:
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
                    print(f"  {file_name} is incorrectly formatted: 'A' detected before 'Q' on line {line_number}.")
                    return False
                elif first_letters and first_char == first_letters[-1]:
                    print(f"  {file_name} is incorrectly formatted: '{first_char}' detected after another '{first_char}' on line {line_number}.")
                    return False

                # Add the first character to the string
                first_letters += first_char

        # Check if the last letter is 'A'
        if first_letters and first_letters[-1] == 'A':
            print(f"  {file_name} is correctly formatted.")
            return True
        else:
            print(f"  {file_name} is incorrectly formatted: Missing 'A' at the end.")
            return False


def manage_backups(filename: str) -> None:
    backup_files = [f for f in os.listdir() if f.startswith(f"Back up of {filename.split('.')[0]}")]

    if len(backup_files) >= MAX_BACKUPS:
        backup_files.sort(key=lambda x: os.path.getctime(x))
        oldest_backup = backup_files[0]
        os.remove(oldest_backup)
        print(f"  Deleted the oldest backup file: {oldest_backup}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"Back up of {filename.split('.')[0]}-{timestamp}.html"

    shutil.copy(filename, backup_filename)
    print(f"  Created backup: {backup_filename}")


def surround_keywords_with_span(html_content:str, keywords: 'list[str]', character_type: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')

    for keyword in keywords:
        print("  Highlighting: " + keyword + "                               ", end='\r')

        matches = soup.find_all(string=re.compile(r'\b' + re.escape(keyword) + r'\b'))
        for match in matches:
            content = str(match)
            replaced_content = re.sub(r'\b' + re.escape(keyword) + r'\b', f'<span class="{character_type}">{keyword}</span>', content)
            match.replace_with(BeautifulSoup(replaced_content, 'html.parser'))

    return str(soup)


def text_to_nodes(input_path: str, output_path: str) -> str:
    output_lines = []

    answer_mode = False
    in_list = False
    in_ordered_list = False
    first_question = True
    id = 0
    with open(input_path, 'r', encoding="utf-8") as file:
        for line in file:
            # blank lines separate question-answer blocks, but also indicate the end of lists and paragraphs within answers so need to handle this
            if line.strip() == '':
                if in_list:
                    output_lines.append(  '</ul>' )
                    in_list = False
                elif in_ordered_list:
                    output_lines.append(  '</ol>' )
                    in_ordered_list = False

                if answer_mode:
                    output_lines.append('        </p>\n')   # close paragraph
                    output_lines.append('        <p>')      # open paragraph

            # question time
            elif line.startswith('Q '):
                answer_mode = False
                id += 1

                if first_question:
                    first_question = False
                else:
                    output_lines.append('        </p>\n')   # close paragraph
                    output_lines.append('      </div>\n')     # close answer
                    output_lines.append('    </div>\n')       # close node

                output_lines.append('    <div class="node">\n')  # open node
                output_lines.append('      <h4 class="question">' + line[2:])   # open question

            elif line.startswith('A '):
                answer_mode = True
                output_lines.append('      </h4>\n')              # close question
                output_lines.append('      <div class="answer">\n          <p>' + line[2:])     # open answer and open first paragraph

            # skip comments
            elif line.startswith('=') or line.startswith('--') or line.startswith(':'):
                pass

            # ordered_list
            elif line.strip().startswith('#'):
                if not in_ordered_list:
                    output_lines.append('<ol><li>')
                    in_ordered_list = True
                else:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("#","",1))
            
            # unordered list
            elif line.strip().startswith('*'):
                if not in_list:
                    output_lines.append('<ul><li>')
                    in_list = True
                else:
                    output_lines.append("</li><li>")

                output_lines.append(line.replace("*","",1))

            else:
                output_lines.append(line)

    print("  Processed " + str(id) + " nodes")
    debug(output_lines, output_path)
    return '\n'.join(output_lines)


def replace_nodes(original: str, replacement: str, output_path: str) -> str:
    print("  Opening current version of guide")
    with open(original, 'r', encoding="utf-8") as file:
        html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        vault = soup.find('main')

    # Parse the replacement content and remove empty paragraphs
    print("  Removing empty divs")
    replacement_soup = BeautifulSoup(replacement, 'html.parser')
    for p_tag in replacement_soup.find_all('div'):
        if not p_tag.text.strip():  # Check if the paragraph has only whitespace
            p_tag.extract()  # Remove the empty paragraph

    print("  Replacing nodes")
    if vault:
        vault.clear()
        vault.append(replacement_soup)

    debug(str(soup), output_path)
    return str(soup)


def highlight_roles(current_contents: str, output_path: str) -> str:
    current_contents = surround_keywords_with_span(current_contents, Fabled, "Fabled")
    current_contents = surround_keywords_with_span(current_contents, Townsfolk, "Townsfolk")
    current_contents = surround_keywords_with_span(current_contents, Outsider, "Outsider")
    current_contents = surround_keywords_with_span(current_contents, Minion, "Minion")
    current_contents = surround_keywords_with_span(current_contents, Demon, "Demon")
    current_contents = surround_keywords_with_span(current_contents, Traveller, "Traveller")

    debug(current_contents, output_path)
    return current_contents


def update_index(html: str, output_path: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script')

    # Extract the JavaScript code from the <script> tag
    javascript_code = script_tag.string.strip()

    # Locate the 'keywords' dictionary in the JavaScript code
    start_index = javascript_code.find("var keywords = {") + len("var keywords = {")
    end_index = javascript_code.find("};", start_index) + 1
    keywords_str = javascript_code[start_index-1:end_index]

    # Convert the new dictionary to a JSON string
    new_keywords_dict_str = json.dumps(all_the_words, indent=2)

    # Replace the old index string with the new one
    javascript_code = javascript_code.replace(keywords_str, new_keywords_dict_str)

    # Update the <script> tag with the modified JavaScript code
    script_tag.string = javascript_code

    new_keyword_count = sum(len(words) for words in all_the_words.values())
    print(f"  Added {new_keyword_count} keywords to index")

    debug(str(soup), output_path)
    return str(soup)


def indent_keywords(html: str) -> str:
    updated_content = []
    found_start = False

    for line in html.split('\n'):
        if found_start:
            updated_content.append(" " * 6 + line)
        else:
            if line.strip().startswith("var keywords = {"):
                found_start = True
            updated_content.append(line)
        if line.startswith("};"):
            found_start = False
    return "\n".join(updated_content)

def indent(html: str, output_path: str) -> str:
    nicely_indented = str(yattag_indent(html))
    fixed_spans = nicely_indented.replace("</span><span", "</span> <span")

    updated_content = indent_keywords(fixed_spans)

    debug(updated_content, output_path)
    return updated_content

# Replaces underscores around words with <em></em> tag
def emphasise(html_content: str, output_path: str) -> str:
    # Define a regex pattern to find words surrounded by underscores
    pattern = re.compile(r'(_)(\w+)(_)')

    modified_html = pattern.sub(lambda match: f'<em>{match.group(2)}</em>', html_content)

    debug(modified_html, output_path)
    return modified_html

def remove_blank_lines(html: str, output_path: str) -> str:
    lines = html.split("\n")
    result = []
    script_encountered = False
    for line in lines:
        if not script_encountered:
            if line.strip():  # Check if line is not blank
                result.append(line)
            if line.strip().startswith("<script>"):
                script_encountered = True
        else:
            result.append(line)

    deblanked_content = "\n".join(result)
    debug(deblanked_content, output_path)
    return deblanked_content

def remove_empty_paragraphs(html: str, output_path: str) -> str:
    lines = html.split("\n")
    result = []

    for line in lines:
      if not line.strip().startswith("<p></p>"):
        result.append(line)

    content = "\n".join(result)
    debug(content, output_path)
    return content


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
Townsfolk += [ "Village Idiot"]

Outsider  =  [ "Snitch", "Butler", "Goon", "Acrobat"]
Outsider  += [ "Puzzlemaster", "Tinker", "Saint", "Sweetheart"]
Outsider  += [ "Plague Doctor", "Recluse", "Mutant", "Heretic"]
Outsider  += [ "Damsel", "Klutz", "Drunk", "Golem", "Moonchild"]
Outsider  += [ "Barber", "Politician", "Lunatic", "Hatter"]

Minion     = [ "Godfather", "Widow", "Poisoner", "Devil's Advocate"]
Minion    += [ "Harpy", "Witch", "Spy", "Cerenovus", "Fearmonger", "Pit-Hag"]
Minion    += [ "Psychopath", "Assassin", "Baron", "Mezepheles", "Goblin"]
Minion    += [ "Scarlet Woman", "Mastermind", "Evil Twin", "Boomdandy"]
Minion    += [ "Marionette", "Organ Grinder", "Vizier", "Summoner"]

Demon      = [ "Pukka", "Lil' Monsta", "Lleech", "No Dashii", "Imp"]
Demon     += [ "Shabaloth", "Po", "Zombuul", "Al-Hadikhia", "Vigormortis"]
Demon     += [ "Fang Gu", "Vortox", "Legion", "Leviathan", "Riot", "Kazali"]
Demon     += [ "Ojo", "Yaggababble" ]

Traveller  = [ "Bureaucrat", "Thief", "Gunslinger", "Scapegoat", "Beggar"]
Traveller += [ "Apprentice", "Matron", "Judge", "Bishop", "Voudon", "Barista"]
Traveller += [ "Harlot", "Butcher", "Deviant", "Bone Collector", "Gangster"]

Fabled     = [ "Revolutionary", "Fiddler", "Toymaker", "Fibbin", "Bootlegger"]
Fabled    += [ "Spirit of Ivory", "Hell's Librarian", "Djinn", "Duchess"]
Fabled    += [ "Storm Catcher", "Sentinel", "Doomsayer", "Angel", "Buddhist"] 
Fabled    += [ "Ferryman", "Gardener"] 

# All the keywords that are not the names of characters
# character types
Extra  = [ "demon", "minion", "townsfolk", "outsider", "fabled", "traveller"] 
# conditions
Extra += [ "poison", "drunk", "droisoned", "sober", "healthy"] 
Extra += [ "good", "evil", "alive", "dead", "preached" ]
# concepts
Extra += [ "nomination | nominate","execution | execute | executing"]
Extra += [ "register | registration", "vote | voting" ]
Extra += [ "alignment", "jinx", "resurrect", "regurgitate | regurgitation"]
Extra += [ "madness", "setup", "protect" ]
Extra += [ "in play", "out of play", "bluff", "mid game", "red herring"]
Extra += [ "Teensyville" ]

all_the_words = {"Townsfolk":Townsfolk ,
                 "Outsider":Outsider,
                 "Minion":Minion,
                 "Demon":Demon,
                 "Traveller":Traveller,
                 "Fabled":Fabled,
                 "Extra":Extra }

print("Starting update.")

print("Checking for input files")
if not sanity_check():
    sys.exit("  Oh dear!")

print("Checking " + BOTC_DATA_FILE)
if not check_file_format(BOTC_DATA_FILE):
    sys.exit("  Oh dear!")

if DEBUG_MODE:
    print("Backing up ...")
    manage_backups(RESULT_FILE)

print("Nodifying text ...")
nodes = text_to_nodes(BOTC_DATA_FILE, 'nodefied content.txt')

print("Placing updated nodes in guide ...")
interim_result = replace_nodes(RESULT_FILE, nodes, 'nodified content.html')

print("Highlighting roles ...")
interim_result = highlight_roles(interim_result, 'highlighted.html')
print("  Done highlighting.                                                              ")

print("Updating index ...")
interim_result = update_index(interim_result, 'updated index.html')

print("Removing excess blank lines ...")
interim_result = remove_blank_lines(interim_result, "removed_blank_lines.html")

print("Prettifying ...")
interim_result = indent(interim_result, 'pretty.html')

print("Adding emphasis ...")
interim_result = emphasise(interim_result, "emphasised.html")

print("Removing blank paragraphs ...")
interim_result = remove_empty_paragraphs(interim_result, "removed_empty_paragraphs.html")

print("Saving updated guide ...")
with open(RESULT_FILE, 'w', encoding='utf-8') as output:
    output.write(interim_result)

print("Done updating.")