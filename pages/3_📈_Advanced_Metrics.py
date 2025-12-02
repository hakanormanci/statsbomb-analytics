"""
StatsBomb Match Metrics Dashboard
Detaylı maç metrikleri ve analizi

Dosya yolu: pages/3_📊_Match_Metrics.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import seaborn as sns
from math import pi
import os
import json

# BASE URL
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/refs/heads/master/data/"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Match Metrics - StatsBomb",
    page_icon="📊",
    layout="wide"
)

# CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stat-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def load_from_local(url):
    """Lokal dosyadan veri oku"""
    import os
    import json
    
    # URL'den dosya yolunu çıkar
    # Örnek: ".../data/events/123.json" → "data/events/123.json"
    if "/competitions.json" in url:
        local_path = "data/competitions.json"
    elif "/matches/" in url:
        parts = url.split("/matches/")[1]  # "11/90.json"
        local_path = f"data/matches/{parts}"
    elif "/events/" in url:
        parts = url.split("/events/")[1]  # "3895292.json"
        local_path = f"data/events/{parts}"
    elif "/lineups/" in url:
        parts = url.split("/lineups/")[1]
        local_path = f"data/lineups/{parts}"
    else:
        return None
    
    # Dosya varsa oku
    if os.path.exists(local_path):
        with open(local_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        st.error(f"❌ File not found: {local_path}")
        return None

@st.cache_data(ttl=3600)
def load_match_info(match_id):
    """Maç bilgilerini yükle"""
    competitions_url = f"{BASE_URL}competitions.json"
    competitions_data = load_from_local(competitions_url)
    
    if not competitions_data:
        return None
    
    competitions = pd.DataFrame(competitions_data)
    
    for _, comp in competitions.iterrows():
        matches_url = f"{BASE_URL}matches/{comp['competition_id']}/{comp['season_id']}.json"
        matches_data = load_from_local(matches_url)
        
        if matches_data:
            matches = pd.DataFrame(matches_data)
            match_info = matches[matches['match_id'] == match_id]
            
            if len(match_info) > 0:
                return match_info.iloc[0]
    
    return None

@st.cache_data(ttl=3600)
def load_events(match_id):
    """Maç olaylarını yükle"""
    url = f"{BASE_URL}events/{match_id}.json"
    data = load_from_local(url)
    
    if data:
        return pd.DataFrame(data)
    return None

def calculate_attacking_metrics(events_df, team_name):
    """Ofansif metrikleri hesapla"""
    # Team events
    events_df['team_name'] = events_df['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    team_events = events_df[events_df['team_name'] == team_name]
    
    # Shots
    shots = team_events[team_events['type'].apply(lambda x: x['name'] == 'Shot')]
    
    # xG
    total_xg = shots['shot'].apply(
        lambda x: x.get('statsbomb_xg', 0) if isinstance(x, dict) else 0
    ).sum()
    
    # Goals
    goals = shots[shots['shot'].apply(
        lambda x: x.get('outcome', {}).get('name') == 'Goal' if isinstance(x, dict) else False
    )]
    
    # Shots on target
    on_target = shots[shots['shot'].apply(
        lambda x: x.get('outcome', {}).get('name') in ['Goal', 'Saved'] if isinstance(x, dict) else False
    )]
    
    # Big chances (xG > 0.3)
    big_chances = shots[shots['shot'].apply(
        lambda x: x.get('statsbomb_xg', 0) > 0.3 if isinstance(x, dict) else False
    )]
    
    # Box shots vs outside
    box_shots = shots[shots['location'].apply(
        lambda x: x[0] >= 102 if x and len(x) > 0 else False
    )]
    
    metrics = {
        'Total Shots': len(shots),
        'Shots on Target': len(on_target),
        'Goals': len(goals),
        'xG': total_xg,
        'xG per Shot': total_xg / len(shots) if len(shots) > 0 else 0,
        'Conversion Rate (%)': (len(goals) / len(shots) * 100) if len(shots) > 0 else 0,
        'Shot Accuracy (%)': (len(on_target) / len(shots) * 100) if len(shots) > 0 else 0,
        'Big Chances': len(big_chances),
        'Box Shots': len(box_shots),
        'Outside Box Shots': len(shots) - len(box_shots),
        'xG Overperformance': len(goals) - total_xg
    }
    
    return metrics, shots

def calculate_passing_metrics(events_df, team_name):
    """Paslaşma metrikleri hesapla"""
    events_df['team_name'] = events_df['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    team_events = events_df[events_df['team_name'] == team_name]
    
    # All passes - sadece recipient bilgisi olanlar
    all_passes = team_events[team_events['type'].apply(lambda x: x['name'] == 'Pass')].copy()
    
    # Sadece recipient bilgisi olan pasları say (tutarlılık için)
    passes = []
    for _, row in all_passes.iterrows():
        pass_dict = row.get('pass')
        if isinstance(pass_dict, dict):
            recipient_info = pass_dict.get('recipient')
            if recipient_info:  # Recipient varsa
                passes.append(row)
    
    passes = pd.DataFrame(passes) if passes else pd.DataFrame()
    
    # Successful passes
    successful = passes[passes['pass'].apply(
        lambda x: x.get('outcome') is None if isinstance(x, dict) else False
    )]
    
    # Progressive passes (10m+ forward)
    progressive = []
    for _, row in passes.iterrows():
        start_loc = row.get('location')
        pass_dict = row.get('pass')
        if isinstance(pass_dict, dict):
            end_loc = pass_dict.get('end_location')
            if start_loc and end_loc:
                if end_loc[0] - start_loc[0] >= 10:  # 10m+ ileri
                    progressive.append(row)
    
    progressive_df = pd.DataFrame(progressive) if progressive else pd.DataFrame()
    
    # Final third passes
    final_third = passes[passes['location'].apply(
        lambda x: x[0] >= 80 if x and len(x) > 0 else False
    )]
    
    # Penalty area passes
    penalty_area = passes[passes['pass'].apply(
        lambda x: (x.get('end_location', [0, 0])[0] >= 102 and 
                   18 <= x.get('end_location', [0, 0])[1] <= 62) 
        if isinstance(x, dict) else False
    )]
    
    # Long passes (30m+)
    long_passes = passes[passes['pass'].apply(
        lambda x: x.get('length', 0) >= 30 if isinstance(x, dict) else False
    )]
    
    long_successful = long_passes[long_passes['pass'].apply(
        lambda x: x.get('outcome') is None if isinstance(x, dict) else False
    )]
    
    metrics = {
        'Total Passes': len(passes),
        'Completed Passes': len(successful),
        'Pass Accuracy (%)': (len(successful) / len(passes) * 100) if len(passes) > 0 else 0,
        'Progressive Passes': len(progressive_df),
        'Final Third Passes': len(final_third),
        'Penalty Area Passes': len(penalty_area),
        'Long Passes (30m+)': len(long_passes),
        'Long Pass Accuracy (%)': (len(long_successful) / len(long_passes) * 100) if len(long_passes) > 0 else 0,
        'Avg Pass Length (m)': passes['pass'].apply(
            lambda x: x.get('length', 0) if isinstance(x, dict) else 0
        ).mean() if len(passes) > 0 else 0
    }
    
    return metrics

def calculate_defensive_metrics(events_df, team_name):
    """Defansif metrikleri hesapla"""
    events_df['team_name'] = events_df['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    team_events = events_df[events_df['team_name'] == team_name]
    
    # Defensive actions
    tackles = team_events[team_events['type'].apply(lambda x: x.get('name') == 'Duel')]
    interceptions = team_events[team_events['type'].apply(lambda x: x.get('name') == 'Interception')]
    blocks = team_events[team_events['type'].apply(lambda x: x.get('name') == 'Block')]
    clearances = team_events[team_events['type'].apply(lambda x: x.get('name') == 'Clearance')]
    pressures = team_events[team_events['type'].apply(lambda x: x.get('name') == 'Pressure')]
    
    # PPDA calculation (opponent passes per defensive action)
    opponent_events = events_df[events_df['team_name'] != team_name]
    opponent_passes = opponent_events[opponent_events['type'].apply(lambda x: x['name'] == 'Pass')]
    
    defensive_actions = len(tackles) + len(interceptions) + len(blocks)
    ppda = len(opponent_passes) / defensive_actions if defensive_actions > 0 else 0
    
    metrics = {
        'Tackles': len(tackles),
        'Interceptions': len(interceptions),
        'Blocks': len(blocks),
        'Clearances': len(clearances),
        'Pressures': len(pressures),
        'Total Defensive Actions': defensive_actions,
        'PPDA': ppda,
        'Recoveries': len(team_events[team_events['type'].apply(lambda x: x.get('name') == 'Ball Recovery')])
    }
    
    return metrics

def plot_xg_comparison(home_metrics, away_metrics, home_team, away_team):
    """xG karşılaştırma grafiği"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    teams = [home_team, away_team]
    xg_values = [home_metrics['xG'], away_metrics['xG']]
    goals = [home_metrics['Goals'], away_metrics['Goals']]
    
    x = np.arange(len(teams))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, xg_values, width, label='xG', color='skyblue', alpha=0.8)
    bars2 = ax.bar(x + width/2, goals, width, label='Goals', color='green', alpha=0.8)
    
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title('xG vs Actual Goals', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(teams)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def plot_radar_chart(home_metrics, away_metrics, home_team, away_team):
    """Radar chart karşılaştırma"""
    categories = ['Shot Accuracy', 'Pass Accuracy', 'Progressive\nPasses', 
                  'Defensive\nActions', 'Pressures']
    
    # Normalize values (0-100)
    home_values = [
        home_metrics['attacking']['Shot Accuracy (%)'],
        home_metrics['passing']['Pass Accuracy (%)'],
        min(home_metrics['passing']['Progressive Passes'] / 50 * 100, 100),  # Normalize to max 50
        min(home_metrics['defensive']['Total Defensive Actions'] / 100 * 100, 100),  # Normalize to max 100
        min(home_metrics['defensive']['Pressures'] / 200 * 100, 100)  # Normalize to max 200
    ]
    
    away_values = [
        away_metrics['attacking']['Shot Accuracy (%)'],
        away_metrics['passing']['Pass Accuracy (%)'],
        min(away_metrics['passing']['Progressive Passes'] / 50 * 100, 100),
        min(away_metrics['defensive']['Total Defensive Actions'] / 100 * 100, 100),
        min(away_metrics['defensive']['Pressures'] / 200 * 100, 100)
    ]
    
    # Number of variables
    num_vars = len(categories)
    
    # Compute angle for each axis
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    home_values += home_values[:1]
    away_values += away_values[:1]
    angles += angles[:1]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, home_values, 'o-', linewidth=2, label=home_team, color='blue')
    ax.fill(angles, home_values, alpha=0.25, color='blue')
    
    ax.plot(angles, away_values, 'o-', linewidth=2, label=away_team, color='red')
    ax.fill(angles, away_values, alpha=0.25, color='red')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100)
    ax.set_title('Team Performance Comparison', size=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)
    
    return fig

