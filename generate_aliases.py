#!/usr/bin/env python3
"""
Generate comprehensive player and team aliases including misspellings and variations.
Uses Claude to intelligently generate common misspellings and name permutations.
"""

import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_aliases_for_players():
    """Use Claude to generate comprehensive aliases including misspellings"""
    
    # Top 50 IPL players
    top_players = [
        {"name": "V Kohli", "full_name": "Virat Kohli"},
        {"name": "RG Sharma", "full_name": "Rohit Sharma"},
        {"name": "MS Dhoni", "full_name": "Mahendra Singh Dhoni"},
        {"name": "JJ Bumrah", "full_name": "Jasprit Bumrah"},
        {"name": "SKY", "full_name": "Suryakumar Yadav"},
        {"name": "HH Pandya", "full_name": "Hardik Pandya"},
        {"name": "RR Pant", "full_name": "Rishabh Pant"},
        {"name": "KL Rahul", "full_name": "KL Rahul"},
        {"name": "AB de Villiers", "full_name": "AB de Villiers"},
        {"name": "DA Warner", "full_name": "David Warner"},
        {"name": "S Dhawan", "full_name": "Shikhar Dhawan"},
        {"name": "SK Raina", "full_name": "Suresh Raina"},
        {"name": "RA Jadeja", "full_name": "Ravindra Jadeja"},
        {"name": "Y Chahal", "full_name": "Yuzvendra Chahal"},
        {"name": "Bumrah", "full_name": "Jasprit Bumrah"},
        {"name": "SS Iyer", "full_name": "Shreyas Iyer"},
        {"name": "SA Yadav", "full_name": "Suryakumar Yadav"},
        {"name": "IK Pathan", "full_name": "Irfan Pathan"},
        {"name": "V Sehwag", "full_name": "Virender Sehwag"},
        {"name": "CH Gayle", "full_name": "Chris Gayle"},
    ]
    
    print("🔄 Generating aliases for players with misspellings...")
    
    aliases_dict = {}
    
    conversation_history = []
    
    # System prompt for Claude
    system_prompt = """You are an expert at generating name variations and common misspellings for Indian and international cricket players.
    
For each player, generate:
1. Common English misspellings (phonetic variations)
2. Informal nicknames
3. Short forms
4. Name permutations
5. Common typos people make

Return ONLY a valid JSON object with no markdown, no code blocks, just raw JSON.
Format: {"variations": ["variation1", "variation2", ...]}"""
    
    for player in top_players:
        canonical_name = player["name"]
        full_name = player["full_name"]
        
        # Ask Claude to generate variations
        prompt = f"""Generate common misspellings, typos, and variations for this cricket player:
        
Canonical Name: {canonical_name}
Full Name: {full_name}

Generate 15-20 variations including:
- Common typos (missing letters, extra letters, wrong letters)
- Phonetic misspellings (Rohit vs Roht vs Rohit vs Rohit etc)
- Informal names
- Short forms
- Nick names
- Wrong spellings people commonly use

Return as JSON: {{"variations": ["var1", "var2", ...]}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history,
                {"role": "user", "content": prompt}
            ]
        )
        
        assistant_message = response.choices[0].message.content
        
        try:
            # Parse the response
            variations_json = json.loads(assistant_message)
            variations = variations_json.get("variations", [])
            
            # Add basic forms too
            base_variations = [
                full_name.lower(),
                canonical_name.lower(),
                full_name.split()[-1].lower(),  # Last name
                full_name.split()[0].lower(),   # First name
            ]
            
            all_variations = list(set(base_variations + variations))
            aliases_dict[canonical_name] = all_variations
            
            print(f"✅ {canonical_name:20} → {len(all_variations):2} variations")
            
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse response for {canonical_name}")
            aliases_dict[canonical_name] = [
                full_name.lower(),
                canonical_name.lower(),
                full_name.split()[-1].lower()
            ]
    
    return aliases_dict


def generate_aliases_for_teams():
    """Generate comprehensive team aliases including misspellings"""
    
    teams = [
        ("CSK", "Chennai Super Kings"),
        ("MI", "Mumbai Indians"),
        ("RCB", "Royal Challengers Bangalore"),
        ("KKR", "Kolkata Knight Riders"),
        ("DC", "Delhi Capitals"),
        ("SRH", "Sunrisers Hyderabad"),
        ("PBKS", "Punjab Kings"),
        ("RR", "Rajasthan Royals"),
        ("GT", "Gujarat Titans"),
        ("LSG", "Lucknow Super Giants"),
    ]
    
    print("\n🔄 Generating aliases for teams with misspellings...")
    
    team_aliases = {}
    
    conversation_history = []
    
    system_prompt = """You are an expert at generating name variations and common misspellings for IPL cricket teams.
    
For each team, generate:
1. Common misspellings
2. Short forms
3. Variations of the acronym
4. Common typos

Return ONLY a valid JSON object with no markdown, no code blocks, just raw JSON.
Format: {"variations": ["variation1", "variation2", ...]}"""
    
    for abbrev, full_name in teams:
        prompt = f"""Generate common misspellings and variations for this IPL team:
        
Abbreviation: {abbrev}
Full Name: {full_name}

Generate 10-15 variations including:
- Misspellings of full name
- Variations of abbreviation
- Common typos
- Phonetic variations

Return as JSON: {{"variations": ["var1", "var2", ...]}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history,
                {"role": "user", "content": prompt}
            ]
        )
        
        assistant_message = response.choices[0].message.content
        
        try:
            variations_json = json.loads(assistant_message)
            variations = variations_json.get("variations", [])
            
            base_variations = [
                full_name.lower(),
                abbrev.lower(),
                full_name.split()[0].lower(),  # First word
            ]
            
            all_variations = list(set(base_variations + variations))
            team_aliases[full_name] = all_variations
            
            print(f"✅ {full_name:30} → {len(all_variations):2} variations")
            
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse response for {full_name}")
            team_aliases[full_name] = [full_name.lower(), abbrev.lower()]
    
    return team_aliases


def save_aliases(player_aliases, team_aliases):
    """Save aliases to JSON files"""
    
    # Save player aliases
    player_json = {"aliases": player_aliases}
    with open("/Users/vikrant/Desktop/IPL_analytics_ai/player_aliases.json", "w") as f:
        json.dump(player_json, f, indent=2)
    
    # Save team aliases
    team_json = {"aliases": team_aliases}
    with open("/Users/vikrant/Desktop/IPL_analytics_ai/team_aliases.json", "w") as f:
        json.dump(team_json, f, indent=2)
    
    print(f"\n✅ Saved {len(player_aliases)} player aliases")
    print(f"✅ Saved {len(team_aliases)} team aliases")


if __name__ == "__main__":
    print("🏏 IPL Aliases Generator - Including Misspellings & Variations\n")
    
    # Generate aliases
    player_aliases = generate_aliases_for_players()
    team_aliases = generate_aliases_for_teams()
    
    # Save to files
    save_aliases(player_aliases, team_aliases)
    
    print("\n✅ Complete! Aliases updated with comprehensive variations & misspellings")
