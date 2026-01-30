#!/usr/bin/env python3
"""
Expand team aliases with misspellings and variations
"""
import json

misspellings = {
    "Chennai Super Kings": {
        "base": ["csk", "chennai super kings", "super kings", "csk", "c s k"],
        "variations": [
            "chaneai super kings", "chelsea super kings", "chnnai super kings",
            "chen super kings", "csk team", "super kings csk", "ksk", "csk csk",
            "chennai sk", "chennai super king", "china super kings", "cennai",
            "super king", "super kings csk", "csk super", "chenaai", "chenai sk"
        ]
    },
    "Mumbai Indians": {
        "base": ["mi", "mumbai indians", "indians", "m i"],
        "variations": [
            "mumbay indians", "mumbai", "mumbai indian", "mi team", "indians mi",
            "mumbaai indians", "mumbai indie", "mumbai ind", "indian mumbai", "mi indians",
            "mumbai indians", "mubai", "bombay indians", "mumbai indians", "mi mi",
            "mumbai i", "indians mumbai", "mumb indians", "mi's", "mumbai's"
        ]
    },
    "Royal Challengers Bangalore": {
        "base": ["rcb", "royal challengers bangalore", "royal challengers", "r c b"],
        "variations": [
            "royale challengers bangalore", "royal challengers bangalor", "rcb team",
            "challengers bangalore", "bangalore rcb", "royal challengers b", "rcb royal",
            "bangalur challengers", "banglaore rcb", "royal challengers", "banglore rcb",
            "bangalore royal", "rcb bangalore", "royal challengers banglaore", "rcb rcb",
            "bangalore challengers", "royal bngalore", "rcb b", "royal c b"
        ]
    },
    "Kolkata Knight Riders": {
        "base": ["kkr", "kolkata knight riders", "knight riders", "k k r"],
        "variations": [
            "kolkatta knight riders", "kolkota knight riders", "knight riders kkr",
            "kkr team", "kolkatta riders", "kkr kolkata", "knights riders", "riders kkr",
            "kolkata knight rider", "kolkta riders", "knights kkr", "kolkota kr",
            "kkr kkr", "kolkata riders", "knight kolkata", "kkr riders", "kolkata kr"
        ]
    },
    "Delhi Capitals": {
        "base": ["dc", "delhi capitals", "capitals", "d c"],
        "variations": [
            "delhi capitol", "delhii capitals", "delhi capital", "dc team", "capitals dc",
            "dc delhi", "delhi cap", "dellhi capitals", "delih capitals", "delhi c",
            "capitals delhi", "delhh capitals", "delhi capitals", "dc capitals",
            "delhi cd", "dc d", "delhi caps", "capitals delhi", "delh capital"
        ]
    },
    "Sunrisers Hyderabad": {
        "base": ["srh", "sunrisers hyderabad", "sunrisers", "s r h"],
        "variations": [
            "sunrissers hyderabad", "sunrisers hyderabd", "srh team", "hyderabad srh",
            "sunrisers hyderbad", "hyderbad sunrisers", "sunrisers h", "srh sunrisers",
            "hyderabad sunrisers", "hyderbad", "sunriser", "srh h", "sunrisers sr",
            "hyderbad srh", "srh srh", "sunrisers hyderabad", "hyderbad sunrisers", "srh hydeabad"
        ]
    },
    "Punjab Kings": {
        "base": ["pbks", "punjab kings", "kings", "p b k s"],
        "variations": [
            "punajab kings", "punjab king", "pbks team", "kings pbks", "punjab k",
            "pbks punjab", "kings punjab", "punajb kings", "punjab kings", "pnajab",
            "punjab kings", "pbks kings", "kings pbks", "pbks p", "punjab kings",
            "panjab kings", "punjab kg", "pbks pb", "kings punjab", "pbks punjab"
        ]
    },
    "Rajasthan Royals": {
        "base": ["rr", "rajasthan royals", "royals", "r r"],
        "variations": [
            "rajastahn royals", "rajasthan royal", "rr team", "royals rr", "rajasthan r",
            "rr rajasthan", "royals rajasthan", "rajstan royals", "rajastan royals",
            "rajashtan royals", "rr rr", "rajasth royals", "rajasthan", "royals raj",
            "rr royals", "rajasthan rr", "rajastan", "rajasthan royal", "rr raj"
        ]
    },
    "Gujarat Titans": {
        "base": ["gt", "gujarat titans", "titans", "g t"],
        "variations": [
            "gujrat titans", "gujuart titans", "titans gt", "gt team", "gt gujarat",
            "titans gujrat", "gujart titans", "gujarh titans", "gujrat", "titans gujrat",
            "gt titans", "gt t", "titans gujart", "gujrat titns", "gt gujrat",
            "titans gujarat", "guajrat titans", "gt titans", "gujarati titans", "titians"
        ]
    },
    "Lucknow Super Giants": {
        "base": ["lsg", "lucknow super giants", "super giants", "l s g"],
        "variations": [
            "lucknow super giant", "lsg team", "super giants lsg", "giants lsg",
            "lucknow sg", "lsg lucknow", "lucknao super giants", "lucknow", "lsg giants",
            "super giants lucknow", "lucknoo", "lucknow super", "lsg super", "lucknow sg",
            "lsg lsg", "lucknow giants", "lucknow super g", "lsg l", "giants lucknow"
        ]
    }
}

def expand_team_aliases():
    """Expand team aliases with misspellings"""
    
    expanded = {}
    
    for team, variations_dict in misspellings.items():
        base = variations_dict["base"]
        variations = variations_dict["variations"]
        
        # Combine all and remove duplicates, convert to lowercase
        all_aliases = list(set(base + variations))
        all_aliases = [a.lower().strip() for a in all_aliases]
        all_aliases = list(set(all_aliases))  # Remove duplicates again
        
        expanded[team] = sorted(all_aliases)
        
        print(f"✅ {team:30} → {len(all_aliases):2} aliases")
    
    return expanded

if __name__ == "__main__":
    print("📝 Expanding team aliases with misspellings & variations...\n")
    
    expanded_aliases = expand_team_aliases()
    
    # Save to file
    output = {"aliases": expanded_aliases}
    with open("/Users/vikrant/Desktop/IPL_analytics_ai/team_aliases.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Updated team_aliases.json with {len(expanded_aliases)} teams")
    print(f"📊 Total alias variations: {sum(len(v) for v in expanded_aliases.values())}")
