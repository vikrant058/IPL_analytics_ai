"""
Validate 2025 IPL data from CricSheet JSON files
"""
import json
import os
from pathlib import Path
from collections import defaultdict
import pandas as pd

def validate_2025_data():
    """Extract and validate all 2025 season matches"""
    
    data_dir = Path('cricsheet_raw_ipl')
    json_files = sorted(data_dir.glob('*.json'))
    
    print(f"📊 2025 IPL DATA VALIDATION")
    print(f"{'='*80}")
    
    matches_2025 = []
    total_deliveries_2025 = 0
    issues = []
    
    # Parse each JSON file
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                match_data = json.load(f)
            
            info = match_data.get('info', {})
            season = info.get('season')
            
            # Check if this is a 2025 match
            if season != '2025':
                continue
            
            match_id = json_file.stem
            match_teams = info.get('teams', [])
            venue = info.get('venue', 'Unknown')
            dates = info.get('dates', [])
            match_date = dates[0] if dates else 'Unknown'
            
            # Count deliveries in this match
            innings_list = match_data.get('innings', [])
            match_deliveries = 0
            
            for inning in innings_list:
                overs = inning.get('overs', [])
                for over_data in overs:
                    deliveries = over_data.get('deliveries', [])
                    match_deliveries += len(deliveries)
            
            total_deliveries_2025 += match_deliveries
            
            # Check if match is complete (should have ~120 deliveries for full match)
            is_complete = match_deliveries >= 100  # Conservative threshold
            
            matches_2025.append({
                'match_id': match_id,
                'date': match_date,
                'teams': ' vs '.join(match_teams),
                'venue': venue,
                'deliveries': match_deliveries,
                'complete': is_complete,
                'status': '✅' if is_complete else '⚠️'
            })
        
        except json.JSONDecodeError as e:
            issues.append(f"❌ JSON Parse Error in {json_file.name}")
        except Exception as e:
            issues.append(f"❌ Error in {json_file.name}: {str(e)}")
    
    # Display results
    print(f"\n📅 2025 MATCHES FOUND: {len(matches_2025)}")
    print(f"{'-'*80}\n")
    
    if matches_2025:
        df = pd.DataFrame(matches_2025)
        print(df.to_string(index=False))
        
        print(f"\n{'-'*80}")
        print(f"\n📊 2025 DATA STATISTICS:")
        print(f"  Total Matches: {len(matches_2025)}")
        print(f"  Total Deliveries: {total_deliveries_2025:,}")
        print(f"  Avg Deliveries/Match: {total_deliveries_2025/len(matches_2025):.0f}")
        
        complete_count = sum(1 for m in matches_2025 if m['complete'])
        print(f"  Complete Matches (≥100 deliveries): {complete_count}/{len(matches_2025)}")
        
        if complete_count < len(matches_2025):
            print(f"\n  ⚠️ INCOMPLETE MATCHES:")
            for m in matches_2025:
                if not m['complete']:
                    print(f"    • {m['match_id']}: {m['deliveries']} deliveries")
        
        # Check teams
        all_teams = set()
        for match in matches_2025:
            teams = match['teams'].split(' vs ')
            all_teams.update(teams)
        
        print(f"\n🏢 TEAMS IN 2025:")
        for team in sorted(all_teams):
            print(f"  • {team}")
        
        # Check venues
        venues = set(m['venue'] for m in matches_2025)
        print(f"\n🏟️ VENUES IN 2025:")
        for venue in sorted(venues):
            print(f"  • {venue}")
    
    else:
        print("❌ NO 2025 MATCHES FOUND IN CRICSHEET DATA!")
    
    if issues:
        print(f"\n⚠️ DATA ISSUES:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"  {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    
    print(f"\n{'='*80}")
    print(f"✅ 2025 VALIDATION COMPLETE\n")
    
    return {
        'total_matches': len(matches_2025),
        'total_deliveries': total_deliveries_2025,
        'matches': matches_2025,
        'data_quality': 'GOOD' if len(matches_2025) == 74 and total_deliveries_2025 > 8000 else 'INCOMPLETE'
    }

if __name__ == '__main__':
    results = validate_2025_data()