def main():
    st.markdown("# 📊 Match Metrics Dashboard")
    
    # Sidebar - Match ID
    st.sidebar.header("⚙️ Settings")
    
    # Session state'ten match ID al
    if 'selected_match_id' in st.session_state:
        default_match_id = st.session_state.selected_match_id
    else:
        default_match_id = 3895292
    
    match_id = st.sidebar.number_input("Match ID", value=default_match_id, step=1)
    
    if st.sidebar.button("🔄 Reload Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner('📥 Loading match data...'):
        match_info = load_match_info(match_id)
        events = load_events(match_id)
    
    if events is None or match_info is None:
        st.error("❌ Failed to load match data!")
        return
    
    # Extract team names
    if isinstance(match_info['home_team'], dict):
        home_team = match_info['home_team'].get('home_team_name')
        away_team = match_info['away_team'].get('away_team_name')
    else:
        home_team = match_info['home_team']
        away_team = match_info['away_team']
    
    home_score = match_info['home_score']
    away_score = match_info['away_score']
    
    # Header
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;'>
            <h1 style='margin: 0;'>{home_team} {home_score} - {away_score} {away_team}</h1>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem;'>Match ID: {match_id}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Calculate all metrics
    with st.spinner('📊 Calculating metrics...'):
        home_attacking, home_shots = calculate_attacking_metrics(events, home_team)
        away_attacking, away_shots = calculate_attacking_metrics(events, away_team)
        
        home_passing = calculate_passing_metrics(events, home_team)
        away_passing = calculate_passing_metrics(events, away_team)
        
        home_defensive = calculate_defensive_metrics(events, home_team)
        away_defensive = calculate_defensive_metrics(events, away_team)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏠 xG", f"{home_attacking['xG']:.2f}")
    with col2:
        st.metric("✈️ xG", f"{away_attacking['xG']:.2f}")
    with col3:
        st.metric("🏠 Shots", home_attacking['Total Shots'])
    with col4:
        st.metric("✈️ Shots", away_attacking['Total Shots'])
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚽ Attacking", 
        "🔗 Passing", 
        "🛡️ Defensive", 
        "⚖️ Comparison",
        "👥 Players"
    ])
    
    # TAB 1: ATTACKING
    with tab1:
        st.markdown("## ⚽ Attacking Metrics")
        
        # Info box with explanations
        with st.expander("ℹ️ Metric Explanations", expanded=False):
            st.markdown("""
            **Total Shots:** All shot attempts (on/off target, blocked, saved)
            
            **Shots on Target:** Shots that would go in if not saved (goals + saves)
            
            **Goals:** Shots that resulted in a goal
            
            **xG (Expected Goals):** Probability of scoring based on shot quality (location, angle, body part, etc.). Sum of all shot probabilities.
            
            **xG per Shot:** Average quality of shots. Higher = better chances created.
            
            **Conversion Rate:** Percentage of shots that became goals (Goals / Total Shots × 100)
            
            **Shot Accuracy:** Percentage of shots on target (On Target / Total Shots × 100)
            
            **Big Chances:** High quality chances with xG > 0.3 (30%+ probability of scoring)
            
            **Box Shots:** Shots taken inside the penalty area (last 18 yards)
            
            **Outside Box Shots:** Shots taken from outside the penalty area
            
            **xG Overperformance:** Actual goals - Expected goals. Positive = lucky/clinical, negative = unlucky/wasteful
            """)
        
        # xG comparison chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_xg = plot_xg_comparison(home_attacking, away_attacking, home_team, away_team)
            st.pyplot(fig_xg)
        
        with col2:
            st.markdown("### 📈 Key Insights")
            
            xg_diff = home_attacking['xG'] - away_attacking['xG']
            if xg_diff > 0.5:
                st.success(f"✅ {home_team} dominated in xG (+{xg_diff:.2f})")
            elif xg_diff < -0.5:
                st.success(f"✅ {away_team} dominated in xG (+{abs(xg_diff):.2f})")
            else:
                st.info(f"⚖️ Evenly matched in xG (diff: {abs(xg_diff):.2f})")
            
            # Overperformance
            if home_attacking['xG Overperformance'] > 0.5:
                st.success(f"🍀 {home_team} outperformed xG by {home_attacking['xG Overperformance']:.2f}")
            elif away_attacking['xG Overperformance'] > 0.5:
                st.success(f"🍀 {away_team} outperformed xG by {away_attacking['xG Overperformance']:.2f}")
        
        st.markdown("---")
        
        # Detailed stats table
        st.markdown("### 📊 Detailed Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🏠 {home_team}")
            home_df = pd.DataFrame([home_attacking]).T
            home_df.columns = ['Value']
            home_df.index.name = 'Metric'
            st.dataframe(home_df, use_container_width=True)
        
        with col2:
            st.markdown(f"#### ✈️ {away_team}")
            away_df = pd.DataFrame([away_attacking]).T
            away_df.columns = ['Value']
            away_df.index.name = 'Metric'
            st.dataframe(away_df, use_container_width=True)
    
    # TAB 2: PASSING
    with tab2:
        st.markdown("## 🔗 Passing Metrics")
        
        # Info box
        with st.expander("ℹ️ Metric Explanations", expanded=False):
            st.markdown("""
            **Total Passes:** All pass attempts by the team
            
            **Completed Passes:** Passes that successfully reached a teammate
            
            **Pass Accuracy:** Percentage of successful passes (Completed / Total × 100)
            
            **Progressive Passes:** Forward passes that move the ball at least 10 meters closer to opponent's goal
            
            **Final Third Passes:** Passes made in the attacking third of the pitch (last 40 meters)
            
            **Penalty Area Passes:** Passes into the opponent's penalty box
            
            **Long Passes (30m+):** Passes covering at least 30 meters distance
            
            **Long Pass Accuracy:** Success rate of long passes only
            
            **Avg Pass Length:** Average distance covered by each pass in meters
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 🏠 {home_team}")
            home_pass_df = pd.DataFrame([home_passing]).T
            home_pass_df.columns = ['Value']
            st.dataframe(home_pass_df, use_container_width=True)
        
        with col2:
            st.markdown(f"### ✈️ {away_team}")
            away_pass_df = pd.DataFrame([away_passing]).T
            away_pass_df.columns = ['Value']
            st.dataframe(away_pass_df, use_container_width=True)
    
    # TAB 3: DEFENSIVE
    with tab3:
        st.markdown("## 🛡️ Defensive Metrics")
        
        # Info box
        with st.expander("ℹ️ Metric Explanations", expanded=False):
            st.markdown("""
            **Tackles:** Attempts to win the ball from an opponent in a duel
            
            **Interceptions:** Passes cut out by reading the game (no physical contact)
            
            **Blocks:** Blocking an opponent's shot or pass with the body
            
            **Clearances:** Kicking the ball away from danger zone (usually defensive third)
            
            **Pressures:** Applying pressure on opponent in possession to force error/turnover
            
            **Total Defensive Actions:** Sum of Tackles + Interceptions + Blocks
            
            **PPDA (Passes Per Defensive Action):** Opponent passes allowed before a defensive action. Lower = more aggressive pressing. Formula: Opponent passes / Defensive actions
            
            **Recoveries:** Regaining possession of a loose ball
            
            💡 **PPDA Benchmark:** <8 = Very high press, 8-10 = High press, 10-12 = Medium press, >12 = Low press
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 🏠 {home_team}")
            home_def_df = pd.DataFrame([home_defensive]).T
            home_def_df.columns = ['Value']
            st.dataframe(home_def_df, use_container_width=True)
            
            if home_defensive['PPDA'] < 10:
                st.success(f"✅ High pressing intensity (PPDA: {home_defensive['PPDA']:.2f})")
        
        with col2:
            st.markdown(f"### ✈️ {away_team}")
            away_def_df = pd.DataFrame([away_defensive]).T
            away_def_df.columns = ['Value']
            st.dataframe(away_def_df, use_container_width=True)
            
            if away_defensive['PPDA'] < 10:
                st.success(f"✅ High pressing intensity (PPDA: {away_defensive['PPDA']:.2f})")
    
    # TAB 4: COMPARISON
    with tab4:
        st.markdown("## ⚖️ Team Comparison")
        
        # Info box
        with st.expander("ℹ️ How to Read This", expanded=False):
            st.markdown("""
            **Radar Chart:** Visual comparison of 5 key performance areas. Larger area = better performance in that category.
            - All metrics normalized to 0-100 scale for fair comparison
            - Areas where shapes don't overlap show clear advantage
            
            **Side-by-Side Table:** Direct numerical comparison
            - Positive difference (+) = Home team advantage
            - Negative difference (-) = Away team advantage
            
            💡 **Tip:** Look for patterns - does one team dominate in multiple areas or is it balanced?
            """)
        
        # Radar chart
        metrics_dict = {
            'attacking': home_attacking,
            'passing': home_passing,
            'defensive': home_defensive
        }
        
        away_metrics_dict = {
            'attacking': away_attacking,
            'passing': away_passing,
            'defensive': away_defensive
        }
        
        fig_radar = plot_radar_chart(metrics_dict, away_metrics_dict, home_team, away_team)
        st.pyplot(fig_radar)
        
        st.markdown("---")
        
        # Side-by-side comparison
        st.markdown("### 📋 Side-by-Side Comparison")
        
        comparison_data = {
            'Metric': [],
            home_team: [],
            away_team: [],
            'Difference': []
        }
        
        # Attacking
        comparison_data['Metric'].append('xG')
        comparison_data[home_team].append(f"{home_attacking['xG']:.2f}")
        comparison_data[away_team].append(f"{away_attacking['xG']:.2f}")
        comparison_data['Difference'].append(f"{home_attacking['xG'] - away_attacking['xG']:+.2f}")
        
        comparison_data['Metric'].append('Shots')
        comparison_data[home_team].append(home_attacking['Total Shots'])
        comparison_data[away_team].append(away_attacking['Total Shots'])
        comparison_data['Difference'].append(f"{home_attacking['Total Shots'] - away_attacking['Total Shots']:+d}")
        
        # Passing
        comparison_data['Metric'].append('Pass Accuracy %')
        comparison_data[home_team].append(f"{home_passing['Pass Accuracy (%)']:.1f}%")
        comparison_data[away_team].append(f"{away_passing['Pass Accuracy (%)']:.1f}%")
        comparison_data['Difference'].append(f"{home_passing['Pass Accuracy (%)'] - away_passing['Pass Accuracy (%)']:+.1f}%")
        
        # Defensive
        comparison_data['Metric'].append('PPDA')
        comparison_data[home_team].append(f"{home_defensive['PPDA']:.2f}")
        comparison_data[away_team].append(f"{away_defensive['PPDA']:.2f}")
        comparison_data['Difference'].append(f"{home_defensive['PPDA'] - away_defensive['PPDA']:+.2f}")
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # TAB 5: PLAYERS
    with tab5:
        st.markdown("## 👥 Player Performance")
        st.info("🚧 Player-level metrics coming soon! Stay tuned.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 Data Source: <a href='https://github.com/statsbomb/open-data' target='_blank'>StatsBomb Open Data</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()