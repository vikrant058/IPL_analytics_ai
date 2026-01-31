"""Generate comprehensive aliases for all IPL players automatically"""
import json
import pandas as pd
from collections import Counter

def generate_aliases(player_name):
    """Generate common variations of a player's name"""
    aliases = set()
    
    # Add the full name
    aliases.add(player_name.lower())
    
    # Split the name
    parts = player_name.split()
    
    # Add each part individually
    for part in parts:
        aliases.add(part.lower())
    
    # Add common variations
    if len(parts) >= 2:
        # First + Last
        aliases.add(f"{parts[0]} {parts[-1]}".lower())
        # Last + First
        aliases.add(f"{parts[-1]} {parts[0]}".lower())
        # Initials with last name
        if len(parts[0]) > 0:
            aliases.add(f"{parts[0][0]} {parts[-1]}".lower())
    
    # Handle special cases and common nicknames
    name_lower = player_name.lower()
    
    # Common IPL player nicknames/variations
    nicknames = {
        'virat kohli': ['king kohli', 'chikoo', 'vk', 'veer'],
        'rohit sharma': ['hitman', 'ro hit', 'the wall', 'rs'],
        'suresh raina': ['chinna thala', 'cherry', 'mr ipl', 'sr'],
        'ms dhoni': ['csk captain', 'thala', 'dhony', 'msd', 'captain'],
        'sachin tendulkar': ['master blaster', 'little master', 'sachin', 'tendulkar'],
        'david warner': ['big show', 'warner', 'da warner'],
        'ab de villiers': ['mr 360', 'abd', 'ab', 'abde villiers'],
        'shikhar dhawan': ['gabbar', 'dhawan', 'sd'],
        'rahul dravid': ['wall', 'dravid', 'rahul'],
        'saurav ganguly': ['dada', 'ganguly', 'bengal tiger'],
        'ravichandran ashwin': ['ash', 'ashwin', 'ashwin r', 'ashwin ashwin'],
        'yuzvendra chahal': ['mystery spinner', 'chahal', 'yuz'],
        'harbhajan singh': ['bhajji', 'harbhajan', 'singh'],
        'sunil narine': ['narine', 'mystery man'],
        'jasprit bumrah': ['boom boom', 'bumrah', 'jasprit'],
        'ravindra jadeja': ['sir jadeja', 'jadeja', 'cricketer', 'ra jadeja'],
        'amit mishra': ['mishra', 'amit'],
        'rishabh pant': ['risk', 'pant', 'rp'],
        'kl rahul': ['klrahul', 'rahul', 'kl'],
        'hardik pandya': ['hardik', 'pandya', 'hp'],
        'ajinkya rahane': ['rahane', 'am rahane', 'rahane aj'],
        'ruturaj gaikwad': ['ruthu', 'gaikwad', 'rutu'],
        'bumrah': ['boom boom', 'bumrah', 'jasprit'],
        'chahal': ['mystery', 'chahal', 'yuz'],
        'ashwin': ['ash', 'ashwin', 'ashwin r'],
        'narine': ['narine', 'mystery man'],
        'du plessis': ['faf', 'du plessis', 'plessis'],
        'gayle': ['universe boss', 'gayle', 'chris gayle'],
    }
    
    # Add known nicknames
    for key, nicks in nicknames.items():
        if key in name_lower or name_lower in key:
            for nick in nicks:
                aliases.add(nick.lower())
    
    # Remove very short aliases (less than 2 chars) except single letter initials
    aliases = {a for a in aliases if len(a) > 1 or (len(a) == 1 and a.isalpha())}
    
    return sorted(list(aliases))


def main():
    # Load current aliases
    with open('player_aliases.json', 'r') as f:
        current_data = json.load(f)
    
    current_aliases = current_data.get('aliases', {})
    print(f"Current aliases count: {len(current_aliases)}")
    
    # Load dataset
    deliveries = pd.read_csv('deliveries.csv')
    
    # Get all unique players
    all_players = sorted(set(deliveries['batter'].unique()) | set(deliveries['bowler'].unique()))
    
    print(f"Total unique players in dataset: {len(all_players)}")
    print(f"Players already with aliases: {len(current_aliases)}")
    print(f"Players needing aliases: {len(all_players) - len(current_aliases)}")
    
    # Generate aliases for all players
    new_aliases = {}
    
    for player in all_players:
        if player in current_aliases:
            # Keep existing aliases
            new_aliases[player] = current_aliases[player]
        else:
            # Generate new aliases
            generated = generate_aliases(player)
            new_aliases[player] = generated
            print(f"Generated for {player}: {len(generated)} aliases")
    
    # Save updated aliases
    output_data = {'aliases': new_aliases}
    with open('player_aliases.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Updated player_aliases.json")
    print(f"Total players: {len(new_aliases)}")
    print(f"Total aliases: {sum(len(v) for v in new_aliases.values())}")


if __name__ == '__main__':
    main()
