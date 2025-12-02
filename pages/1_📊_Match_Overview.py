"""
StatsBomb Match Detail Page
Detaylı maç analizi sayfası

Kullanım:
streamlit run match_detail.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
from matplotlib.patches import Rectangle, Arc
import seaborn as sns

# Doğru BASE URL
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/refs/heads/master/data/"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Match Detail - StatsBomb",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .match-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    p[title] {
        cursor: help;
        border-bottom: 1px dotted #999;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

def fetch_with_retry(url, max_retries=3, timeout=10):
    """Retry mekanizması ile veri çekme"""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
            else:
                st.error(f"❌ Failed to load data: {str(e)}")
                return None
    return None

@st.cache_data(ttl=3600)
def load_match_info(match_id):
    """Maç bilgilerini yükle"""
    # Tüm maçları tara ve bu match_id'yi bul
    competitions_url = f"{BASE_URL}competitions.json"
    competitions_data = fetch_with_retry(competitions_url)
    
    if not competitions_data:
        return None
    
    competitions = pd.DataFrame(competitions_data)
    
    # Her competition/season kombinasyonunu kontrol et
    for _, comp in competitions.iterrows():
        matches_url = f"{BASE_URL}matches/{comp['competition_id']}/{comp['season_id']}.json"
        matches_data = fetch_with_retry(matches_url)
        
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
    data = fetch_with_retry(url, max_retries=5, timeout=15)
    
    if data:
        return pd.DataFrame(data)
    return None

@st.cache_data(ttl=3600)
def load_lineups(match_id):
    """Kadroları yükle"""
    url = f"{BASE_URL}lineups/{match_id}.json"
    data = fetch_with_retry(url)
    return data if data else []

def draw_pitch(ax, pitch_color='#1e3a1e', line_color='white'):
    """Futbol sahası çiz"""
    pitch_length = 120
    pitch_width = 80
    
    # Saha zemini
    ax.add_patch(Rectangle((0, 0), pitch_length, pitch_width, 
                           facecolor=pitch_color, edgecolor=line_color, linewidth=2))
    
    # Kenar çizgileri
    ax.plot([0, 0], [0, pitch_width], color=line_color, linewidth=2)
    ax.plot([0, pitch_length], [pitch_width, pitch_width], color=line_color, linewidth=2)
    ax.plot([pitch_length, pitch_length], [pitch_width, 0], color=line_color, linewidth=2)
    ax.plot([pitch_length, 0], [0, 0], color=line_color, linewidth=2)
    
    # Orta çizgi
    ax.plot([pitch_length/2, pitch_length/2], [0, pitch_width], color=line_color, linewidth=2)
    
    # Orta daire
    center_circle = plt.Circle((pitch_length/2, pitch_width/2), 9.15, 
                               color=line_color, fill=False, linewidth=2)
    ax.add_patch(center_circle)
    
    # Sol ceza sahası
    ax.add_patch(Rectangle((0, 18), 18, 44, fill=False, edgecolor=line_color, linewidth=2))
    ax.add_patch(Rectangle((0, 30), 6, 20, fill=False, edgecolor=line_color, linewidth=2))
    
    # Sağ ceza sahası
    ax.add_patch(Rectangle((102, 18), 18, 44, fill=False, edgecolor=line_color, linewidth=2))
    ax.add_patch(Rectangle((114, 30), 6, 20, fill=False, edgecolor=line_color, linewidth=2))
    
    # Penaltı noktaları
    ax.plot(12, 40, 'o', color=line_color, markersize=4)
    ax.plot(108, 40, 'o', color=line_color, markersize=4)
    
    ax.set_xlim(-2, pitch_length + 2)
    ax.set_ylim(-2, pitch_width + 2)
    ax.axis('off')
    ax.set_aspect('equal')

def plot_shot_map(events_df, team_name):
    """Şut haritası"""
    # Team bilgisini string'e çevir
    events_df_copy = events_df.copy()
    events_df_copy['team_name'] = events_df_copy['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    
    shots = events_df_copy[
        (events_df_copy['type'].apply(lambda x: x['name'] == 'Shot')) &
        (events_df_copy['team_name'] == team_name)
    ].copy()
    
    if len(shots) == 0:
        return None
    
    # Şut detayları
    shots['outcome'] = shots['shot'].apply(
        lambda x: x.get('outcome', {}).get('name', 'Unknown') if isinstance(x, dict) else 'Unknown'
    )
    shots['xg'] = shots['shot'].apply(
        lambda x: x.get('statsbomb_xg', 0) if isinstance(x, dict) else 0
    )
    shots['x'] = shots['location'].apply(lambda x: x[0] if x else None)
    shots['y'] = shots['location'].apply(lambda x: x[1] if x else None)
    
    # Grafik
    fig, ax = plt.subplots(figsize=(12, 8))
    draw_pitch(ax)
    
    # Goller
    goals = shots[shots['outcome'] == 'Goal']
    # Gol olmayanlar
    non_goals = shots[shots['outcome'] != 'Goal']
    
    # Şutları çiz (xG'ye göre boyut)
    if len(non_goals) > 0:
        scatter1 = ax.scatter(non_goals['x'], non_goals['y'], 
                             s=non_goals['xg']*1000, c='red', alpha=0.6, 
                             edgecolors='white', linewidths=2, label='No Goal')
    
    if len(goals) > 0:
        scatter2 = ax.scatter(goals['x'], goals['y'], 
                             s=goals['xg']*1000 + 200, c='lime', alpha=0.9, 
                             edgecolors='white', linewidths=3, marker='*', label='Goal')
    
    ax.set_title(f'{team_name} - Shot Map', fontsize=16, color='white', pad=20)
    ax.legend(loc='upper left', fontsize=12)
    
    fig.patch.set_facecolor('#0e1117')
    return fig

def plot_pass_network(events_df, team_name, min_passes=2, debug=False):
    """Paslaşma ağı"""
    # Team bilgisini string'e çevir
    events_df_copy = events_df.copy()
    events_df_copy['team_name'] = events_df_copy['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    
    passes = events_df_copy[
        (events_df_copy['type'].apply(lambda x: x['name'] == 'Pass')) &
        (events_df_copy['team_name'] == team_name)
    ].copy()
    
    # Debug bilgisi
    if debug:
        st.markdown(f"""
            <p title="How many times {team_name} attempted a pass">
                📊 Debug - Total passes for {team_name}: <strong>{len(passes)}</strong>
            </p>
        """, unsafe_allow_html=True)
    
    # Başarılı paslar
    passes['successful'] = passes['pass'].apply(
        lambda x: x.get('outcome') is None if isinstance(x, dict) else False
    )
    successful_passes = passes[passes['successful']]
    
    if debug:
        st.markdown(f"""
            <p title="Passes that reached a teammate">
                ✅ Successful passes: <strong>{len(successful_passes)}</strong>
            </p>
        """, unsafe_allow_html=True)
    
    if len(successful_passes) == 0:
        return None
    
    # Paslaşma çiftleri
    pass_pairs = []
    for _, row in successful_passes.iterrows():
        # Player bilgisi dictionary olabilir
        passer_info = row.get('player')
        if isinstance(passer_info, dict):
            passer = passer_info.get('name')
        elif isinstance(passer_info, str):
            passer = passer_info
        else:
            passer = None
        
        # Pass dictionary'den recipient'i çıkar
        pass_dict = row.get('pass')
        recipient = None
        
        if isinstance(pass_dict, dict):
            recipient_info = pass_dict.get('recipient')
            if isinstance(recipient_info, dict):
                recipient = recipient_info.get('name')
            elif isinstance(recipient_info, str):
                recipient = recipient_info
        
        # İkisi de string ise ekle
        if passer and recipient and isinstance(passer, str) and isinstance(recipient, str):
            pass_pairs.append((passer, recipient))
    
    if debug:
        st.markdown(f"""
            <p title="All player-to-player passes found (e.g. Player A → Player B)">
                🔗 Pass pairs found: <strong>{len(pass_pairs)}</strong>
            </p>
        """, unsafe_allow_html=True)
    
    if len(pass_pairs) == 0:
        if debug:
            st.write("⚠️ No valid pass pairs found")
        return None
    
    pass_counts = pd.DataFrame(pass_pairs, columns=['from', 'to'])
    pass_counts = pass_counts.groupby(['from', 'to']).size().reset_index(name='count')
    
    if debug:
        st.markdown(f"""
            <p title="Grouped by player pairs (e.g. if A passed to B 5 times, this counts as 1 unique connection)">
                📊 Unique connections: <strong>{len(pass_counts)}</strong>
            </p>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <p title="Only showing connections with at least {min_passes} passes between the same two players">
                🎯 After filtering (min {min_passes} passes): <strong>{len(pass_counts[pass_counts['count'] >= min_passes])}</strong>
            </p>
        """, unsafe_allow_html=True)
    
    pass_counts = pass_counts[pass_counts['count'] >= min_passes]
    
    if len(pass_counts) == 0:
        return None
    
    # Oyuncu pozisyonları
    player_positions = {}
    for _, row in successful_passes.iterrows():
        # Player bilgisi dictionary olabilir
        player_info = row.get('player')
        if isinstance(player_info, dict):
            player = player_info.get('name')
        elif isinstance(player_info, str):
            player = player_info
        else:
            continue
        
        location = row.get('location')
        if location and player:
            if player not in player_positions:
                player_positions[player] = []
            player_positions[player].append(location)
    
    # Ortalama pozisyon hesapla
    avg_positions = {}
    for player, locations in player_positions.items():
        if len(locations) > 0:
            avg_x = np.mean([loc[0] for loc in locations])
            avg_y = np.mean([loc[1] for loc in locations])
            avg_positions[player] = (avg_x, avg_y)
    
    if debug:
        st.markdown(f"""
            <p title="Players shown on the network diagram">
                👥 Players with positions: <strong>{len(avg_positions)}</strong>
            </p>
        """, unsafe_allow_html=True)
    
    # Grafik
    fig, ax = plt.subplots(figsize=(14, 10))
    draw_pitch(ax)
    
    # Pasları çiz
    for _, row in pass_counts.iterrows():
        if row['from'] in avg_positions and row['to'] in avg_positions:
            x1, y1 = avg_positions[row['from']]
            x2, y2 = avg_positions[row['to']]
            
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->', color='cyan', 
                                     lw=row['count']/5, alpha=0.5))
    
    # Oyuncuları çiz
    for player, (x, y) in avg_positions.items():
        total_passes = pass_counts[
            (pass_counts['from'] == player) | (pass_counts['to'] == player)
        ]['count'].sum()
        
        ax.scatter(x, y, c='yellow', s=total_passes*10, 
                  alpha=0.8, edgecolors='white', linewidths=2, zorder=3)
        ax.text(x, y-3, player.split()[-1], ha='center', 
               fontsize=9, color='white', fontweight='bold', zorder=4)
    
    ax.set_title(f'{team_name} - Passing Network', fontsize=16, color='white', pad=20)
    fig.patch.set_facecolor('#0e1117')
    return fig

def calculate_team_stats(events_df, team_name):
    """Takım istatistikleri hesapla"""
    # Team bilgisini string'e çevir
    events_df_copy = events_df.copy()
    events_df_copy['team_name'] = events_df_copy['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    
    team_events = events_df_copy[events_df_copy['team_name'] == team_name]
    
    # Şutlar
    shots = team_events[team_events['type'].apply(lambda x: x['name'] == 'Shot')]
    goals = shots[shots['shot'].apply(
        lambda x: x.get('outcome', {}).get('name') == 'Goal' if isinstance(x, dict) else False
    )]
    xg = shots['shot'].apply(
        lambda x: x.get('statsbomb_xg', 0) if isinstance(x, dict) else 0
    ).sum()
    
    # Paslar
    passes = team_events[team_events['type'].apply(lambda x: x['name'] == 'Pass')]
    successful_passes = passes[passes['pass'].apply(
        lambda x: x.get('outcome') is None if isinstance(x, dict) else False
    )]
    pass_accuracy = (len(successful_passes) / len(passes) * 100) if len(passes) > 0 else 0
    
    # Top hakimiyeti (olaylar bazında yaklaşık)
    total_events = len(events_df_copy)
    team_event_count = len(team_events)
    possession = (team_event_count / total_events * 100) if total_events > 0 else 0
    
    # Defansif aksiyonlar
    tackles = len(team_events[team_events['type'].apply(lambda x: x.get('name') == 'Duel')])
    interceptions = len(team_events[team_events['type'].apply(lambda x: x.get('name') == 'Interception')])
    
    return {
        'shots': len(shots),
        'goals': len(goals),
        'xg': xg,
        'passes': len(passes),
        'pass_accuracy': pass_accuracy,
        'possession': possession,
        'tackles': tackles,
        'interceptions': interceptions
    }

def main():
    st.markdown("# ⚽ Match Detail Analysis")
    
    # Match ID
    MATCH_ID = 3895292
    
    st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;'>
            <p><strong>Match ID:</strong> {MATCH_ID}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Veri yükle
    with st.spinner('📥 Loading match data...'):
        match_info = load_match_info(MATCH_ID)
        events = load_events(MATCH_ID)
        lineups = load_lineups(MATCH_ID)
    
    if match_info is None or events is None:
        st.error("❌ Failed to load match data!")
        return
    
    # Maç başlığı
    st.markdown(f"""
        <div class='match-header'>
            <h1>{match_info['home_team']['home_team_name']} vs {match_info['away_team']['away_team_name']}</h1>
            <h2 style='margin-top: 1rem;'>{match_info['home_score']} - {match_info['away_score']}</h2>
            <p style='margin-top: 1rem; font-size: 1.1rem;'>
                📅 {match_info['match_date']} | 🏟️ {match_info['stadium']['name'] if isinstance(match_info['stadium'], dict) else 'Unknown'}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Takım isimleri
    home_team = match_info['home_team']['home_team_name']
    away_team = match_info['away_team']['away_team_name']
    
    # İstatistikler
    st.markdown("## 📊 Match Statistics")
    
    home_stats = calculate_team_stats(events, home_team)
    away_stats = calculate_team_stats(events, away_team)
    
    # Karşılaştırmalı istatistikler
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### {home_team}")
    with col2:
        st.markdown("### ")
    with col3:
        st.markdown(f"### {away_team}")
    
    # Stats grid
    stats_to_show = [
        ('Goals', 'goals'),
        ('xG', 'xg'),
        ('Shots', 'shots'),
        ('Passes', 'passes'),
        ('Pass Accuracy %', 'pass_accuracy'),
        ('Possession %', 'possession'),
        ('Tackles', 'tackles'),
        ('Interceptions', 'interceptions')
    ]
    
    for stat_name, stat_key in stats_to_show:
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            value = home_stats[stat_key]
            if stat_key in ['xg', 'pass_accuracy', 'possession']:
                st.metric(stat_name, f"{value:.1f}")
            else:
                st.metric(stat_name, int(value))
        
        with col2:
            st.markdown(f"<div style='text-align: center; padding-top: 1rem;'><strong>{stat_name}</strong></div>", 
                       unsafe_allow_html=True)
        
        with col3:
            value = away_stats[stat_key]
            if stat_key in ['xg', 'pass_accuracy', 'possession']:
                st.metric(stat_name, f"{value:.1f}")
            else:
                st.metric(stat_name, int(value))
    
    st.markdown("---")
    
    # Şut haritaları
    st.markdown("## 🎯 Shot Maps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {home_team}")
        fig_home = plot_shot_map(events, home_team)
        if fig_home:
            st.pyplot(fig_home)
        else:
            st.info("No shot data available")
    
    with col2:
        st.markdown(f"### {away_team}")
        fig_away = plot_shot_map(events, away_team)
        if fig_away:
            st.pyplot(fig_away)
        else:
            st.info("No shot data available")
    
    st.markdown("---")
    
    # Paslaşma ağları
    st.markdown("## 🔗 Passing Networks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {home_team}")
        fig_pass_home = plot_pass_network(events, home_team, min_passes=2, debug=True)
        if fig_pass_home:
            st.pyplot(fig_pass_home)
        else:
            st.info("Not enough passing data (minimum 2 passes between players required)")
    
    with col2:
        st.markdown(f"### {away_team}")
        fig_pass_away = plot_pass_network(events, away_team, min_passes=2, debug=True)
        if fig_pass_away:
            st.pyplot(fig_pass_away)
        else:
            st.info("Not enough passing data (minimum 2 passes between players required)")
    
    st.markdown("---")
    
    st.markdown("---")
    
    # Kadro bilgisi
    if lineups and len(lineups) > 0:
        st.markdown("## 👥 Lineups")
        
        col1, col2 = st.columns(2)
        
        for i, team_lineup in enumerate(lineups):
            with col1 if i == 0 else col2:
                st.markdown(f"### {team_lineup['team_name']}")
                
                players_df = pd.DataFrame(team_lineup['lineup'])
                players_df = players_df[['player_name', 'jersey_number']].sort_values('jersey_number')
                players_df.columns = ['Player', 'Number']
                
                st.dataframe(players_df, hide_index=True, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 Data Source: <a href='https://github.com/statsbomb/open-data' target='_blank'>StatsBomb Open Data</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()