# Advanced Filters for AI Analytics Engine

## ✅ Currently Implemented Filters

### 1. **Match Phase / Overs**
- **Powerplay** (Overs 1-6): Aggressive batting restrictions
- **Middle Overs** (Overs 6-15.6): Consolidation phase
- **Death Overs** (Overs 16-20): Final push, high risk-reward

**Example Query**: "kohli's powerplay performance" → Shows stats from first 6 overs only

### 2. **Bowler Type**
- **Pace**: Fast bowlers (>130 km/h)
- **Spin**: Spinners (off-spin, leg-spin)
- **Left-arm**: All left-arm bowlers
- **Right-arm**: All right-arm bowlers
- **Off-Spinner**: Specific spin type
- **Leg-Spinner**: Specific spin type

**Example Query**: "rohit vs pace bowlers" → Shows how Rohit performs against fast bowling

### 3. **Batter Role**
- **Opener**: Top 2 positions
- **Middle Order**: Positions 3-5
- **Lower Order**: Positions 6+

**Example Query**: "virat as opener stats" → Filters stats when Kohli bats at #1

### 4. **Conditions (vs_conditions)**
- **vs_pace**: Performance against fast bowlers
- **vs_spin**: Performance against spinners
- **home**: Matches at home venue
- **away**: Matches at away venues

### 5. **Season Filter**
- Single or multiple seasons (2008-2025)

---

## 🎯 Recommended Advanced Filters to Add

### A. **Match Context Filters**

#### 1. **Match Situation**
```
match_situation: 'batting_first' | 'chasing' | 'pressure_chase' | 'comfortable_position'
```
- **Batting First**: Team batting in first innings
- **Chasing**: Team chasing target
- **Pressure Chase**: Chasing by small margins (< 20 runs/over needed)
- **Comfortable Position**: Chasing with easy rate (< 8 runs/over needed)

**Example Query**: "How does Kohli perform in pressure chases?"
→ Shows stats when RRR > 10 runs/over

#### 2. **Match Type / Tournament Phase**
```
match_type: 'league_stage' | 'qualifier' | 'eliminator' | 'final'
```
- Different performance patterns in different match intensities

**Example Query**: "Bumrah's performance in knockout matches"

#### 3. **Toss Decision Impact**
```
toss_decision: 'bat_first' | 'field_first'
```
- How conditions affect performance when batting/fielding first

---

### B. **Opposition & Head-to-Head Filters**

#### 1. **Opposition Type**
```
opposition_type: 'strong_team' | 'weak_team' | 'top_4_team' | 'bottom_4_team'
```
- Based on win percentage rankings

#### 2. **Head-to-Head Specific**
```
h2h_context: 'career_average_vs_opponent' | 'recent_encounters' | 'home_vs_away'
```

**Example Query**: "Rohit vs Bumrah: head-to-head at different venues"

---

### C. **Performance Context Filters**

#### 1. **Player Form/Consistency**
```
form: 'recent_form' | 'peak_performance' | 'slump_phase' | 'consistent_period'
```
- **Recent Form**: Last 10 matches
- **Peak Performance**: Top 10% performances
- **Slump Phase**: Bottom 10% performances
- **Consistent Period**: Standard deviation < threshold

**Example Query**: "Kohli's stats during peak form"

#### 2. **Rest & Recovery**
```
rest_status: 'fresh' | 'tired' | 'after_break'
```
- Games after long rest vs consecutive matches

#### 3. **Strike Rate / Aggression**
```
aggression: 'conservative' | 'moderate' | 'aggressive' | 'ultra_aggressive'
```
- Grouped by strike rate ranges (SR < 100, 100-130, 130-150, > 150)

---

### D. **Venue & Conditions**

#### 1. **Venue Type**
```
venue_type: 'batting_friendly' | 'bowling_friendly' | 'balanced' | 'high_scoring' | 'low_scoring'
```
- Classified by historical average scores

#### 2. **Ground Size**
```
ground_size: 'small' | 'medium' | 'large'
```
- Affects 6-hitting ability and scoring patterns

