
import requests
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime, timedelta

GOLD_MARKET_CODE = "088691"

def fetch_cot_data(years=3):
    all_data = []
    current_year = datetime.now().year
    
    for year in range(current_year - years, current_year + 1):
        try:
            url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                import zipfile, io
                z = zipfile.ZipFile(io.BytesIO(response.content))
                csv_name = z.namelist()[0]
                df = pd.read_csv(z.open(csv_name), low_memory=False)
                gold_df = df[df["CFTC_Market_Code"].astype(str).str.strip() == GOLD_MARKET_CODE]
                all_data.append(gold_df)
                print(f"✅ שנה {year}: {len(gold_df)} שורות")
        except Exception as e:
            print(f"⚠️ שגיאה בשנה {year}: {e}")
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    combined["Report_Date"] = pd.to_datetime(combined["As_of_Date_In_Form_YYMMDD"], format="%y%m%d")
    combined = combined.sort_values("Report_Date")
    return combined

def analyze_cot(df):
    df = df.copy()
    
    # עמודות מרכזיות
    df["net_large"] = df["M_Money_Positions_Long_All"] - df["M_Money_Positions_Short_All"]
    df["net_commercial"] = df["Comm_Positions_Long_All"] - df["Comm_Positions_Short_All"]
    df["total_oi"] = df["Open_Interest_All"]
    
    # נרמול לאחוזונים
    df["large_pct"] = df["net_large"].rank(pct=True) * 100
    df["commercial_pct"] = df["net_commercial"].rank(pct=True) * 100
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # ניתוח עונתיות
    df["month"] = df["Report_Date"].dt.month
    monthly = df.groupby("month")["net_large"].mean()
    current_month = datetime.now().month
    seasonal_bias = monthly[current_month]
    avg_seasonal = monthly.mean()
    
    # זיהוי דפוסים דומים היסטוריים
    current_large_pct = latest["large_pct"]
    similar = df[
        (df["large_pct"] >= current_large_pct - 10) &
        (df["large_pct"] <= current_large_pct + 10) &
        (df["Report_Date"] < latest["Report_Date"])
    ].tail(5)
    
    # ניתוח קיצוניות
    if latest["large_pct"] >= 80:
        extreme = "EXTREME LONG — סיכון גבוה לתיקון"
        extreme_emoji = "🔴"
    elif latest["large_pct"] <= 20:
        extreme = "EXTREME SHORT — הזדמנות קנייה פוטנציאלית"
        extreme_emoji = "🟢"
    elif latest["large_pct"] >= 60:
        extreme = "לונג מעל הממוצע"
        extreme_emoji = "🟡"
    else:
        extreme = "ניטרלי"
        extreme_emoji = "⚪"

    # שינוי שבועי
    weekly_change = latest["net_large"] - prev["net_large"]
    change_dir = "הגדילו" if weekly_change > 0 else "הקטינו"
    
    report_date = latest["Report_Date"].strftime("%d/%m/%Y")
    
    summary = f"""
📋 ניתוח COT היסטורי — זהב (36 חודשים)
דוח אחרון: {report_date}

👥 מוסדיים (Smart Money):
פוזיציה נטו: {int(latest['net_large']):,} חוזים
אחוזון היסטורי: {latest['large_pct']:.0f}% {extreme_emoji} {extreme}
שינוי שבועי: {change_dir} ב-{abs(int(weekly_change)):,} חוזים

🏭 מסחריים (Hedgers):
פוזיציה נטו: {int(latest['net_commercial']):,} חוזים
אחוזון היסטורי: {latest['commercial_pct']:.0f}%

📅 עונתיות — חודש {current_month}:
{'חיובית מעל הממוצע' if seasonal_bias > avg_seasonal else 'שלילית מתחת לממוצע'} היסטורית

🔍 מצבים דומים בעבר: {len(similar)} מקרים נמצאו
"""
    return summary.strip()

if __name__ == "__main__":
    print("שואב נתוני COT...")
    df = fetch_cot_data(years=3)
    if df is not None:
        result = analyze_cot(df)
        print(result)
    else:
        print("לא ניתן לשאוב נתונים")
