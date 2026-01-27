# Implementation Plan: Cricket Stats Corrections

## Data Structure Confirmed

Based on analysis of `deliveries.csv`:

### Columns Available:
- `batsman_runs`: Runs scored directly by batter (0, 1, 2, 3, 4, 6)
- `extra_runs`: Additional runs (wides, byes, leg byes, no balls)
- `total_runs`: Sum of batsman_runs + extra_runs
- `extras_type`: Type of extra ('legbyes', 'wides', 'byes', 'noballs', 'penalty', or NaN)
- `is_wicket`: Boolean (0=not out, 1=wicket/out)
- `match_id`, `inning`: For grouping

### Extra Types:
1. **'wides'** - Not counted as valid delivery for batter
2. **'legbyes'** - Not counted as bowler's runs conceded
3. **'byes'** - Not counted as bowler's runs conceded
4. **'noballs'** - Counted as bowler's runs conceded
5. **'penalty'** - Team extra (counted in match runs, not bowler's runs)
6. **NaN** - Normal delivery

---

## CORRECTIONS TO IMPLEMENT

### FIX #1: Batting Average (Line 301)

**Current Code:**
```python
'average': round(runs / innings, 2) if innings > 0 else 0,
```

**Issue:** 
- Includes not-out innings in denominator
- Cricket rule: Average = Runs / Dismissed Innings

**NEW CODE:**
```python
# Count dismissals (innings where player got out)
dismissals = player_deliveries[player_deliveries['is_wicket'] == 1][['match_id', 'inning']].drop_duplicates().shape[0]
'average': round(runs / dismissals, 2) if dismissals > 0 else 0,
```

**Impact:** All batting averages will be corrected to exclude not-out innings

---

### FIX #2: Strike Rate (Line 302)

**Current Code:**
```python
'strike_rate': round((runs / balls * 100), 2) if balls > 0 else 0,
```

**Issue:**
- Includes wides in "balls faced"
- Cricket rule: Strike Rate = (Runs / Valid Deliveries) × 100
- Wides are not valid deliveries for the batter

**NEW CODE:**
```python
# Valid deliveries = all deliveries except wides
valid_deliveries = len(player_deliveries[player_deliveries['extras_type'] != 'wides'])
'strike_rate': round((runs / valid_deliveries * 100), 2) if valid_deliveries > 0 else 0,
```

**Impact:** Strike rates for batters facing wides will be more accurate

---

### FIX #3: Dot Balls - Batting (Line 281)

**Current Code:**
```python
dot_balls = len(player_deliveries[player_deliveries['batsman_runs'] == 0])
```

**Issue:**
- Counts wides and no balls as dots
- Cricket rule: A dot is a valid delivery with 0 runs
- Wides/no balls are NOT valid deliveries

**NEW CODE:**
```python
# Dot ball = valid delivery (not wide/no ball) with 0 batsman runs
dot_balls = len(player_deliveries[
    (player_deliveries['batsman_runs'] == 0) & 
    (player_deliveries['extras_type'] != 'wides') &
    (player_deliveries['extras_type'] != 'noballs')
])
```

**Impact:** Dot ball counts will be more accurate

---

### FIX #4: Bowling Stats - Runs Conceded (Line 359)

**Current Code:**
```python
runs_conceded = player_deliveries['total_runs'].sum()
```

**Issue:**
- Includes leg byes and byes
- Cricket rule: Bowler concedes only: runs off bat + wides + no balls
- Leg byes and byes are NOT credited to bowler

**NEW CODE:**
```python
# Runs conceded = exclude leg byes and byes
runs_conceded = player_deliveries[
    ~player_deliveries['extras_type'].isin(['legbyes', 'byes'])
]['total_runs'].sum()
```

**OR more explicitly:**
```python
# Runs conceded = batsman_runs + wides + noballs (excluding legbyes and byes)
runs_conceded = (
    player_deliveries[player_deliveries['extras_type'] != 'legbyes']['total_runs'].sum() -
    player_deliveries[player_deliveries['extras_type'] == 'byes']['total_runs'].sum()
)
```

**Impact:** Bowling economy and average will be corrected significantly

---

### FIX #5: Bowling Average (Line 387)

**Current Code:**
```python
'average': round(runs_conceded / wickets, 2) if wickets > 0 else 0,
```

**Automatic Fix:** Once runs_conceded is fixed in FIX #4, this will automatically be correct.

---

### FIX #6: Economy Rate (Line 386)

**Current Code:**
```python
'economy': round((runs_conceded / (balls / 6)), 2) if balls > 0 else 0,
```

**Automatic Fix:** Once runs_conceded is fixed in FIX #4, this will be correct.

**Additional Issue:** Should overs count exclude wides/no balls?
- In cricket, an over is still 6 valid deliveries even if it has wides
- Current logic uses: `balls / 6` where balls might include extra balls
- Need to verify if we should count overs as "6 valid deliveries"

**RECOMMENDED FIX:**
```python
# Overs bowled = valid deliveries (excluding wides/noballs) / 6
valid_deliveries_bowled = len(player_deliveries[
    (player_deliveries['extras_type'] != 'wides') &
    (player_deliveries['extras_type'] != 'noballs')
])
overs = valid_deliveries_bowled / 6

'economy': round((runs_conceded / overs), 2) if overs > 0 else 0,
```

---

### FIX #7: Dot Balls - Bowling (Line 347)

**Current Code:**
```python
dot_balls = len(player_deliveries[player_deliveries['total_runs'] == 0])
```

**Issue:**
- Counts wides and no balls as dots
- Cricket rule: A dot is a valid delivery with 0 runs

**NEW CODE:**
```python
# Dot ball = valid delivery with 0 runs
dot_balls = len(player_deliveries[
    (player_deliveries['total_runs'] == 0) &
    (player_deliveries['extras_type'] != 'wides') &
    (player_deliveries['extras_type'] != 'noballs')
])
```

**Impact:** Dot ball counts will be accurate

---

### FIX #8: Best Figures (Lines 352-361)

**Current Code:**
```python
match_stats = player_deliveries.groupby('match_id').agg({
    'is_wicket': 'sum',
    'total_runs': 'sum'
}).reset_index()
```

**Issue:**
- Uses `total_runs` which includes leg byes and byes
- Should use corrected runs_conceded

**NEW CODE:**
```python
# Calculate best figures with correct runs conceded
best_figures_data = []
for match_id in player_deliveries['match_id'].unique():
    match_data = player_deliveries[player_deliveries['match_id'] == match_id]
    wickets = match_data['is_wicket'].sum()
    runs = match_data[
        ~match_data['extras_type'].isin(['legbyes', 'byes'])
    ]['total_runs'].sum()
    best_figures_data.append({'match_id': match_id, 'wickets': wickets, 'runs': runs})

best_match = max(best_figures_data, key=lambda x: x['wickets'], default={'wickets': 0, 'runs': 0})
best_figures = f"{int(best_match['wickets'])}/{int(best_match['runs'])}"
```

---

### FIX #9: Maiden Overs (Line 367)

**Current Code:**
```python
over_runs = player_deliveries.groupby(['match_id', 'inning', 'over'])['total_runs'].sum()
maiden_overs = len(over_runs[over_runs == 0])
```

**Issue:**
- An over might have wides/no balls but still be maiden (0 runs off bat)
- Current code counts any over with 0 total_runs
- A true maiden = 6 valid deliveries with 0 runs

**RECOMMENDED VERIFICATION:**
```python
# A maiden over = 0 total runs in a group of 6 valid deliveries
# This is partially correct, but verify that:
# 1. Each over group has exactly 6 deliveries (or 5 if final over)
# 2. We're not counting wides/no balls that added extra deliveries

maiden_data = []
for (match_id, inning, over), group in player_deliveries.groupby(['match_id', 'inning', 'over']):
    valid_deliveries = len(group[
        (group['extras_type'] != 'wides') &
        (group['extras_type'] != 'noballs')
    ])
    total_runs_in_over = group['total_runs'].sum()
    # It's maiden if: has at least 5 valid deliveries AND 0 total runs
    if total_runs_in_over == 0 and valid_deliveries >= 5:
        maiden_data.append((match_id, inning, over))

maiden_overs = len(maiden_data)
```

---

## IMPLEMENTATION STEPS

### Step 1: Add Helper Function (after line 267)
```python
def _count_dismissals(self, player_deliveries: pd.DataFrame) -> int:
    """Count unique innings where player got dismissed"""
    dismissals = player_deliveries[player_deliveries['is_wicket'] == 1][
        ['match_id', 'inning']
    ].drop_duplicates().shape[0]
    return dismissals

def _get_valid_deliveries(self, player_deliveries: pd.DataFrame) -> pd.DataFrame:
    """Filter for valid deliveries (excluding wides and no balls)"""
    return player_deliveries[
        (player_deliveries['extras_type'] != 'wides') &
        (player_deliveries['extras_type'] != 'noballs')
    ]

def _get_bowler_credited_runs(self, player_deliveries: pd.DataFrame) -> int:
    """Get runs conceded by bowler (excluding leg byes and byes)"""
    return player_deliveries[
        ~player_deliveries['extras_type'].isin(['legbyes', 'byes'])
    ]['total_runs'].sum()
```

### Step 2: Update _get_batting_stats() (Lines 270-310)

Replace entire method with corrected version using helper functions.

### Step 3: Update _get_bowling_stats() (Lines 320-390)

Replace entire method with corrected version using helper functions.

### Step 4: Test Against Known Players

Sample test queries:
- Virat Kohli: average should match official IPL stats
- Jasprit Bumrah: economy should match official stats
- MS Dhoni: average and not-out count should be correct

### Step 5: Verify with Official Statistics

Cross-check against:
- IPL official website
- ESPN Cricinfo
- CricketInfo database

---

## RISK ASSESSMENT

| Fix | Risk | Mitigation |
|-----|------|-----------|
| Batting Average | High - changes all averages | Compare with official stats, git commit before/after |
| Strike Rate | Medium - affects many players | Verify with sample players |
| Bowling Economy | High - changes all economies | Cross-check with official IPL stats |
| Dot Balls | Low - informational only | No downstream impact |
| Best Figures | Medium - display metric | Verify format is correct |
| Maiden Overs | Low - informational only | Count should decrease or stay same |

---

## DEPLOYMENT CHECKLIST

- [ ] Read and understand entire stats_engine.py
- [ ] Add helper functions for calculating dismissals, valid deliveries, bowler-credited runs
- [ ] Update _get_batting_stats() with fixes #1, #2, #3
- [ ] Update _get_bowling_stats() with fixes #4, #5, #6, #7, #8
- [ ] Verify maiden over logic (fix #9)
- [ ] Test with 5-10 known players
- [ ] Compare results against official IPL statistics
- [ ] Commit changes with detailed message
- [ ] Push to GitHub
- [ ] Monitor Streamlit Cloud deployment

---

**Created**: 27 January 2026
**Status**: Ready for Implementation
**Files to Modify**: stats_engine.py (Lines 270-390)
