"""
Project Overview & Technical Summary
Özet teknik bilgiler ve proje açıklaması

Dosya yolu: pages/4_📋_Project_Info.py
"""

import streamlit as st

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Project Info",
    page_icon="📋",
    layout="wide"
)

# CSS
st.markdown("""
    <style>
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 2rem 0;
        text-align: center;
    }
    .info-card {
        background-color: #f0f4f8;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: #2d3748;
    }
    .info-card h3 {
        color: #1a365d;
        margin-top: 0;
    }
    .info-card p {
        color: #2d3748;
    }
    .info-card ul {
        color: #2d3748;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown("# 📋 Project Information")
    
    # Hero section
    st.markdown("""
        <div class='highlight-box'>
            <h1>⚽ Football Analytics Dashboard</h1>
            <p style='font-size: 1.2rem; margin-top: 1rem;'>
                Interactive web application for analyzing football match data with advanced statistics and visualizations
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Pages", "5")
    with col2:
        st.metric("💻 Language", "Python")
    with col3:
        st.metric("📦 Libraries", "6+")
    with col4:
        st.metric("🎯 Data Source", "StatsBomb")
    
    st.markdown("---")
    
    # Main content in 2 columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🎯 What Does It Do?")
        st.markdown("""
        This dashboard helps analyze football matches by:
        
        - 📋 **Browse Matches** - View match lists with scores and details
        - 📊 **Match Analysis** - See shots, passes, and team statistics
        - 🔗 **Pass Networks** - Visualize player-to-player connections
        - 📈 **Advanced Metrics** - xG, PPDA, progressive passes, etc.
        
        **Target Users:** Football analysts, coaches, data enthusiasts
        """)
        
        st.markdown("---")
        
        st.markdown("## 🛠️ Technologies Used")
        st.markdown("""
        **Core Stack:**
        - **Python 3.12** - Programming language
        - **Streamlit** - Web framework
        - **Pandas** - Data manipulation
        - **Matplotlib** - Visualizations
        
        **Data Source:**
        - **StatsBomb Open Data** - Free football match data via REST API
        """)
    
    with col2:
        st.markdown("## ✨ Key Features")
        st.markdown("""
        **1. Interactive Visualizations**
        - Shot maps on football pitch
        - Passing network diagrams
        - Comparison charts
        
        **2. Advanced Analytics**
        - Expected Goals (xG)
        - Pressing intensity (PPDA)
        - Progressive passes
        - Pass success rates
        
        **3. User-Friendly Interface**
        - Multi-page navigation
        - Filters and selections
        - CSV data export
        - Responsive design
        """)
        
        st.markdown("---")
        
        st.markdown("## 💡 Notable Implementations")
        st.markdown("""
        **Smart Coordinate Handling:**
        Teams switch sides at halftime - the app automatically normalizes 
        pitch coordinates so all analyses show consistent direction.
        
        **Data Quality:**
        Only analyzes passes with complete information (player-to-player) 
        to ensure accurate statistics across all pages.
        
        **Performance:**
        Uses caching to avoid repeated API calls and speed up the app.
        """)
    
    st.markdown("---")
    
    # Production note
    st.markdown("## 🚀 About This Project")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='info-card'>
            <h3>📌 Current Version (Prototype)</h3>
            <p>This is a <strong>demonstration/portfolio project</strong> designed to showcase:</p>
            <ul>
                <li>Data processing skills</li>
                <li>Visualization design</li>
                <li>Web development</li>
                <li>Clean code practices</li>
            </ul>
            <p><strong>Suitable for:</strong> Portfolio, demos, learning</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='info-card'>
            <h3>🏢 Production Version Would Need</h3>
            <p>For real-world deployment with many users:</p>
            <ul>
                <li><strong>Database:</strong> Store data persistently</li>
                <li><strong>API Layer:</strong> Separate backend service</li>
                <li><strong>Automated Updates:</strong> Scheduled data refresh</li>
                <li><strong>Cloud Hosting:</strong> Scalable infrastructure</li>
            </ul>
            <p><strong>Estimated effort:</strong> 8-12 weeks additional development</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Skills demonstrated
    st.markdown("## 🎓 Skills Demonstrated")
    
    skills_col1, skills_col2, skills_col3 = st.columns(3)
    
    with skills_col1:
        st.markdown("""
        **Data Processing**
        - REST API integration
        - JSON parsing
        - Data transformation
        - Feature engineering
        """)
    
    with skills_col2:
        st.markdown("""
        **Programming**
        - Python development
        - Pandas operations
        - Function design
        - Error handling
        """)
    
    with skills_col3:
        st.markdown("""
        **Visualization**
        - Interactive dashboards
        - Chart design
        - UI/UX considerations
        - Responsive layouts
        """)
    
    st.markdown("---")
    
    # Code example
    st.markdown("## 💻 Code Example")
    
    st.markdown("**Example: Calculating xG (Expected Goals) for a team**")
    
    st.code("""
def calculate_xg(events_df, team_name):
    # Get all shots by the team
    shots = events_df[
        (events_df['team_name'] == team_name) &
        (events_df['type'] == 'Shot')
    ]
    
    # Sum up xG values from all shots
    total_xg = shots['shot'].apply(
        lambda x: x.get('statsbomb_xg', 0)
    ).sum()
    
    # Count actual goals
    goals = shots[shots['outcome'] == 'Goal']
    
    return {
        'xG': total_xg,
        'Goals': len(goals),
        'Overperformance': len(goals) - total_xg
    }
    """, language="python")
    
    st.markdown("---")
    
    # How it works
    st.markdown("## 🔄 How It Works (Simple Flow)")
    
    st.markdown("""
    ```
    1. User selects a match
       ↓
    2. App fetches data from GitHub API (StatsBomb)
       ↓
    3. Data is processed and transformed (pandas)
       ↓
    4. Metrics are calculated (xG, passes, etc.)
       ↓
    5. Visualizations are created (matplotlib)
       ↓
    6. Results displayed on web page (Streamlit)
    ```
    """)
    
    st.markdown("---")
    
    # Project stats
    st.markdown("## 📊 Project Statistics")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Lines of Code", "~2,000+")
    
    with stat_col2:
        st.metric("Functions", "30+")
    
    with stat_col3:
        st.metric("Data Points", "1000+ per match")
    
    with stat_col4:
        st.metric("Metrics Calculated", "25+")
    
    st.markdown("---")
    
    # Contact/Links section
    st.markdown("## 🔗 Links & Resources")
    
    link_col1, link_col2 = st.columns(2)
    
    with link_col1:
        st.markdown("""
        **Data Source:**
        - [StatsBomb Open Data](https://github.com/statsbomb/open-data)
        - Free football match data
        - JSON format via REST API
        """)
    
    with link_col2:
        st.markdown("""
        **Technologies:**
        - [Python](https://python.org)
        - [Streamlit](https://streamlit.io)
        - [Pandas](https://pandas.pydata.org)
        - [Matplotlib](https://matplotlib.org)
        """)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; margin-top: 2rem;'>
            <h3>📧 Portfolio Project</h3>
            <p>This project demonstrates skills in:</p>
            <p><strong>Data Processing • Web Development • Analytics • Visualization</strong></p>
            <p style='margin-top: 1rem; font-size: 0.9rem;'>
                Built with Python, Streamlit, Pandas, and Matplotlib
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()