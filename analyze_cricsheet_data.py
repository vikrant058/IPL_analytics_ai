"""
Analyze CricSheet IPL data and compare with current dataset
"""
import json
import os
from pathlib import Path
from collections import defaultdict
import pandas as pd

def analyze_cricsheet_data():
    """Analyze all JSON files in cricsheet_raw_ipl"""
    
    data_dir = Path('cricsheet_raw_ipl')
    json_files = sorted(data_dir.glob('*.json'))
    
    print(f"📊 CRICSHEET DATA ANALYSIS")
    print(f"{'='*70}")
    print(f"Total JSON files found: {len(json_files)}\n")
    
    # Counters
    seasons = defaultdict(int)
    years = set()
    teams = set()
    venues = set()
    total_deliveries = 0
    match_ids = []
    data_issues = []
    sample_structures = []
    
    # Parse each JSON file
    for i, json_file in enumerate(json_files):
        try:
            with open(json_file, 'r') as f:
                match_data = json.load(f)
            
            # Extract match info
            info = match_data.get('info', {})
            match_id = json_file.stem
            match_ids.append(match_id)
            
            season = info.get('season', 'Unknown')
            seasons[season] += 1
            
            # Extract year from season (e.g., "2007/08" -> 2008)
            if '/' in season:
                year = int(season.split('/')[-1])
                if year < 100:
                    year = 2000 + year
                years.add(year)
            
            # Get teams and venue
            match_teams = info.get('teams', [])
            for team in match_teams:
                teams.add(team)
            
            venue = info.get('venue', 'Unknown')
            venues.add(venue)
            
            # Count deliveries
            innings_list = match_data.get('innings', [])
            for inning in innings_list:
                overs = inning.get('overs', [])
                for over_data in overs:
                    deliveries = over_data.get('deliveries', [])
                    total_deliveries += len(deliveries)
            
            # Store sample structure for first and last match
            if i == 0 or i == len(json_files) - 1:
                sample_structures.append({
                    'file': json_file.name,
                    'match_id': match_id,
                    'season': season,
                    'teams': match_teams,
                    'venue': venue,
                    'innings_count': len(innings_list),
                    'has_info': bool(info),
                    'has_meta': bool(match_data.get('meta')),
                })
        
        except json.JSONDecodeError as e:
            data_issues.append(f"❌ JSON Parse Error in {json_file.name}: {str(e)}")
        except Exception as e:
            data_issues.append(f"❌ Error in {json_file.name}: {str(e)}")
    
    # Calculate statistics
    years_sorted = sorted(list(years))
    
    print(f"✅ SEASONS COVERAGE:")
    print(f"{'-'*70}")
    for season in sorted(seasons.keys(), key=lambda x: str(x)):
        print(f"  {season}: {seasons[season]} matches")
    
    print(f"\n📅 YEARS COVERED:")
    print(f"{'-'*70}")
    print(f"  Range: {min(years_sorted)} to {max(years_sorted)}")
    print(f"  Years: {', '.join(map(str, years_sorted))}")
    
    if 2025 in years:
        print(f"  ✅ 2025 DATA INCLUDED: {seasons.get('2024/25', 0)} matches")
    else:
        print(f"  ❌ 2025 DATA NOT INCLUDED")
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"{'-'*70}")
    print(f"  Total Matches: {len(match_ids)}")
    print(f"  Total Deliveries: {total_deliveries:,}")
    print(f"  Unique Teams: {len(teams)}")
    print(f"  Unique Venues: {len(venues)}")
    
    print(f"\n🏢 TEAMS IN DATA:")
    print(f"{'-'*70}")
    for team in sorted(teams):
        print(f"  • {team}")
    
    print(f"\n🏟️ VENUES IN DATA:")
    print(f"{'-'*70}")
    for venue in sorted(venues):
        print(f"  • {venue}")
    
    print(f"\n📋 SAMPLE MATCH STRUCTURES:")
    print(f"{'-'*70}")
    for sample in sample_structures:
        print(f"  File: {sample['file']}")
        print(f"    Match ID: {sample['match_id']}")
        print(f"    Season: {sample['season']}")
        print(f"    Teams: {sample['teams']}")
        print(f"    Venue: {sample['venue']}")
        print(f"    Innings: {sample['innings_count']}")
        print()
    
    if data_issues:
        print(f"\n⚠️ DATA ISSUES FOUND:")
        print(f"{'-'*70}")
        for issue in data_issues:
            print(f"  {issue}")
    
    # Compare with current data
    print(f"\n📈 COMPARISON WITH CURRENT DATA:")
    print(f"{'-'*70}")
    
    # Load current CSV files
    try:
        current_matches = pd.read_csv('matches.csv')
        current_deliveries = pd.read_csv('deliveries.csv')
        
        print(f"  Current matches.csv: {len(current_matches)} matches")
        print(f"  Current deliveries.csv: {len(current_deliveries):,} deliveries")
        print(f"\n  New cricsheet data: {len(match_ids)} matches")
        print(f"  New cricsheet data: {total_deliveries:,} deliveries")
        
        diff_matches = len(match_ids) - len(current_matches)
        diff_deliveries = total_deliveries - len(current_deliveries)
        
        print(f"\n  Difference:")
        print(f"    Matches: +{diff_matches} ({(diff_matches/len(current_matches)*100):.1f}%)")
        print(f"    Deliveries: +{diff_deliveries:,} ({(diff_deliveries/len(current_deliveries)*100):.1f}%)")
        
        # Check current data seasons
        current_seasons = current_matches['season'].unique()
        print(f"\n  Current data seasons: {sorted(current_seasons, key=lambda x: str(x))}")
        print(f"  New data seasons: {sorted(seasons.keys(), key=lambda x: str(x))}")
        
        # Check for new seasons
        current_set = set(current_seasons)
        new_set = set(seasons.keys())
        new_seasons = new_set - current_set
        
        if new_seasons:
            print(f"\n  ✅ NEW SEASONS IN CRICSHEET DATA:")
            for season in sorted(new_seasons):
                print(f"    • {season}: {seasons[season]} matches")
        else:
            print(f"\n  ℹ️ No new seasons (same season range)")
        
    except FileNotFoundError:
        print(f"  ⚠️ Could not load current CSV files")
    
    print(f"\n{'='*70}")
    print(f"✅ ANALYSIS COMPLETE\n")
    
    return {
        'total_matches': len(match_ids),
        'total_deliveries': total_deliveries,
        'seasons': dict(seasons),
        'years': sorted(list(years)),
        'has_2025': 2025 in years,
        'teams_count': len(teams),
        'venues_count': len(venues),
        'data_issues': data_issues
    }

if __name__ == '__main__':
    results = analyze_cricsheet_data()
