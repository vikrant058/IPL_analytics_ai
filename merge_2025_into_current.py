"""
Merge 2025 CricSheet data into current IPL dataset
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def merge_2025_data():
    print(f"🔄 MERGING 2025 DATA INTO CURRENT DATASET")
    print(f"{'='*80}\n")
    
    # Load current data
    print("📖 Loading current datasets...")
    matches_df = pd.read_csv('matches.csv')
    deliveries_df = pd.read_csv('deliveries.csv')
    
    print(f"   Current: {len(matches_df)} matches, {len(deliveries_df)} deliveries\n")
    
    # Process 2025 matches from JSON
    data_dir = Path('cricsheet_raw_ipl')
    json_files = sorted(data_dir.glob('*.json'))
    
    new_matches = []
    new_deliveries = []
    
    print(f"📥 Processing 2025 CricSheet JSON files...\n")
    
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
            
            # Skip if already in dataset
            if match_id in matches_df['id'].values:
                continue
            
            # Extract match info
            dates = info.get('dates', [])
            match_date = dates[0] if dates else None
            
            teams = info.get('teams', [])
            team1, team2 = teams[0] if len(teams) > 0 else None, teams[1] if len(teams) > 1 else None
            
            venue = info.get('venue', None)
            city = info.get('city', None)
            
            toss = info.get('toss', {})
            toss_winner = toss.get('winner', None)
            toss_decision = toss.get('decision', None)
            
            outcome = info.get('outcome', {})
            winner = outcome.get('winner', None)
            
            # Parse result
            if 'by' in outcome:
                by_dict = outcome['by']
                if 'runs' in by_dict:
                    result = 'runs'
                    result_margin = by_dict['runs']
                elif 'wickets' in by_dict:
                    result = 'wickets'
                    result_margin = by_dict['wickets']
                else:
                    result = None
                    result_margin = None
            else:
                result = None
                result_margin = None
            
            pom = info.get('player_of_match', [None])[0]
            
            # Create match row
            match_row = {
                'id': match_id,
                'season': season,
                'city': city,
                'date': match_date,
                'match_type': 'League',
                'player_of_match': pom,
                'venue': venue,
                'team1': team1,
                'team2': team2,
                'toss_winner': toss_winner,
                'toss_decision': toss_decision,
                'winner': winner,
                'result': result,
                'result_margin': result_margin,
                'target_runs': None,
                'target_overs': None,
                'super_over': 'N',
                'method': None,
                'umpire1': None,
                'umpire2': None,
                'year': 2025
            }
            
            new_matches.append(match_row)
            
            # Process deliveries
            innings_list = match_data.get('innings', [])
            for inning_idx, inning in enumerate(innings_list):
                batting_team = inning.get('team')
                overs = inning.get('overs', [])
                
                for over_data in overs:
                    over_num = over_data.get('over')
                    deliveries = over_data.get('deliveries', [])
                    
                    for ball_num, delivery in enumerate(deliveries):
                        batter = delivery.get('batter')
                        bowler = delivery.get('bowler')
                        non_striker = delivery.get('non_striker')
                        
                        runs_dict = delivery.get('runs', {})
                        batsman_runs = runs_dict.get('batter', 0)
                        extras_runs = runs_dict.get('extras', 0)
                        total_runs = runs_dict.get('total', 0)
                        
                        extras_type = None
                        extras_dict = delivery.get('extras', {})
                        for ext_type in ['wides', 'noballs', 'byes', 'legbyes']:
                            if ext_type in extras_dict:
                                extras_type = ext_type
                                break
                        
                        is_wicket = 0
                        player_dismissed = 'NA'
                        dismissal_kind = 'NA'
                        fielder = 'NA'
                        
                        if 'wicket' in delivery:
                            is_wicket = 1
                            wicket_info = delivery['wicket']
                            player_dismissed = wicket_info.get('player_out', 'NA')
                            dismissal_kind = wicket_info.get('kind', 'NA')
                            fielder_info = wicket_info.get('fielders', [])
                            if fielder_info:
                                fielder = fielder_info[0].get('name', 'NA') if isinstance(fielder_info[0], dict) else fielder_info[0]
                        
                        # Determine bowling team
                        bowling_team = team2 if batting_team == team1 else team1
                        
                        deliv_row = {
                            'match_id': match_id,
                            'inning': inning_idx + 1,
                            'batting_team': batting_team,
                            'bowling_team': bowling_team,
                            'over': over_num,
                            'ball': ball_num + 1,
                            'batter': batter,
                            'bowler': bowler,
                            'non_striker': non_striker,
                            'batsman_runs': batsman_runs,
                            'extra_runs': extras_runs,
                            'total_runs': total_runs,
                            'extras_type': extras_type,
                            'is_wicket': is_wicket,
                            'player_dismissed': player_dismissed,
                            'dismissal_kind': dismissal_kind,
                            'fielder': fielder
                        }
                        
                        new_deliveries.append(deliv_row)
        
        except Exception as e:
            print(f"⚠️ Error processing {json_file.name}: {str(e)}")
            continue
    
    print(f"✅ Processed {len(new_matches)} new matches with {len(new_deliveries)} deliveries\n")
    
    # Convert to DataFrames
    new_matches_df = pd.DataFrame(new_matches)
    new_deliveries_df = pd.DataFrame(new_deliveries)
    
    # Merge with existing data
    print(f"🔗 Merging with existing datasets...\n")
    
    matches_merged = pd.concat([matches_df, new_matches_df], ignore_index=True)
    deliveries_merged = pd.concat([deliveries_df, new_deliveries_df], ignore_index=True)
    
    # Ensure proper column order and types
    matches_merged['id'] = matches_merged['id'].astype(int)
    deliveries_merged['match_id'] = deliveries_merged['match_id'].astype(int)
    
    # Save merged data
    print(f"💾 Saving merged datasets...\n")
    matches_merged.to_csv('matches.csv', index=False)
    deliveries_merged.to_csv('deliveries.csv', index=False)
    
    print(f"✅ MERGE COMPLETE")
    print(f"{'='*80}")
    print(f"📊 Final Dataset:")
    print(f"   Matches: {len(matches_merged):,} (was {len(matches_df):,}, added {len(new_matches_df)})")
    print(f"   Deliveries: {len(deliveries_merged):,} (was {len(deliveries_df):,}, added {len(new_deliveries_df)})")
    print(f"   Seasons: {sorted(matches_merged['season'].unique())}")
    print(f"\n✨ Dataset updated successfully!\n")

if __name__ == '__main__':
    merge_2025_data()
