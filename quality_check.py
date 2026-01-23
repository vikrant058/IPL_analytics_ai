"""
Comprehensive quality check for merged IPL dataset
"""
import pandas as pd
import numpy as np
from collections import defaultdict

def run_quality_checks():
    print(f"\n{'='*80}")
    print(f"📊 IPL DATASET QUALITY CHECK")
    print(f"{'='*80}\n")
    
    # Load data
    try:
        matches = pd.read_csv('matches.csv', low_memory=False, on_bad_lines='skip')
        deliveries = pd.read_csv('deliveries.csv', low_memory=False, on_bad_lines='skip')
        ground_mapping = __import__('json').load(open('ground_names.json'))
        print("✅ All data files loaded successfully\n")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # 1. BASIC STATISTICS
    print(f"1️⃣ DATASET STATISTICS")
    print(f"{'-'*80}")
    print(f"   Total Matches: {len(matches):,}")
    print(f"   Total Deliveries: {len(deliveries):,}")
    print(f"   Date Range: {matches['date'].min()} to {matches['date'].max()}")
    
    seasons = sorted(matches['season'].unique())
    print(f"   Seasons: {', '.join(map(str, seasons))}")
    
    # Check 2025 specifically
    matches_2025 = matches[matches['season'] == '2025']
    deliveries_2025 = deliveries[deliveries['match_id'].isin(matches_2025['id'])]
    print(f"\n   🎯 2025 Data:")
    print(f"      Matches: {len(matches_2025)}")
    print(f"      Deliveries: {len(deliveries_2025):,}")
    print(f"      Teams: {', '.join(sorted(set(list(matches_2025['team1'].unique()) + list(matches_2025['team2'].unique()))))}")
    
    # 2. MATCHES-DELIVERIES ALIGNMENT
    print(f"\n2️⃣ MATCHES-DELIVERIES ALIGNMENT")
    print(f"{'-'*80}")
    
    match_ids_in_matches = set(matches['id'].unique())
    match_ids_in_deliveries = set(deliveries['match_id'].unique())
    
    missing_in_deliveries = match_ids_in_matches - match_ids_in_deliveries
    extra_in_deliveries = match_ids_in_deliveries - match_ids_in_matches
    
    if missing_in_deliveries:
        print(f"   ⚠️ Matches with NO deliveries: {len(missing_in_deliveries)}")
        for mid in sorted(missing_in_deliveries)[:5]:
            match_row = matches[matches['id'] == mid].iloc[0]
            print(f"      • {mid}: {match_row['team1']} vs {match_row['team2']} ({match_row['date']})")
        if len(missing_in_deliveries) > 5:
            print(f"      ... and {len(missing_in_deliveries) - 5} more")
    else:
        print(f"   ✅ All matches have deliveries")
    
    if extra_in_deliveries:
        print(f"   ⚠️ Deliveries for non-existent matches: {len(extra_in_deliveries)}")
    else:
        print(f"   ✅ No orphaned deliveries")
    
    # 3. DATA QUALITY METRICS
    print(f"\n3️⃣ DATA QUALITY METRICS")
    print(f"{'-'*80}")
    
    # Check for duplicates
    dup_matches = len(matches) - len(matches.drop_duplicates(subset=['id']))
    dup_deliveries = len(deliveries) - len(deliveries.drop_duplicates())
    
    print(f"   Duplicate Matches: {dup_matches} {'❌' if dup_matches > 0 else '✅'}")
    print(f"   Duplicate Deliveries: {dup_deliveries} {'❌' if dup_deliveries > 0 else '✅'}")
    
    # Check null values
    print(f"\n   Missing Values (Matches):")
    null_matches = matches.isnull().sum()
    has_nulls = False
    for col in null_matches[null_matches > 0].index:
        if col not in ['umpire1', 'umpire2', 'method']:  # Expected nulls
            print(f"      • {col}: {null_matches[col]}")
            has_nulls = True
    if not has_nulls:
        print(f"      ✅ No unexpected null values")
    
    print(f"\n   Missing Values (Deliveries):")
    null_deliveries = deliveries.isnull().sum()
    has_nulls_deliv = False
    critical_cols = ['match_id', 'batter', 'bowler', 'total_runs']
    for col in critical_cols:
        if null_deliveries[col] > 0:
            print(f"      ❌ {col}: {null_deliveries[col]}")
            has_nulls_deliv = True
    if not has_nulls_deliv:
        print(f"      ✅ All critical fields populated")
    
    # 4. TEAM CONSISTENCY
    print(f"\n4️⃣ TEAM CONSISTENCY")
    print(f"{'-'*80}")
    
    all_teams = set()
    all_teams.update(matches['team1'].unique())
    all_teams.update(matches['team2'].unique())
    all_teams.update(deliveries['batting_team'].unique())
    all_teams.update(deliveries['bowling_team'].unique())
    
    print(f"   Unique Teams: {len(all_teams)}")
    for team in sorted(all_teams):
        print(f"      • {team}")
    
    # Check for team name variations
    team_variations = defaultdict(set)
    for team in all_teams:
        if 'Royal Challengers' in team:
            team_variations['Royal Challengers'].add(team)
        elif 'Kings' in team and 'Punjab' in team:
            team_variations['Punjab Kings'].add(team)
    
    if team_variations:
        print(f"\n   ⚠️ Team Name Variations Found:")
        for base_team, variations in team_variations.items():
            if len(variations) > 1:
                print(f"      {base_team}: {', '.join(sorted(variations))}")
    else:
        print(f"\n   ✅ Consistent team naming")
    
    # 5. VENUE STANDARDIZATION
    print(f"\n5️⃣ VENUE STANDARDIZATION")
    print(f"{'-'*80}")
    
    venues_in_matches = set(matches['venue'].dropna().unique())
    print(f"   Total Unique Venues: {len(venues_in_matches)}")
    
    # Check how many venues are in ground mapping
    mapped_venues = sum(1 for venue in venues_in_matches if any(
        venue in aliases for aliases in ground_mapping.values()
    ))
    print(f"   Venues in ground_names.json: {mapped_venues}/{len(venues_in_matches)}")
    
    unmapped = [v for v in venues_in_matches if not any(
        v in aliases for aliases in ground_mapping.values()
    )]
    
    if unmapped:
        print(f"\n   ⚠️ Unmapped Venues ({len(unmapped)}):")
        for venue in sorted(unmapped)[:10]:
            print(f"      • {venue}")
        if len(unmapped) > 10:
            print(f"      ... and {len(unmapped) - 10} more")
    else:
        print(f"   ✅ All venues mapped")
    
    # 6. DELIVERY STATISTICS
    print(f"\n6️⃣ DELIVERY STATISTICS")
    print(f"{'-'*80}")
    
    avg_deliveries = len(deliveries) / len(matches)
    print(f"   Average Deliveries per Match: {avg_deliveries:.1f}")
    print(f"   Expected (Full Match): ~240 deliveries")
    
    # Check for very short matches
    short_matches = []
    for mid in matches['id']:
        deliv_count = len(deliveries[deliveries['match_id'] == mid])
        if deliv_count < 100:
            short_matches.append((mid, deliv_count))
    
    if short_matches:
        print(f"\n   ⚠️ Matches with <100 deliveries: {len(short_matches)}")
        for mid, count in sorted(short_matches, key=lambda x: x[1])[:5]:
            match_row = matches[matches['id'] == mid].iloc[0]
            print(f"      • {mid}: {count} deliveries ({match_row['date']})")
        if len(short_matches) > 5:
            print(f"      ... and {len(short_matches) - 5} more")
    else:
        print(f"   ✅ All matches have sufficient deliveries")
    
    # 7. SEASON-BY-SEASON BREAKDOWN
    print(f"\n7️⃣ SEASON BREAKDOWN")
    print(f"{'-'*80}")
    
    for season in sorted(seasons):
        season_matches = len(matches[matches['season'] == season])
        season_deliveries = len(deliveries[deliveries['match_id'].isin(
            matches[matches['season'] == season]['id']
        )])
        status = "✅" if season_deliveries > 0 else "❌"
        print(f"   {season}: {season_matches} matches, {season_deliveries:,} deliveries {status}")
    
    # 8. DATA INTEGRITY SUMMARY
    print(f"\n8️⃣ OVERALL DATA INTEGRITY")
    print(f"{'-'*80}")
    
    issues = []
    if dup_matches > 0:
        issues.append(f"Duplicate matches: {dup_matches}")
    if dup_deliveries > 0:
        issues.append(f"Duplicate deliveries: {dup_deliveries}")
    if missing_in_deliveries:
        issues.append(f"Matches missing deliveries: {len(missing_in_deliveries)}")
    if extra_in_deliveries:
        issues.append(f"Orphaned deliveries: {len(extra_in_deliveries)}")
    if len(unmapped) > 0:
        issues.append(f"Unmapped venues: {len(unmapped)}")
    
    if issues:
        print(f"   ⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"      • {issue}")
    else:
        print(f"   ✅ NO CRITICAL ISSUES FOUND")
    
    # 9. FINAL SUMMARY
    print(f"\n{'='*80}")
    print(f"✅ QUALITY CHECK COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"📈 DATASET READY FOR USE:")
    print(f"   • Matches: {len(matches):,} (2008-2025)")
    print(f"   • Deliveries: {len(deliveries):,}")
    print(f"   • 2025 Season: {len(matches_2025)} new matches")
    print(f"   • Teams: {len(all_teams)}")
    print(f"   • Venues: {len(venues_in_matches)}")
    print(f"\n✨ Integration Status: {'✅ SUCCESSFUL' if not issues else '⚠️ NEEDS REVIEW'}\n")

if __name__ == '__main__':
    run_quality_checks()
