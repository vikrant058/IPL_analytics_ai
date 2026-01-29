# IPL Analytics Chatbot - Comprehensive Filter Support

## Overview
The IPL Analytics chatbot has been enhanced to understand and process **ALL primary and secondary cricket variables** through natural language, enabling complex multi-filter queries.

---

## Primary Variables

### 1. **Batter/Player**
Query individual cricket player statistics
```
"virat kohli"
"kohli stats"
"sky"
```

### 2. **Bowler/Player**
Query individual bowler statistics
```
"jasprit bumrah"
"bumrah"
"chahal"
```

### 3. **Opposition Team**
Analyze player stats against specific teams
```
"kohli vs csk"
"bumrah against mumbai"
"sharma vs delhi"
```

### 4. **Team vs Team**
Compare team statistics
```
"mumbai vs delhi"
"csk against rcb"
```

---

## Secondary Variables (All Filters)

### 1. **Match Phase**
- **powerplay** (overs 0-6): Opening phase
- **middle_overs** (overs 6-16): Middle phase
- **death_overs** (overs 16-20): Final overs
- **opening** (overs 0-3): First 3 overs
- **closing** (overs 17-20): Last 3 overs

```
"kohli in powerplay"
"bumrah in death overs"
"sharma in middle overs"
```

### 2. **Match Situation**
- **chasing**: Batting second (chasing target)
- **defending**: Batting first (defending total)
- **batting_first**: First innings
- **pressure_chase**: Tight chase situations
- **winning_position**: Team in dominant position

```
"kohli chasing"
"bumrah defending 150+"
"sharma batting first"
```

### 3. **Year/Season**
Extract any IPL year (2008-2025)
```
"kohli in 2024"
"bumrah statistics 2023"
"virat 2024 2025"
```

### 4. **Ground/Venue**
Analyze at specific IPL stadiums
```
"kohli at wankhede"
"bumrah in chinnaswamy"
"sharma eden gardens"
```

**Supported Grounds:**
- Wankhede Stadium (Mumbai)
- M Chinnaswamy Stadium (Bengaluru)
- Arun Jaitley Stadium (Delhi)
- Eden Gardens (Kolkata)
- MA Chidambaram Stadium (Chennai)
- Rajiv Gandhi International Stadium (Hyderabad)
- Narendra Modi Stadium (Ahmedabad)
- Sawai Mansingh Stadium (Jaipur)
- Dr DY Patil Sports Academy (Mumbai)
- Punjab Cricket Association IS Bindra Stadium (Mohali)
- And 5+ more venues

### 5. **Bowling Type**
Filter by type of bowler faced/used
```
"kohli vs pace"
"bumrah against spin"
"sharma vs left arm"
"sky against spinners"
```

**Types:**
- pace / fast_bowler
- spin / spinner
- left_arm
- right_arm

### 6. **Batter Handedness**
Analyze performance against specific handedness
```
"kohli vs left hander"
"bumrah against right handed"
"sharma vs left handed bowlers"
```

**Types:**
- left_handed
- right_handed

### 7. **Inning (Batting Order)**
Separate first and second innings analysis
```
"kohli inning 1"
"sharma inning 2"
"bumrah batting first"
"virat batting second"
```

**Types:**
- 1 = Batting first
- 2 = Batting second/Chasing

### 8. **Home/Away**
Home ground vs away matches
```
"kohli at home"
"bumrah away 2024"
"sharma home in powerplay"
```

**Types:**
- home
- away

### 9. **VS Conditions (Advanced)**
Detailed bowling type analysis
```
"kohli vs off spin"
"bumrah against leg spinners"
"sharma vs left arm pace"
```

**Types:**
- vs_pace
- vs_spin
- vs_off_spin
- vs_leg_spin
- vs_left_arm
- vs_right_arm
- vs_left_arm_spin
- vs_right_arm_spin

### 10. **Batter Role**
Playing position/order category
```
"kohli as opener"
"sharma middle order"
"sky finisher stats"
```

**Types:**
- opener
- middle_order
- lower_order
- finisher

---

## Query Examples

### Single Variable Queries
```
"virat kohli"                    → Batter stats
"bumrah"                          → Bowler stats
```

### Batter vs Opposition
```
"kohli vs bumrah"                 → Head-to-head stats
"kohli against csk"               → Batter vs team
```

### With Match Phase
```
"kohli in powerplay"              → Powerplay specialist
"bumrah death overs"              → Death overs performance
"sharma middle overs"             → Middle overs analysis
```

### With Match Situation
```
"kohli chasing"                   → Performance while chasing
"bumrah defending"                → Bowling while defending
"sharma batting first"            → Stats while batting first
```

### With Time/Year
```
"kohli in 2024"                   → 2024 stats
"bumrah 2023 2024"                → Multi-year comparison
```

### With Ground/Venue
```
"kohli at wankhede"               → Home ground stats
"bumrah chinnaswamy"              → Specific venue
"sharma delhi 2024"               → Venue + year
```

### With Opponent Handedness
```
"kohli vs left hander"            → Against LHB
"bumrah against right handed"     → Against RHB
"sharma left arm bowlers"         → Against specific type
```

