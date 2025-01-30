import csv
import re

# Read the mission template
with open('mission_template.yml', 'r') as template_file:
    mission_template = template_file.read()

def to_pascal_case(s):
    return ' '.join(word.capitalize() for word in s.split('_'))

def convert_roman_numerals_to_uppercase(s):
    # Define a regex pattern to match Roman numerals
    roman_numeral_pattern = re.compile(r'\b[i|v|x|l|c|d|m]+\b', re.IGNORECASE)
    
    # Function to convert matched Roman numeral to uppercase
    def to_upper(match):
        return match.group(0).upper()
    
    # Use re.sub to replace all matches with their uppercase versions
    return roman_numeral_pattern.sub(to_upper, s)

def roman_to_int(s):
    roman_numerals = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000
    }
    int_value = 0
    prev_value = 0
    for char in s:
        value = roman_numerals[char]
        if value > prev_value:
            int_value += value - 2 * prev_value
        else:
            int_value += value
        prev_value = value
    return int_value

# Function to replace placeholders in the template with actual values
def generate_mission_yaml(row):
    # Handle item rewards
    if row['Item']:
        item_split = row['Item'].split(':')
        itemRewardMaterial = to_pascal_case(item_split[0])
        itemRewardMaterialRaw = item_split[0]
        itemRewardAmount = item_split[1] if len(item_split) > 1 else '1'
        itemRewardsLore = f'\n      - "&b&l* &7{itemRewardAmount} {itemRewardMaterial}"'
        itemRewardsLoreMessage = f'\n&b&l* &7{itemRewardAmount} {itemRewardMaterial}'
        itemRewards = f'give %player% {itemRewardMaterialRaw} {itemRewardAmount}'
    else:
        itemRewardsLore = ''
        itemRewards = ''
        itemRewardsLoreMessage = ''

    # Handle mission details
    requirements = row['Requirements'].split('\r\n')
    requirements_lore = ''
    missions = ''
    for i, req in enumerate(requirements):
        mission_split = req.replace('-', '').replace(' ', '').split(':')
        missionType = mission_split[0]
        material = mission_split[1]
        amount = mission_split[2]
        requirements_lore += f'        - "&b&l* &7{missionType} {amount} {material}: %progress_{i+1}%/{amount}"\n'
        missions += f'        - {missionType}:{material}:{amount}\n'

    if (row["Override Material"]):
        material = row["Override Material"]
    # Check for Roman numeral in the Name
    name_parts = row['Name'].split()
    number = 1
    for part in name_parts:
        if re.fullmatch(r'[IVXLCDM]+', part, re.IGNORECASE):
            number = roman_to_int(part.upper())
            name_parts.remove(part)
            break

    return mission_template.format(
        id='_'.join(name_parts).replace(' ', '_').lower(),
        number=number,
        material=material,
        displayName=f"&b&l{row['Name'].title()}",
        requirements_lore=requirements_lore.strip(),
        missions=missions.strip(),
        type=row['Type'],
        crystals=row['Crystals'],
        money=row['Money'],
        experience=row['XP'],
        itemRewardsLore=itemRewardsLore,
        itemRewards=itemRewards,
        itemRewardsLoreMessage=itemRewardsLoreMessage,
    )

# Read the CSV file
with open('Missions.csv', 'r', newline='') as csv_file:
    csv_reader = csv.DictReader(csv_file, skipinitialspace=True, quoting=csv.QUOTE_MINIMAL)
    missions = [generate_mission_yaml(row) for row in csv_reader]

# Write the generated YAML to a file
with open('missions.yml', 'w') as yaml_file:
    yaml_file.write('missions:\n')
    yaml_file.write('\n'.join(missions))
    yaml_file.write("""
dailySlots:
- 10
- 11
- 12
- 13
- 14
- 15
- 16
customMaterialLists:
  LOGS:
  - "OAK_LOG"
  - "BIRCH_LOG"
  - "SPRUCE_LOG"
  - "DARK_OAK_LOG"
  - "ACACIA_LOG"
  - "JUNGLE_LOG"
  - "CRIMSON_STEM"
  - "WARPED_STEM"
  - "CHERRY_LOG"
  - "MANGROVE_LOG"
  - "PALE_OAK_LOG"
                    """)

print("missions.yml file has been generated.")