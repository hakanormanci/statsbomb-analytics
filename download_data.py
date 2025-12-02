"""
StatsBomb Veri İndirme Script (Minimal)
Sadece 1. Bundesliga 2023/2024 ve seçili maç için veri indirir

Kullanım:
python download_data.py
"""

import requests
import json
import os
import time

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/refs/heads/master/data/"

# ÖNEMLİ: Hangi veriyi indireceğini buradan ayarla
COMPETITION_ID = 9      # 1. Bundesliga
SEASON_ID = 281         # 2023/2024
MATCH_ID = 3895292      # Union Berlin maçı (değiştirilebilir)

def download_file(url, save_path, max_retries=5):
    """Dosya indir ve kaydet (retry logic ile)"""
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Klasör yoksa oluştur
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Kaydet
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)
            
            print(f"✅ Downloaded: {save_path}")
            return response.json()
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed after {max_retries} attempts: {save_path}")
                print(f"   Error: {e}")
                return None
    
    return None

def main():
    print("🚀 StatsBomb Minimal Veri İndirme\n")
    print(f"📊 Competition: {COMPETITION_ID}")
    print(f"📅 Season: {SEASON_ID}")
    print(f"⚽ Match: {MATCH_ID}\n")
    
    # 1. Competitions indir (genel bilgi için)
    print("📥 Step 1/4: Downloading competitions list...")
    download_file(
        f"{BASE_URL}competitions.json",
        "data/competitions.json"
    )
    
    # 2. Sadece bu lig/sezon için matches indir
    print(f"\n📥 Step 2/4: Downloading matches for Bundesliga 2023/2024...")
    matches_data = download_file(
        f"{BASE_URL}matches/{COMPETITION_ID}/{SEASON_ID}.json",
        f"data/matches/{COMPETITION_ID}/{SEASON_ID}.json"
    )
    
    if not matches_data:
        print("❌ Failed to download matches. Exiting.")
        return
    
    print(f"✅ Found {len(matches_data)} matches in this season")
    
    # 3. Sadece seçili maç için events indir
    print(f"\n📥 Step 3/4: Downloading events for match {MATCH_ID}...")
    download_file(
        f"{BASE_URL}events/{MATCH_ID}.json",
        f"data/events/{MATCH_ID}.json"
    )
    
    # 4. Sadece seçili maç için lineups indir
    print(f"\n📥 Step 4/4: Downloading lineups for match {MATCH_ID}...")
    download_file(
        f"{BASE_URL}lineups/{MATCH_ID}.json",
        f"data/lineups/{MATCH_ID}.json"
    )
    
    print("\n" + "="*60)
    print("✅ İndirme Tamamlandı!")
    print("="*60)
    print(f"\n📁 İndirilen dosyalar:")
    print(f"  ├── data/competitions.json")
    print(f"  ├── data/matches/{COMPETITION_ID}/{SEASON_ID}.json  ({len(matches_data)} matches)")
    print(f"  ├── data/events/{MATCH_ID}.json")
    print(f"  └── data/lineups/{MATCH_ID}.json")
    
    print(f"\n💡 İpucu: Başka bir maç indirmek için:")
    print(f"   1. Bu scriptin başındaki MATCH_ID değerini değiştir")
    print(f"   2. Script'i tekrar çalıştır")
    print(f"\n📊 Şu anda indirilen maç:")
    
    # Maç bilgisini göster
    for match in matches_data:
        if match['match_id'] == MATCH_ID:
            home = match['home_team']['home_team_name']
            away = match['away_team']['away_team_name']
            score = f"{match['home_score']} - {match['away_score']}"
            date = match['match_date']
            print(f"   {home} vs {away} ({score}) - {date}")
            break
    
    print("\n🎯 Artık uygulamayı çalıştırabilirsin:")
    print("   streamlit run app.py")

if __name__ == "__main__":
    main()