### With Home/Away
```
"kohli at home"                   → Home matches
"bumrah away in death"            → Away death overs
"sharma home 2024"                → Home matches in 2024
```

### Complex Multi-Filter Queries
```
"kohli in powerplay chasing 2024"
→ Kohli's powerplay performance while chasing in 2024

"bumrah at wankhede in death overs 2024"
→ Bumrah's death overs record at Wankhede in 2024

"kohli vs bumrah in chinnaswamy powerplay"
→ H2H at Chinnaswamy stadium during powerplay

"sharma against left arm pace at home"
→ Sharma's record against left arm pace bowlers at home

"virat chasing in middle overs vs spin 2024"
→ Virat's stats chasing during middle overs against spin bowlers in 2024

"bumrah vs right handed batters in powerplay 2023 2024"
→ Bumrah's performance against RHB in powerplay across two seasons
```

---

## Architecture

### Components Enhanced

**1. openai_handler.py**
- `_extract_filter_keywords()`: Extracts 10 categories of filters
- `parse_query()`: GPT-4 powered natural language understanding
- Enhanced fallback parser with pattern matching
- Filter normalization and canonicalization

**2. stats_engine.py**
- `_apply_cricket_filters()`: Applies all filters to deliveries DataFrame
- Ground-based filtering
- Inning-based filtering
- Handedness-based filtering
- Match type filtering (home/away)

**3. Query Routing**
- `get_response()`: Routes queries to appropriate handlers
- `_get_player_stats_response()`: Single player analysis with all filters
- `_get_head_to_head_response()`: H2H comparison with all filters
- `_get_team_stats_response()`: Team statistics

---

## Filter Precedence & Combination

All filters work **composably**:
- Order doesn't matter: "powerplay 2024 kohli" = "kohli 2024 powerplay"
- Multiple filters combine: "kohli powerplay chasing 2024" applies ALL filters
- Filters narrow down dataset progressively
- No filter conflicts: complementary analysis

---

## Implementation Details

### Filter Extraction Method
```python
_extract_filter_keywords(query: str) -> Dict

Example:
"kohli vs csk at wankhede in 2024 powerplay" 
→ {
    'opposition_team': 'CSK',
    'ground': 'Wankhede Stadium',
    'seasons': [2024],
    'match_phase': 'powerplay'
}
```

### Query Parsing Method
```python
parse_query(query: str) -> Dict

Returns: {
    'player1': 'V Kohli',
    'player2': None,
    'opposition_team': 'Chennai Super Kings',
    'ground': 'Wankhede Stadium',
    'seasons': [2024],
    'match_phase': 'powerplay',
    'match_situation': None,
    'handedness': None,
    'inning': None,
    'match_type': None,
    'vs_conditions': None,
    'query_type': 'player_stats'
}
```

### Filter Application
```python
_apply_cricket_filters(deliveries_df: DataFrame, filters: Dict) -> DataFrame

Applies sequential filtering:
1. Opposition team filter
2. Match phase filter (overs 0-5 for powerplay, etc.)
3. Match situation filter (inning-based)
4. Bowler type filter
5. VS conditions filter
6. Ground/venue filter
7. Inning filter
8. Handedness filter
9. Match type filter (home/away)
```

---

## Testing

Created `quick_filter_test.py` with 9 comprehensive test cases:

✅ Filter extraction test: 9/9 passing
✅ All primary variables detected
✅ All secondary variables extracted
✅ Complex query combinations working
✅ Natural language parsing accurate

---

## Deployment Status

- ✅ Code pushed to GitHub (commit: ed82d88)
- ✅ Streamlit Cloud auto-deployment triggered
- Expected live: 2-3 minutes after push
- Public URL: https://cricketanalytics.streamlit.app/

---

## Future Enhancements

1. **Batter Role Detection**: Automatically detect batting position from match data
2. **Venue Aliases**: Expand ground name recognition (city names, old names)
3. **Form Indicators**: Recent form (last 5, last 10 matches)
4. **Head-to-Head Context**: Win/loss records in H2H
5. **Season Ranges**: "last 3 seasons", "since 2020"
6. **Player Comparisons**: "kohli vs sharma" (player vs player stats)
7. **Statistical Insights**: Trend analysis, form peaks
8. **Export Capabilities**: Download stats as CSV/JSON

---

## Example Conversation Flow

**User**: "How does Virat perform in the powerplay at home in 2024?"

**Chatbot Processing**:
1. Extract filters: match_phase='powerplay', match_type='home', seasons=[2024]
2. Identify player: 'V Kohli'
3. Query type: 'player_stats'
4. Apply filters to batting deliveries
5. Calculate stats: runs, strikes, averages
6. Generate insights with context

**Response**:
```
📊 **Virat Kohli - Powerplay Stats (Home, 2024)**
🏟️ Matches: 5
🏃 Runs: 287
⚡ Strike Rate: 145.68
🎯 Average: 57.4
🔥 Half-centuries: 1

Key Insights:
- Aggressive approach with SR 145.68
- Found gaps well with 15% dot balls
- Strong against pace bowlers
```

---

## Contact & Support

For issues or feature requests:
- GitHub: https://github.com/vikrant058/IPL_analytics_ai
- Issues: Report on GitHub issues
- Features: Suggest enhancements via PR
