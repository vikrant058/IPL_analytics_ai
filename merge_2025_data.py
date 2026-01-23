"""
Merge 2025 IPL data from CricSheet JSON into existing CSV files
"""
import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

def merge_2025_data():
    """Merge 2025 matches and deliveries into existing CSVs"""
    
    print(f"📊 MERGING 2025 IPL DATA")
    print(f"{'='*80}\n")
    
    # Load existing data
    print("📖 Loading existing data...")
    matches_current = pd.read_csv('matches.csv')
    deliveries_current = pd.read_csv('deliveries.csv')
    
    print(f"  Current matches: {len(matches_current)}")
    print(f"  Current deliveries: {len(deliveries_current)}\n")
    
    # Extract 2025 data from JSON files
    print("🔍 Extracting 2025 matches from JSON...")
    
    data_dir = Path('cricsheet_raw_ipl')
    json_files = sorted(data_dir.glob('*.json'))
    
    new_matches = []
    new_deliveries = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                match_data = json.load(f)
            
            info = match_data.get('info', {})
            season = info.get('season')
            
            # Only process 2025 matches
            if season != '2025':
                continue
            
            match_id = int(json_file.stem)
            match_teams = info.get('teams', [])
            city = info.get('city', '')
            dates = info.get('dates', [])
            match_date = dates[0] if dates else ''
            venue = info.get('venue', '')
            
            # Get match outcome
            outcome = info.get('outcome', {})
            winner = outcome.get('winner', '')
            
            # Skip incomplete match
            if match_id == 1473495:
                print(f"  ⏭️  Skipping incomplete match {match_id}")
                continue
            
            # Build match row
            match_row = {
                'id': match_id,
                'season': season,
                'city': city,
                'date': match_date,
                'match_type': info.get('match_type', 'League'),
                'player_of_match': ', '.join(info.get('player_of_match', [])),
                'venue': venue,
                'team1': match_teams[0] if len(match_teams) > 0 else '',
                'team2': match_teams[1] if len(match_teams) > 1 else '',
                'toss_winner': info.get('toss', {}).get('winner', ''),
                'toss_decision': info.get('toss', {}).get('decision', ''),
                'winner': winner,
                'result': outcome.get('result', ''),
                'result_margin': outcome.get('by', {}).get('runs', outcome.get('by', {}).get('wickets', '')),
                'target_runs': '',
                'target_overs': '',
                'super_over': outcome.get('super_over', 'N'),
                'method': '',
                'umpire1': '',
                'umpire2': '',
                'year': 2025
            }
            
            # Extract umpires
            officials = info.get('officials', {})
            umpires = officials.get('umpires', [])
            if len(umpires) >= 2:
                match_row['umpire1'] = umpires[0]
                match_row['umpire2'] = umpires[1]
            
            new_matches.append(match_row)
            
            # Extract deliveries
            innings_list = match_data.get('innings', [])
            
            for inning_idx, inning in enumerate(innings_list):
                inning_num = inning_idx + 1
                batting_team = inning.get('team', '')
                
                # Determine bowling team
                bowling_team = match_teams[1] if match_teams[0] == batting_team else match_teams[0]
                
                overs = inning.get('overs', [])
                
                for over_data in overs:
                    over_num = over_data.get('over', 0)
                    deliveries = over_data.get('deliveries', [])
                    
                    for ball_num, delivery in enumerate(deliveries, 1):
                        batter = delivery.get('batter', '')
                        bowler = delivery.get('bowler', '')
                        non_striker = delivery.get('non_striker', '')
                        
                        runs = delivery.get('runs', {})
                        batsman_runs = runs.get('batter', 0)
                        extra_runs = runs.get('extras', 0)
                        total_runs = runs.get('total', 0)
                        
                        # Handle extras
                        extras_type = ''
                        extras_dict = delivery.get('extras', {})
                        if extras_dict:
                            for extra_type in ['wides', 'noballs', 'byes', 'legbyes', 'penalty']:
                                if extra_type in extras_dict:
                                    extras_type = extra_type
                                    break
                        
                        # Handle wickets
                        is_wicket = 0
                        player_dismissed = 'NA'
                        dismissal_kind = 'NA'
                        fielder = 'NA'
                        
                        if 'wicket' in delivery:
                            is_wicket = 1
                            wicket = delivery['wicket']
                            player_dismissed = wicket.get('player_out', 'NA')
                            dismissal_kind = wicket.get('kind', 'NA')
                            fielders = wicket.get('fielders', [])
                            if fielders:
                                fielder = fielders[0].get('name', 'NA') if isinstance(fielders[0], dict) else fielders[0]
                        
                        delivery_row = {
                            'match_id': match_id,
                            'inning': inning_num,
                            'batting_team': batting_team,
                            'bowling_team': bowling_team,
                            'over': over_num,
                            'ball': ball_num,
                            'batter': batter,
                            'bowler': bowler,
                            'non_striker': non_striker,
                            'batsman_runs': batsman_runs,
                            'extra_runs': extra_runs,
                            'total_runs': total_runs,
                            'extras_type': extras_type,
                            'is_wicket': is_wicket,
                            'player_dismissed': player_dismissed,
                            'dismissal_kind': dismissal_kind,
                            'fielder': fielder
                        }
                        
                        new_deliveries.append(delivery_row)
        
        except Exception as e:
            print(f"  ⚠️  Error processing {json_file.name}: {str(e)}")
    
    print(f"  ✅ Extracted {len(new_matches)} matches and {len(new_deliveries)} deliveries\n")
    
    # Convert to DataFrames
    matches_2025_df = pd.DataFrame(new_matches)
    deliveries_2025_df = pd.DataFrame(new_deliveries)
    
    # Standardize team names in 2025 data
    print("🔄 Standardizing team names...")
    team_mapping = {
        'Royal Challengers Bengaluru': 'Royal Challengers Bangalore'
    }
    
    for col in ['team1', 'team2']:
        if col in matches_2025_df.columns:
            matches_2025_df[col] = matches_2025_df[col].replace(team_mapping)
    
    for col in ['batting_team', 'bowling_team']:
        if col in deliveries_2025_df.columns:
            deliveries_2025_df[col] = deliveries_2025_df[col].replace(team_mapping)
    
    # Reorder columns to match current data
    matches_2025_df = matches_2025_df[matches_current.columns]
    deliveries_2025_df = deliveries_2025_df[deliveries_current.columns]
    
    # Merge data
    print("🔗 Merging with existing data...")
    matches_merged = pd.concat([matches_current, matches_2025_df], ignore_index=True)
    deliveries_merged = pd.concat([deliveries_current, deliveries_2025_df], ignore_index=True)
    
    # Save merged data
    print("💾 Saving merged data...")
    matches_merged.to_csv('matches.csv', index=False)
    deliveries_merged.to_csv('deliveries.csv', index=False)
    
    print(f"\n✅ MERGE COMPLETE!")
    print(f"{'='*80}")
    print(f"\n📊 UPDATED DATA SUMMARY:")
    print(f"  Matches: {len(matches_current)} + {len(matches_2025_df)} = {len(matches_merged)}")
    print(f"  Deliveries: {len(deliveries_current):,} + {len(deliveries_2025_df):,} = {len(deliveries_merged):,}")
    print(f"  Years: {sorted(matches_merged['season'].unique())}")
    print(f"\n✅ Ready to reload the app!\n")

if __name__ == '__main__':
    merge_2025_data()
