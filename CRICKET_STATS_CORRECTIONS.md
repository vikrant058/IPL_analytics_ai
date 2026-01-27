# Cricket Statistics Corrections Based on Official Rules

## Reference Document
**Mens_Twenty20_International_Playing_Conditions-Effective_December_2023.pdf**

---

## CRITICAL CORRECTIONS NEEDED

### 1. **BATTING AVERAGE CALCULATION** ❌ INCORRECT
**Current Implementation (WRONG):**
```python
'average': round(runs / innings, 2) if innings > 0 else 0
```
**Cricket Rule**: Average = Runs / (Innings Where Player Got Out)
- **NOT OUT INNINGS MUST BE EXCLUDED** from the denominator
- Current code treats "Not Out" innings the same as "Out" innings

**Status in Code**: Line 299 in stats_engine.py - NEEDS FIX
**Impact**: All batting averages are INFLATED (denominator is too high)

**Fix Required**:
```python
# Count only innings where player got OUT (is_wicket == True for that innings)
out_innings = player_deliveries[player_deliveries['is_wicket'] == True]
# Count unique (match_id, inning) combinations where player got out
unique_out_innings = out_innings[out_innings['inning'].isin([1, 2])][
    ['match_id', 'inning']
].drop_duplicates().shape[0]

'average': round(runs / unique_out_innings, 2) if unique_out_innings > 0 else 0
```

---

### 2. **STRIKE RATE CALCULATION** ❌ PARTIALLY INCORRECT
**Current Implementation (WRONG):**
```python
'strike_rate': round((runs / balls * 100), 2) if balls > 0 else 0
```
**Cricket Rule**: Strike Rate = (Runs / Deliveries Faced) × 100
- **WIDES MUST NOT BE COUNTED** in deliveries faced
- Wides are extras, not valid deliveries for the batter

**Status in Code**: Line 300 in stats_engine.py - NEEDS FIX
**Impact**: Strike rates for batters facing many wides are UNDERSTATED

**Fix Required**:
```python
# Deliveries faced = All balls EXCEPT wides
deliveries_faced = len(player_deliveries[player_deliveries['wide_runs'] == 0])

'strike_rate': round((runs / deliveries_faced * 100), 2) if deliveries_faced > 0 else 0
```

---

### 3. **ECONOMY RATE CALCULATION** ❌ INCORRECT
**Current Implementation (WRONG):**
```python
'economy': round((runs_conceded / (balls / 6)), 2) if balls > 0 else 0
```
**Cricket Rule**: Economy = (Runs Conceded / Overs) where Runs = EXCLUDING LEG BYES & BYES
- **LEG BYES and BYES are NOT credited to bowler**
- These runs don't affect the bowler's economy
- Bowler only concedes: runs off bat + wides + no balls

**Status in Code**: Line 308 in stats_engine.py - NEEDS FIX
**Impact**: Economy rates are INFLATED if bowlers conceded many leg byes/byes

**Fix Required**:
```python
# Runs conceded = EXCLUDING leg_byes and byes
runs_conceded = (
    player_deliveries['runs_off_bat'].sum() + 
    player_deliveries['wide_runs'].sum() + 
    player_deliveries['no_ball_runs'].sum()
)

'economy': round((runs_conceded / (balls / 6)), 2) if balls > 0 else 0
```

---

