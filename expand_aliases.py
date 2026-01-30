#!/usr/bin/env python3
"""
Expand player aliases with common misspellings and variations
"""
import json

# Define misspelling patterns for common cricket players
misspellings = {
    "V Kohli": {
        "base": ["virat kohli", "kohli", "virat", "v kohli"],
        "variations": [
            "viraat", "virat koli", "veerat", "virat kohl", "kohli viraat",
            "viraat kohli", "kohli virat", "virat kohli ji", "king kohli",
            "v k", "vk", "viraat koli", "virat kholi", "coholli",
            "virat cohhli", "virat kohli", "vkohli", "kohli v", "virrat kohli"
        ]
    },
    "RG Sharma": {
        "base": ["rohit sharma", "rohit", "rg sharma", "r sharma"],
        "variations": [
            "ro sharma", "rohit sharm", "roheit", "rohit sharmer", "roht",
            "rohit sharmaa", "rohhit", "ro hit", "sharma rohit", "rohit sharmas",
            "rohit sharma ji", "hitman", "the wall", "rs", "rohhit sharma",
            "rohit shrama", "rohit sharme", "roheit sharma", "ro sharma", "rohit s"
        ]
    },
    "MS Dhoni": {
        "base": ["dhoni", "mahendra singh dhoni", "ms dhoni", "m dhoni"],
        "variations": [
            "msd", "dhonee", "dhony", "mahendra dhoni", "singh dhoni", "ms doni",
            "m s dhoni", "dhoni mahi", "mahi dhoni", "dhonni", "captain cool",
            "thala", "dhoni ms", "mahinder singh dhoni", "ms dhoney", "dhone",
            "mahendra singh doni", "ms d", "ddhoni", "dhoni thala", "m.s. dhoni"
        ]
    },
    "JJ Bumrah": {
        "base": ["jasprit bumrah", "bumrah", "jj bumrah", "j bumrah"],
        "variations": [
            "jaspit bumrah", "jasper bumrah", "bumra", "jasprit bumra", "jaspreet",
            "bumrah jasprit", "bumrah jasper", "jasprit", "jasper", "bumrha",
            "bhumrah", "jj bumra", "boomrah", "bumrah ji", "bumra jasprit",
            "jasprit boomrah", "bumrah jaspit", "jasper bhumrah", "bumrah jasper", "jj bhumrah"
        ]
    },
    "SA Yadav": {
        "base": ["suryakumar yadav", "suryakumar", "yadav", "sky", "sa yadav"],
        "variations": [
            "s yadav", "surya kumar yadav", "surya yadav", "surya", "sky yadav",
            "skyyadav", "suryakumaar", "surya kumar", "surya kumaar", "suryakumar yada",
            "sky surya", "yadav surya", "surya yadavv", "suryakumer", "skyh",
            "suryakumar yada", "surya kl", "sky yada", "sa yada", "suryakumar sa"
        ]
    },
    "HH Pandya": {
        "base": ["hardik pandya", "hardik", "hh pandya", "h pandya"],
        "variations": [
            "hardiq pandya", "hardick", "hardik pandi", "pandya hardik", "hardhik",
            "har dik", "hardik pandy", "hardik pandia", "hardicks", "hardik pandyaa",
            "hardikpandya", "hh pandi", "hardik p", "hardikk", "hardik pandhya",
            "hardiq", "hardik pandy", "hardik sharmaa", "pandya hardiq", "hardik pandya"
        ]
    },
    "RR Pant": {
        "base": ["rishabh pant", "rishabh", "pant", "rr pant", "r pant"],
        "variations": [
            "rishabh pantha", "rishab pant", "rishabh pont", "rishabh pants", "pant rishabh",
            "rishabh p", "rishbh pant", "rishabpant", "rishab p", "rr panta",
            "rishabh pent", "rishabh panth", "rishaab pant", "rishab", "rishabh rant",
            "pant rishabh", "rishabh p", "rr pant", "rishbah pant", "rishabh pandt"
        ]
    },
    "KL Rahul": {
        "base": ["kl rahul", "rahul", "k rahul", "kl"],
        "variations": [
            "kan rahul", "kannur rahul", "k l rahul", "rahul kl", "klrahul",
            "kannur lochan", "kl r", "rahul kl", "kl rahuul", "k.l. rahul",
            "klrahul", "rahul k", "kannur", "kel rahul", "kl rahul",
            "rahul kannur", "k l rahul", "kl r", "kanpur rahul", "kl rahu"
        ]
    },
    "Y Chahal": {
        "base": ["yuzvendra chahal", "yuzvendra", "chahal", "yuzvi"],
        "variations": [
            "ychhal", "yuzvendra chhal", "yuzvendar", "chahal yuzvendra", "yuzi",
            "chahal yz", "yusvendra", "yuzvendre", "yuzvendra chalal", "yuzvendra chaal",
            "yuzvendra chahl", "yuzvendar chahal", "yuzvi chahal", "chahal yuzvi", "yu chahal",
            "chahal yuzi", "yuzvendra ch", "yuzvendra cha", "y chahal", "yuzvi ch"
        ]
    },
    "RA Jadeja": {
        "base": ["ravindra jadeja", "jadeja", "ra jadeja", "r jadeja"],
        "variations": [
            "ravindra", "ravindr jadeja", "ravindra jadeya", "rav jadeja", "jadeja ravindra",
            "ravindra j", "raavindra", "ravendra jadeja", "jadeja raj", "rj jadeja",
            "ra jadeija", "ravendra", "jadeja ravendra", "sir jadeja", "ravindra jaja",
            "rav jadej", "ra jad", "ravindra yad", "jadeja ra", "ravindra yada"
        ]
    },
    "AB de Villiers": {
        "base": ["ab de villiers", "ab devilliers", "a de villiers", "ab", "abd"],
        "variations": [
            "de villiers", "villiers", "ab de villa", "ab devillers", "ab de villier",
            "ab dev", "ab deville", "ab d v", "adb", "de villier",
            "villiers ab", "ab devilers", "ab de velliers", "ab div", "de villa",
            "ab de v", "ab dev", "ab dv", "de v", "ab de vil"
        ]
    },
    "DA Warner": {
        "base": ["david warner", "warner", "da warner", "d warner"],
        "variations": [
            "davit warner", "david warmer", "davud warner", "warner david", "david w",
            "dav warner", "davied warner", "davvid", "dav w", "warner davit",
            "david warnor", "davit", "warner d", "davud", "dave warner",
            "d w", "da w", "david w", "warner da", "davud warnor"
        ]
    },
    "S Dhawan": {
        "base": ["shikhar dhawan", "dhawan", "s dhawan", "shikhar"],
        "variations": [
            "sikhar dhawan", "shikhar dawan", "shikher", "dhawan shikhar", "shik dhawan",
            "shik", "shikhar d", "shikar dhawan", "shikhar dhaawan", "shikhar dhwan",
            "shikher dhawan", "shikhar dhowa", "dhawan sikhar", "s d", "shikhar dh",
            "shikhar dha", "dhawan shik", "sikhar", "shikhar sha", "shikhar sh"
        ]
    },
    "SK Raina": {
        "base": ["suresh raina", "raina", "sk raina", "s raina"],
        "variations": [
            "suresh", "surash raina", "suresh reina", "suresh rana", "raina suresh",
            "suresh r", "suressh", "suresh rain", "suraish raina", "suresh raana",
            "raina sursh", "suresh rainaa", "shuresh raina", "sr", "raina suresh",
            "suresh ra", "surash", "suresh raina", "raina suresh", "suresh rei"
        ]
    }
}

def expand_aliases():
    """Expand player aliases with misspellings"""
    
    expanded = {}
    
    for player, variations_dict in misspellings.items():
        base = variations_dict["base"]
        variations = variations_dict["variations"]
        
        # Combine all and remove duplicates, convert to lowercase
        all_aliases = list(set(base + variations))
        all_aliases = [a.lower().strip() for a in all_aliases]
        all_aliases = list(set(all_aliases))  # Remove duplicates again
        
        expanded[player] = sorted(all_aliases)
        
        print(f"✅ {player:20} → {len(all_aliases):2} aliases")
    
    return expanded

if __name__ == "__main__":
    print("📝 Expanding player aliases with misspellings & variations...\n")
    
    expanded_aliases = expand_aliases()
    
    # Save to file
    output = {"aliases": expanded_aliases}
    with open("/Users/vikrant/Desktop/IPL_analytics_ai/player_aliases.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Updated player_aliases.json with {len(expanded_aliases)} players")
    print(f"📊 Total alias variations: {sum(len(v) for v in expanded_aliases.values())}")
