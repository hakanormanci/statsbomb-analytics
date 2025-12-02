"""
StatsBomb Detailed Pass Analysis Page
Detaylı paslaşma analizi - Ayrı sayfa

Kullanım:
streamlit run pass_analysis.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
from matplotlib.patches import Rectangle, Arc, FancyArrowPatch
import os
import json

# Doğru BASE URL
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/refs/heads/master/data/"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Pass Analysis - StatsBomb",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
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
    """Maç bilgilerini yükle (ev sahibi/deplasman bilgisi için)"""
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

def draw_pitch(ax, pitch_color='#1e3a1e', line_color='white'):
    """Futbol sahası çiz"""
    pitch_length = 120
    pitch_width = 80
    
    ax.add_patch(Rectangle((0, 0), pitch_length, pitch_width, 
                           facecolor=pitch_color, edgecolor=line_color, linewidth=2))
    
    ax.plot([0, 0], [0, pitch_width], color=line_color, linewidth=2)
    ax.plot([0, pitch_length], [pitch_width, pitch_width], color=line_color, linewidth=2)
    ax.plot([pitch_length, pitch_length], [pitch_width, 0], color=line_color, linewidth=2)
    ax.plot([pitch_length, 0], [0, 0], color=line_color, linewidth=2)
    
    ax.plot([pitch_length/2, pitch_length/2], [0, pitch_width], color=line_color, linewidth=2)
    
    center_circle = plt.Circle((pitch_length/2, pitch_width/2), 9.15, 
                               color=line_color, fill=False, linewidth=2)
    ax.add_patch(center_circle)
    
    ax.add_patch(Rectangle((0, 18), 18, 44, fill=False, edgecolor=line_color, linewidth=2))
    ax.add_patch(Rectangle((0, 30), 6, 20, fill=False, edgecolor=line_color, linewidth=2))
    
    ax.add_patch(Rectangle((102, 18), 18, 44, fill=False, edgecolor=line_color, linewidth=2))
    ax.add_patch(Rectangle((114, 30), 6, 20, fill=False, edgecolor=line_color, linewidth=2))
    
    ax.plot(12, 40, 'o', color=line_color, markersize=4)
    ax.plot(108, 40, 'o', color=line_color, markersize=4)
    
    ax.set_xlim(-2, pitch_length + 2)
    ax.set_ylim(-2, pitch_width + 2)
    ax.axis('off')
    ax.set_aspect('equal')

def plot_pass_diagram(events_df, selected_team, passer, receiver, is_home_team):
    """Belirli bir ikili için pas diyagramı çiz"""
    events_df_copy = events_df.copy()
    events_df_copy['team_name'] = events_df_copy['team'].apply(
        lambda x: x['name'] if isinstance(x, dict) else x
    )
    
    passes = events_df_copy[
        (events_df_copy['type'].apply(lambda x: x['name'] == 'Pass')) &
        (events_df_copy['team_name'] == selected_team)
    ].copy()
    
    player_passes = []
    for _, row in passes.iterrows():
        passer_info = row.get('player')
        if isinstance(passer_info, dict):
            current_passer = passer_info.get('name')
        else:
            current_passer = passer_info
        
        pass_dict = row.get('pass')
        if isinstance(pass_dict, dict):
            recipient_info = pass_dict.get('recipient')
            if isinstance(recipient_info, dict):
                current_receiver = recipient_info.get('name')
            else:
                current_receiver = recipient_info
            
            if current_passer == passer and current_receiver == receiver:
                start_loc = row.get('location')
                end_loc = pass_dict.get('end_location')
                successful = pass_dict.get('outcome') is None
                period = row.get('period', 1)
                
                if start_loc and end_loc:
                    if period == 1:
                        if is_home_team:
                            start_x, start_y = start_loc[0], start_loc[1]
                            end_x, end_y = end_loc[0], end_loc[1]
                        else:
                            start_x, start_y = 120 - start_loc[0], 80 - start_loc[1]
                            end_x, end_y = 120 - end_loc[0], 80 - end_loc[1]
                    else:
                        if is_home_team:
                            start_x, start_y = 120 - start_loc[0], 80 - start_loc[1]
                            end_x, end_y = 120 - end_loc[0], 80 - end_loc[1]
                        else:
                            start_x, start_y = start_loc[0], start_loc[1]
                            end_x, end_y = end_loc[0], end_loc[1]
                    
                    player_passes.append({
                        'start': (start_x, start_y),
                        'end': (end_x, end_y),
                        'successful': successful,
                        'period': period
                    })
    
    if len(player_passes) == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(14, 10))
    draw_pitch(ax)
    
    # Atak yönü göstergesi
    # Koordinatları normalize ettik (her zaman soldan sağa göster)
    # Ama deplasman takımı için text'i ters yaz
    arrow_y = 75
    
    ax.annotate('', xy=(110, arrow_y), xytext=(10, arrow_y),
               arrowprops=dict(arrowstyle='->', lw=4, color='yellow', alpha=0.7))
    
    if is_home_team:
        ax.text(60, arrow_y + 3, f'{selected_team} ATTACKING DIRECTION →', 
               ha='center', fontsize=14, color='yellow', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    else:
        # Deplasman takımı - bilgi ver ama ok yönü aynı (koordinatlar normalize edildi)
        ax.text(60, arrow_y + 3, f'{selected_team} ATTACKING DIRECTION → (normalized)', 
               ha='center', fontsize=12, color='yellow', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    for i, pass_info in enumerate(player_passes):
        start = pass_info['start']
        end = pass_info['end']
        successful = pass_info['successful']
        period = pass_info['period']
        
        color = 'lime' if successful else 'red'
        alpha = 0.6
        
        arrow = FancyArrowPatch(
            (start[0], start[1]), (end[0], end[1]),
            arrowstyle='->', mutation_scale=20,
            color=color, alpha=alpha, linewidth=2
        )
        ax.add_patch(arrow)
        
        if period == 1:
            ax.plot(start[0], start[1], 'o', color=color, markersize=8, alpha=0.8)
        else:
            ax.plot(start[0], start[1], 's', color=color, markersize=8, alpha=0.8)
    
    period_1_count = sum(1 for p in player_passes if p['period'] == 1)
    period_2_count = sum(1 for p in player_passes if p['period'] == 2)
    
    ax.set_title(f'{passer.split()[-1]} → {receiver.split()[-1]} ({len(player_passes)} passes: {period_1_count} in 1st half, {period_2_count} in 2nd half)', 
                fontsize=16, color='white', pad=20, fontweight='bold')
    
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='lime', linewidth=2, label='Successful'),
        Line2D([0], [0], color='red', linewidth=2, label='Unsuccessful'),
        Line2D([0], [0], color='yellow', linewidth=4, label='Attack Direction'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=8, label='1st Half', linestyle='None'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=8, label='2nd Half', linestyle='None')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12)
    
    fig.patch.set_facecolor('#0e1117')
    return fig

def analyze_passes(events_df, selected_team, is_home_team):
    """Pasları analiz et"""
    events_df_copy = events_df.copy()
    events_df_copy['team_name'] = events_df_copy['team'].apply(
        lambda x: x['name'] if isinstance(x, dict) else x
    )
    
    passes = events_df_copy[
        (events_df_copy['type'].apply(lambda x: x['name'] == 'Pass')) &
        (events_df_copy['team_name'] == selected_team)
    ].copy()
    
    pass_details = []
    for _, row in passes.iterrows():
        passer_info = row.get('player')
        if isinstance(passer_info, dict):
            passer = passer_info.get('name')
        else:
            passer = passer_info
        
        period = row.get('period', 1)
        
        pass_dict = row.get('pass')
        recipient = None
        pass_length = None
        
        if isinstance(pass_dict, dict):
            recipient_info = pass_dict.get('recipient')
            if isinstance(recipient_info, dict):
                recipient = recipient_info.get('name')
            elif isinstance(recipient_info, str):
                recipient = recipient_info
            
            pass_length = pass_dict.get('length')
        
        successful = pass_dict.get('outcome') is None if isinstance(pass_dict, dict) else False
        
        start_loc = row.get('location')
        end_loc = pass_dict.get('end_location') if isinstance(pass_dict, dict) else None
        
        pass_direction = None
        if start_loc and end_loc:
            x_diff = end_loc[0] - start_loc[0]
            
            if period == 1:
                if is_home_team:
                    if x_diff > 5:
                        pass_direction = "→ Forward"
                    elif x_diff < -5:
                        pass_direction = "← Backward"
                    else:
                        pass_direction = "↔ Lateral"
                else:
                    if x_diff < -5:
                        pass_direction = "← Forward"
                    elif x_diff > 5:
                        pass_direction = "→ Backward"
                    else:
                        pass_direction = "↔ Lateral"
            else:
                if is_home_team:
                    if x_diff < -5:
                        pass_direction = "← Forward"
                    elif x_diff > 5:
                        pass_direction = "→ Backward"
                    else:
                        pass_direction = "↔ Lateral"
                else:
                    if x_diff > 5:
                        pass_direction = "→ Forward"
                    elif x_diff < -5:
                        pass_direction = "← Backward"
                    else:
                        pass_direction = "↔ Lateral"
        
        if passer and recipient:
            pass_details.append({
                'from': passer,
                'to': recipient,
                'successful': successful,
                'length': pass_length,
                'direction': pass_direction,
                'period': period
            })
    
    return pd.DataFrame(pass_details)

def main():
    st.markdown("# 🔗 Detailed Pass Analysis")
    
    st.sidebar.header("⚙️ Settings")
    match_id = st.sidebar.number_input("Match ID", value=3895292, step=1)
    
    if st.sidebar.button("🔄 Load Match Data"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner('📥 Loading match data...'):
        match_info = load_match_info(match_id)
        events = load_events(match_id)
    
    if events is None:
        st.error("❌ Failed to load match data!")
        return
    
    events['team_name'] = events['team'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
    teams = events['team_name'].unique().tolist()
    
    if len(teams) < 2:
        st.error("❌ Could not find team data!")
        return
    
    home_team = None
    away_team = None
    
    if match_info is not None:
        if isinstance(match_info['home_team'], dict):
            home_team = match_info['home_team'].get('home_team_name')
        else:
            home_team = match_info['home_team']
            
        if isinstance(match_info['away_team'], dict):
            away_team = match_info['away_team'].get('away_team_name')
        else:
            away_team = match_info['away_team']
        
        st.sidebar.markdown("### 🔍 Match Info")
        st.sidebar.write(f"Home: {home_team}")
        st.sidebar.write(f"Away: {away_team}")
    else:
        st.sidebar.warning("⚠️ Could not determine home/away teams.")
        home_team = teams[0] if len(teams) > 0 else None
        away_team = teams[1] if len(teams) > 1 else None
    
    st.sidebar.markdown("---")
    selected_team = st.sidebar.selectbox("Select Team", teams)
    
    is_home_team = (selected_team == home_team)
    
    if home_team and away_team:
        st.sidebar.info(f"🏠 Home: {home_team}\n✈️ Away: {away_team}")
        if is_home_team:
            st.sidebar.success(f"Selected: {selected_team} (Home)")
        else:
            st.sidebar.warning(f"Selected: {selected_team} (Away)")
    
    with st.spinner('🔄 Analyzing passes...'):
        pass_df = analyze_passes(events, selected_team, is_home_team)
    
    if len(pass_df) == 0:
        st.warning("No pass data available for this team")
        return
    
    grouped = pass_df.groupby(['from', 'to']).agg({
        'successful': ['sum', 'count'],
        'length': 'mean'
    }).reset_index()
    
    grouped.columns = ['From', 'To', 'Successful', 'Total', 'Avg Length (m)']
    grouped['Success Rate (%)'] = (grouped['Successful'] / grouped['Total'] * 100).round(1)
    
    sort_by = st.sidebar.selectbox(
        "Sort by",
        ['Total', 'Successful', 'Success Rate (%)', 'Avg Length (m)']
    )
    
    grouped_sorted = grouped.sort_values(sort_by, ascending=False)
    
    min_passes_filter = st.sidebar.slider("Minimum passes to show", 1, 20, 5)
    grouped_filtered = grouped_sorted[grouped_sorted['Total'] >= min_passes_filter]
    
    st.markdown("## 📊 Overall Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pass Attempts", len(pass_df))
    
    with col2:
        successful_passes = len(pass_df[pass_df['successful']])
        st.metric("Successful Passes", successful_passes)
    
    with col3:
        success_rate = (successful_passes / len(pass_df) * 100) if len(pass_df) > 0 else 0
        st.metric("Overall Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        avg_length = pass_df['length'].mean()
        st.metric("Avg Pass Length", f"{avg_length:.1f}m" if pd.notna(avg_length) else "N/A")
    
    st.markdown("---")
    
    st.markdown("## 👥 Player-to-Player Connections")
    st.info(f"💡 Showing connections with at least {min_passes_filter} passes.")
    
    display_df = grouped_filtered.copy()
    display_df['Avg Length (m)'] = display_df['Avg Length (m)'].apply(
        lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
    )
    
    if len(grouped_filtered) > 0:
        connection_options = [
            f"{row['From']} → {row['To']} ({int(row['Total'])} passes)"
            for _, row in grouped_filtered.iterrows()
        ]
        
        selected_connection_str = st.selectbox(
            "Select a connection to visualize (5+ passes only)",
            ["None"] + connection_options,
            help="Choose a player-to-player connection"
        )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        if selected_connection_str != "None":
            selected_idx = connection_options.index(selected_connection_str)
            selected_connection = grouped_filtered.iloc[selected_idx]
            
            passer = selected_connection['From']
            receiver = selected_connection['To']
            total_passes = selected_connection['Total']
            
            if total_passes >= 5:
                st.markdown("---")
                st.markdown(f"## 🎯 Pass Diagram: {passer} → {receiver}")
                
                with st.spinner('Drawing passes...'):
                    fig = plot_pass_diagram(events, selected_team, passer, receiver, is_home_team)
                    
                    if fig:
                        st.pyplot(fig)
                    else:
                        st.warning("Could not generate pass diagram")
            else:
                st.info(f"💡 This connection has only {total_passes} passes. Select 5+.")
    else:
        st.warning("No connections found with the selected filters")
    
    st.markdown("---")
    
    csv = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download Pass Analysis as CSV",
        data=csv,
        file_name=f"pass_analysis_{selected_team.replace(' ', '_')}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 Data Source: <a href='https://github.com/statsbomb/open-data' target='_blank'>StatsBomb Open Data</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()