### 4. **BOWLING AVERAGE CALCULATION** ❌ INCORRECT  
**Current Implementation (WRONG):**
```python
'average': round(runs_conceded / wickets, 2) if wickets > 0 else 0
```
**Cricket Rule**: Bowling Average = Runs Conceded / Wickets (Same issue as #3)
- **MUST use corrected runs conceded** (excluding leg byes & byes)

**Status in Code**: Line 309 in stats_engine.py - NEEDS FIX

**Fix Required**:
```python
# Use corrected runs_conceded from fix #3
'average': round(runs_conceded / wickets, 2) if wickets > 0 else 0
```

---

### 5. **DOTS BALLS COUNTED INCORRECTLY** ❌ INCORRECT
**Current Implementation (WRONG):**
```python
# Batting: dot_balls = len(player_deliveries[player_deliveries['batsman_runs'] == 0])
# Bowling: dot_balls = len(player_deliveries[player_deliveries['total_runs'] == 0])
```
**Cricket Rule**: A dot ball is a valid delivery with 0 runs
- **WIDES and NO BALLS are not valid deliveries**, so they're not dots
- A wide with 0 runs is NOT a dot ball

**Status in Code**: Lines 284, 299 (batting), Lines 309, 311 (bowling) - NEEDS FIX
**Impact**: Dot ball counts and percentages are INFLATED

**Fix Required**:
```python
# Batting: dot balls = valid deliveries with 0 runs (excluding wides)
dot_balls_batting = len(player_deliveries[
    (player_deliveries['batsman_runs'] == 0) & 
    (player_deliveries['wide_runs'] == 0)
])

# Bowling: dot balls = valid deliveries with 0 runs (excluding wides & no balls)
dot_balls_bowling = len(player_deliveries[
    (player_deliveries['total_runs'] == 0) & 
    (player_deliveries['wide_runs'] == 0) &
    (player_deliveries['no_ball_runs'] == 0)
])
```

---

### 6. **INNINGS COUNT ISSUE** ⚠️ NEEDS CLARIFICATION
**Current Implementation**:
```python
valid_innings = player_deliveries[player_deliveries['inning'].isin([1, 2])][
    ['match_id', 'inning']
].drop_duplicates()
innings = valid_innings.shape[0]
```
**Question**: Does this include NOT OUT innings in the count?
- For **batting**: Typically YES, we count all innings (both out and not out)
- For **bowling**: YES, we count all overs bowled in each inning

**Status**: Seems correct but VERIFY that the 'is_wicket' flag properly identifies not-outs
- If is_wicket == False for an entire inning, player was not out ✓
- If is_wicket == True at some point, player was out ✓

---

### 7. **MAIDEN OVERS CALCULATION** ⚠️ VERIFY
**Current Implementation**:
```python
over_runs = player_deliveries.groupby(['match_id', 'inning', 'over'])['total_runs'].sum()
maiden_overs = len(over_runs[over_runs == 0])
```
**Cricket Rule**: A maiden over is 6 valid deliveries (not wides/no balls) with 0 runs
- **MUST verify that the over count excludes wides and no balls**

**Status**: Line 323 - NEEDS VERIFICATION
**Potential Issue**: If an over has wides/no balls, it might be counted as maiden incorrectly

**Fix Required**:
```python
# Group by over and check: 6 valid deliveries with 0 total runs
over_data = player_deliveries.groupby(['match_id', 'inning', 'over']).agg({
    'total_runs': 'sum',
    'wide_runs': 'sum',
    'no_ball_runs': 'sum'
}).reset_index()

# Maiden over = 0 total runs AND 0 wides AND 0 no balls
maiden_overs = len(over_data[
    (over_data['total_runs'] == 0) & 
    (over_data['wide_runs'] == 0) &
    (over_data['no_ball_runs'] == 0)
])
```

---

### 8. **BEST FIGURES CALCULATION** ❌ INCORRECT
**Current Implementation (WRONG):**
```python
best_runs = int(match_stats.loc[best_match_idx, 'total_runs'])
best_figures = f"{best_wickets}/{best_runs}"
```
**Cricket Rule**: Best figures are W/R where R = runs conceded (excluding leg byes & byes)
- **MUST use corrected runs** (same as bowling average fix)

**Status in Code**: Lines 316-321 - NEEDS FIX

**Fix Required**:
```python
# Calculate runs correctly for each match
match_stats = player_deliveries.groupby('match_id').agg({
    'is_wicket': 'sum',
    'runs_off_bat': 'sum',
    'wide_runs': 'sum',
    'no_ball_runs': 'sum'
}).reset_index()

match_stats['runs_conceded'] = (
    match_stats['runs_off_bat'] + 
    match_stats['wide_runs'] + 
    match_stats['no_ball_runs']
)

best_match_idx = match_stats['is_wicket'].idxmax()
best_wickets = int(match_stats.loc[best_match_idx, 'is_wicket'])
best_runs = int(match_stats.loc[best_match_idx, 'runs_conceded'])
best_figures = f"{best_wickets}/{best_runs}"
```

---

### 9. **HIGHEST SCORE CALCULATION** ❌ POTENTIALLY WRONG
**Current Implementation**:
```python
match_scores = player_deliveries.groupby('match_id')['batsman_runs'].sum()
highest_score = int(match_scores.max()) if len(match_scores) > 0 else 0
```
**Question**: Is this counting all deliveries correctly?
- **Issue**: If deliveries include extras (wides, no balls), they shouldn't contribute to individual score
- A batter's score = runs off bat + leg byes + byes

**Status**: Line 290 - NEEDS VERIFICATION
**Potential Issue**: Wides and no balls might be miscounted

**Fix Required** (if needed):
```python
# A batter's actual runs = runs off bat + leg byes + byes (NOT wides/no balls)
match_scores = player_deliveries.groupby('match_id').agg({
    'batsman_runs': 'sum'  # This should be correct if batsman_runs excludes team extras
}).reset_index()
highest_score = int(match_scores['batsman_runs'].max()) if len(match_scores) > 0 else 0
```

---

## SUMMARY OF FIXES NEEDED

| # | Metric | Status | Severity | Location |
|---|--------|--------|----------|----------|
| 1 | Batting Average | ❌ WRONG | **CRITICAL** | Line 299 |
| 2 | Strike Rate | ❌ WRONG | **HIGH** | Line 300 |
| 3 | Economy Rate | ❌ WRONG | **CRITICAL** | Line 308 |
| 4 | Bowling Average | ❌ WRONG | **CRITICAL** | Line 309 |
| 5 | Dot Balls | ❌ WRONG | HIGH | Lines 284, 299, 309, 311 |
| 6 | Innings Count | ⚠️ VERIFY | MEDIUM | Line 272, 303 |
| 7 | Maiden Overs | ⚠️ VERIFY | MEDIUM | Line 323 |
| 8 | Best Figures | ❌ WRONG | **CRITICAL** | Lines 316-321 |
| 9 | Highest Score | ⚠️ VERIFY | LOW | Line 290 |

---

## IMPLEMENTATION PRIORITY

### Phase 1 (CRITICAL - Do First):
1. Fix Batting Average (exclude not-outs)
2. Fix Economy Rate (exclude leg byes & byes)
3. Fix Bowling Average (use correct runs)
4. Fix Best Figures (use correct runs)

### Phase 2 (HIGH):
5. Fix Strike Rate (exclude wides from deliveries)
6. Fix Dot Balls (exclude wides & no balls)

### Phase 3 (MEDIUM):
7. Verify Innings Count logic
8. Fix Maiden Overs calculation

### Phase 4 (LOW):
9. Verify Highest Score calculation

---

## REQUIRED DATA FIELDS

Ensure your deliveries_df has these columns:
- `is_wicket` - Boolean, True if batter got out
- `batsman_runs` - Runs scored off the bat
- `wide_runs` - Runs from wides (should be in extra_runs)
- `no_ball_runs` - Runs from no balls (should be in extra_runs)
- `leg_bye_runs` - Runs from leg byes
- `bye_runs` - Runs from byes
- `total_runs` - Sum of all runs in a delivery
- `runs_off_bat` - Alternative to batsman_runs
- `extra_runs` - Contains wides + no balls + byes + leg byes

---

## VERIFICATION CHECKLIST

Before deploying fixes:
- [ ] Check sample player data: Compare calculated averages against CricketInfo/ESPN
- [ ] Verify leg bye vs bye separation in data
- [ ] Confirm wide ball data is properly flagged
- [ ] Test with known players (e.g., Virat Kohli)
- [ ] Compare with official IPL statistics

---

**Last Updated**: 27 January 2026
**Status**: Analysis Complete - Ready for Implementation