#### 3. **Pitch Characteristics** (if data available)
```
pitch: 'batting_track' | 'bowling_track' | 'turning_track'
```

---

### E. **Partnership & Innings Context**

#### 1. **Partnership Analysis**
```
partnership_type: 'opening_partnership' | 'recovery_partnership' | 'aggressive_partnership' | 'final_overs_partnership'
```

#### 2. **Innings Situation**
```
innings_position: 'early_innings' | 'middle_innings' | 'end_innings'
```
- Overs 1-8, 9-16, 17-20

#### 3. **Partnership Duration**
```
partnership_length: 'short_partnership' | 'long_partnership'
```
- By number of runs or balls

---

### F. **Historical & Comparative Filters**

#### 1. **Year-on-Year Trends**
```
year_comparison: 'improvement' | 'decline' | 'consistent' | 'surge'
```

#### 2. **Career Stage**
```
career_stage: 'early_career' | 'peak_years' | 'late_career'
```

#### 3. **Playing Role Evolution**
```
role_evolution: 'opener_to_middle_order' | 'specialist_role_change' | 'leadership_impact'
```

---

### G. **Pressure & Match Context**

#### 1. **Pressure Index**
```
pressure_level: 'high_pressure' | 'medium_pressure' | 'low_pressure'
```
- Calculated by:
  - Match importance (knockout vs league)
  - RRR (required run rate)
  - Wickets lost
  - Target proximity

#### 2. **Comeback Performance**
```
comeback_context: 'after_poor_innings' | 'after_injury' | 'recall_performance'
```

#### 3. **Match Impact**
```
match_impact: 'match_winner' | 'match_losing' | 'supporting_role' | 'game_changer'
```

---

## 📊 Implementation Priority

### Phase 1 (HIGH) - Implement First
- ✅ Match Phase (already done)
- ✅ Bowler Type (already done)
- Match Situation (batting_first vs chasing)
- Opposition Type (strong vs weak team)
- Venue Type (batting-friendly vs bowling-friendly)

### Phase 2 (MEDIUM) - Next
- Player Form (recent, peak, consistent)
- Ground Size
- Partnership Type
- Career Stage
- Pressure Index

### Phase 3 (LOWER) - Future Enhancement
- Pitch Characteristics
- Role Evolution
- Weather conditions
- Historical trends

---

## 📝 Example Queries After Implementation

```
"Kohli's average in pressure chases against pace bowlers in powerplay at away venues"
→ Filters: chasing, pressure_chase, vs_pace, powerplay, away, player1=kohli

"Compare Bumrah vs Malinga in death overs during knockout matches"
→ Filters: death_overs, match_type=knockout, bowler_type comparison

"Rohit's performance when batting first vs chasing in high-scoring venues"
→ Filters: batting_first vs chasing, venue_type=high_scoring, player1=rohit

"How consistent is Dhoni in peak form vs slump phase?"
→ Filters: form comparison (peak vs slump), player1=dhoni
```

---

## 🔧 Technical Implementation Notes

1. **Overs Classification**: 
   - Powerplay: 0-6 (balls 0-36)
   - Middle: 6-15.6 (balls 36-94)
   - Death: 16-20 (balls 94-120)

2. **Bowler Type Detection**:
   - Create `bowler_characteristics` table from bowling economy, speed, variations
   - Use clustering to identify spin vs pace

3. **Opposition Strength**:
   - Calculate from historical win %
   - Dynamic ranking by season

4. **Pressure Index Formula**:
   - `pressure = (match_importance_score × rr_multiplier × wicket_factor) / target_proximity`

5. **Form Definition**:
   - Recent: Last 10 matches
   - Peak: Top quartile by runs scored
   - Consistent: Low variance in last 10 matches
   - Slump: Bottom quartile

---

## ✨ Expected Benefits

- **Better Insights**: Understand performance in specific contexts
- **Tactical Analysis**: Find strengths/weaknesses in particular situations
- **Prediction Accuracy**: More granular data for ML models
- **Narrative Generation**: Rich stories from filtered data
- **Scout Recommendations**: AI can suggest optimal XI based on opposition/conditions
