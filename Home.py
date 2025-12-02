"""
StatsBomb Match List - Ana Sayfa
Ana uygulama dosyası

Kullanım:
streamlit run app.py
"""

import streamlit as st
import pandas as pd
import requests
import time
import os
import json

# Doğru BASE URL
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/refs/heads/master/data/"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Match List",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        padding-bottom: 2rem;
    }
    .stDataFrame {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
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
def load_competition_info(competition_id, season_id):
    """Turnuva ve sezon bilgilerini getir"""
    url = f"{BASE_URL}competitions.json"
    
    st.info(f"📡 Loading competition info: {url}")
    data = load_from_local(url)
    
    if data is None:
        return None
    
    try:
        competitions = pd.DataFrame(data)
        
        comp_info = competitions[
            (competitions['competition_id'] == competition_id) & 
            (competitions['season_id'] == season_id)
        ]
        
        if len(comp_info) > 0:
            st.success("✅ Competition info loaded!")
            return comp_info.iloc[0]
        else:
            st.warning(f"⚠️ Competition ID: {competition_id}, Season ID: {season_id} not found!")
            st.write("Available Competition IDs and Season IDs:")
            st.dataframe(competitions[['competition_id', 'season_id', 'competition_name', 'season_name']].head(20))
        return None
        
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
        return None

@st.cache_data(ttl=3600)
def load_matches(competition_id, season_id):
    """Maçları yükle ve işle"""
    url = f"{BASE_URL}matches/{competition_id}/{season_id}.json"
    
    st.info(f"📡 Loading matches: {url}")
    data = load_from_local(url)
    
    if data is None:
        return None
    
    try:
        matches = pd.DataFrame(data)
        st.success(f"✅ {len(matches)} matches loaded!")
        
        # Dictionary kolonlarını aç
        matches['home_team_id'] = matches['home_team'].apply(lambda x: x['home_team_id'])
        matches['home_team_name'] = matches['home_team'].apply(lambda x: x['home_team_name'])
        matches['away_team_id'] = matches['away_team'].apply(lambda x: x['away_team_id'])
        matches['away_team_name'] = matches['away_team'].apply(lambda x: x['away_team_name'])
        
        # Stadium bilgisi
        matches['stadium_name'] = matches['stadium'].apply(
            lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else 'Unknown'
        )
        
        # Match week number (rakam olarak)
        matches['match_week'] = matches['match_week'].astype(int)
        
        # Tarih formatı düzelt
        matches['match_date'] = pd.to_datetime(matches['match_date'])
        matches['formatted_date'] = matches['match_date'].dt.strftime('%d.%m.%Y')
        matches['formatted_time'] = matches['kick_off'].apply(
            lambda x: x if pd.notna(x) else '—'
        )
        
        # Sıralama: Önce match_week, sonra tarih (küçükten büyüğe)
        matches = matches.sort_values(['match_week', 'match_date'], ascending=[True, True])
        
        return matches
        
    except Exception as e:
        st.error(f"❌ Error processing data: {e}")
        return None

def display_match_list(matches_df):
    """Maç listesini tablo olarak göster"""
    
    # Gösterilecek kolonları seç
    display_df = matches_df[[
        'formatted_date',
        'match_week',
        'home_team_name',
        'away_team_name',
        'stadium_name',
        'home_score',
        'away_score',
        'match_id'
    ]].copy()
    
    # Kolon isimlerini İngilizce yap
    display_df.columns = [
        '📅 Date',
        '🏆 Week',
        '🏠 Home Team',
        '✈️ Away Team',
        '🏟️ Stadium',
        '⚽ Home Score',
        '⚽ Away Score',
        'Match ID'
    ]
    
    # Skor kolonlarını integer yap
    display_df['⚽ Home Score'] = display_df['⚽ Home Score'].astype(int)
    display_df['⚽ Away Score'] = display_df['⚽ Away Score'].astype(int)
    
    # Skor formatı
    display_df['📊 Score'] = (
        display_df['⚽ Home Score'].astype(str) + ' - ' + 
        display_df['⚽ Away Score'].astype(str)
    )
    
    # Son gösterim için kolonları düzenle
    final_df = display_df[[
        '📅 Date',
        '🏆 Week',
        '🏠 Home Team',
        '✈️ Away Team',
        '🏟️ Stadium',
        '📊 Score',
        'Match ID'
    ]]
    
    # Match ID'yi gizle
    final_df_display = final_df.drop('Match ID', axis=1)
    
    return final_df_display, final_df

def main():
    # Başlık
    st.markdown("# ⚽ StatsBomb Match List")
    
    # Parametreler
    COMPETITION_ID = 9
    SEASON_ID = 281
    
    st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;'>
            <p><strong>Competition ID:</strong> {COMPETITION_ID} | <strong>Season ID:</strong> {SEASON_ID}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Manuel yenileme butonu
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Reload Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Loading göstergesi
    with st.spinner('📥 Loading data...'):
        # Turnuva bilgisi
        comp_info = load_competition_info(COMPETITION_ID, SEASON_ID)
        
        # Maçları yükle
        matches = load_matches(COMPETITION_ID, SEASON_ID)
    
    if matches is None or len(matches) == 0:
        st.error("❌ Failed to load match data!")
        
        st.markdown("### 🔧 Troubleshooting:")
        st.markdown("""
        1. **Check your internet connection**
        2. **Try disabling VPN if you're using one**
        3. **Wait a few minutes and try again**
        4. **Click the "Reload Data" button above**
        5. **Clear browser cache** (Ctrl+Shift+Delete)
        """)
        
        # Alternatif: Manuel URL göster
        st.markdown("### 📋 Manual Check:")
        manual_url = f"{BASE_URL}matches/{COMPETITION_ID}/{SEASON_ID}.json"
        st.code(manual_url)
        st.markdown(f"[🔗 Click to view data in browser]({manual_url})")
        
        return
    
    # Turnuva bilgisi başlık
    if comp_info is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background-color: #e8f4f8; border-radius: 10px; margin-bottom: 2rem;'>
                    <h2 style='color: #1f77b4; margin: 0;'>{comp_info['competition_name']}</h2>
                    <h3 style='color: #666; margin: 0.5rem 0 0 0;'>{comp_info['season_name']}</h3>
                </div>
            """, unsafe_allow_html=True)
    
    # İstatistikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Matches", len(matches))
    
    with col2:
        total_goals = matches['home_score'].sum() + matches['away_score'].sum()
        st.metric("⚽ Total Goals", int(total_goals))
    
    with col3:
        avg_goals = total_goals / len(matches)
        st.metric("📈 Goals per Match", f"{avg_goals:.2f}")
    
    with col4:
        unique_teams = pd.concat([
            matches['home_team_name'], 
            matches['away_team_name']
        ]).nunique()
        st.metric("👥 Teams", unique_teams)
    
    st.markdown("---")
    
    # Filtreler
    st.sidebar.header("🔍 Filters")
    
    # Takım filtresi
    all_teams = sorted(list(set(
        matches['home_team_name'].tolist() + 
        matches['away_team_name'].tolist()
    )))
    
    selected_team = st.sidebar.selectbox(
        "Select Team (Optional)",
        ["All"] + all_teams
    )
    
    # Hafta filtresi
    all_weeks = sorted(matches['match_week'].unique().tolist())
    selected_week = st.sidebar.selectbox(
        "Select Week (Optional)",
        ["All"] + all_weeks
    )
    
    # Filtreleme uygula
    filtered_matches = matches.copy()
    
    if selected_team != "All":
        filtered_matches = filtered_matches[
            (filtered_matches['home_team_name'] == selected_team) |
            (filtered_matches['away_team_name'] == selected_team)
        ]
    
    if selected_week != "All":
        filtered_matches = filtered_matches[
            filtered_matches['match_week'] == selected_week
        ]
    
    # Filtrelenmiş sonuç sayısı
    if len(filtered_matches) < len(matches):
        st.info(f"🔍 Filtered results: {len(filtered_matches)} matches")
    
    # Maç listesini göster
    if len(filtered_matches) > 0:
        display_df, full_df = display_match_list(filtered_matches)
        
        st.markdown("### 📋 Match List")
        
        # Match ID seçimi için
        st.info("💡 **Select a match** from the dropdown below to view details or pass analysis")
        
        match_options = [
            f"{row['🏠 Home Team']} vs {row['✈️ Away Team']} ({row['📅 Date']}) - ID: {row['Match ID']}"
            for _, row in full_df.iterrows()
        ]
        
        selected_match = st.selectbox(
            "Select a match to analyze",
            ["None"] + match_options
        )
        
        if selected_match != "None":
            # Match ID'yi çıkar
            match_id = int(selected_match.split("ID: ")[1])
            
            # Session state'e kaydet
            st.session_state.selected_match_id = match_id
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    <div style='background-color: #e8f4f8; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #667eea;'>
                        <h3 style='margin-top: 0;'>📊 Match Detail</h3>
                        <p>View comprehensive match analysis including:</p>
                        <ul>
                            <li>Shot maps</li>
                            <li>Passing networks</li>
                            <li>Team statistics</li>
                            <li>Player lineups</li>
                        </ul>
                        <p style='margin-bottom: 0;'><strong>→ Go to "Match Detail" page from the sidebar</strong></p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div style='background-color: #fff4e6; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f59e0b;'>
                        <h3 style='margin-top: 0;'>🔗 Pass Analysis</h3>
                        <p>Explore detailed passing statistics:</p>
                        <ul>
                            <li>Player-to-player connections</li>
                            <li>Pass success rates</li>
                            <li>Pass diagrams on pitch</li>
                            <li>Half-by-half analysis</li>
                        </ul>
                        <p style='margin-bottom: 0;'><strong>→ Go to "Pass Analysis" page from the sidebar</strong></p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Tablo gösterimi - interaktif
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        
        # İndirme butonu
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"matches_{COMPETITION_ID}_{SEASON_ID}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No matches found matching the filters.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 Data Source: <a href='https://github.com/statsbomb/open-data' target='_blank'>StatsBomb Open Data</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()