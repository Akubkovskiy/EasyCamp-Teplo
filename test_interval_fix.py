
import asyncio
import sqlite3
from datetime import datetime, timedelta, date
from app.services.avito_api_service import avito_api_service
import requests

def get_db_bookings(house_id):
    conn = sqlite3.connect('easycamp.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get bookings intersecting with next 180 days
    today = date.today().isoformat()
    # Fix: Uppercase status check
    cursor.execute(
        "SELECT check_in, check_out FROM bookings WHERE house_id = ? AND status IN ('NEW', 'CONFIRMED', 'PAID') AND check_out >= ?",
        (house_id, today)
    )
    bookings = cursor.fetchall()
    conn.close()
    
    return [
        {'start': datetime.strptime(b['check_in'], '%Y-%m-%d').date(), 
         'end': datetime.strptime(b['check_out'], '%Y-%m-%d').date()} 
        for b in bookings
    ]

async def fix_intervals():
    house_id = 2
    item_id = 3792037514
    
    print(f"Fixing intervals for House {house_id} (Item {item_id})...")
    
    # 1. Get local bookings
    bookings = await asyncio.to_thread(get_db_bookings, house_id)
    bookings.sort(key=lambda x: x['start'])
    print(f"Found {len(bookings)} local bookings.")
    for b in bookings:
        print(f"- {b['start']} to {b['end']}")
        
    # 2. Calculate free intervals
    today = datetime.now().date()
    end_date = today + timedelta(days=180)
    
    free_intervals = []
    current_date = today
    
    for booking in bookings:
        # If gap between current and booking start
        if current_date < booking['start']:
            free_intervals.append({
                'date_start': current_date.isoformat(),
                'date_end': booking['start'].isoformat(),
                'open': 1
            })
        
        # Advance current to booking end
        if booking['end'] > current_date:
            current_date = booking['end']
            
    # Final interval
    if current_date < end_date:
        free_intervals.append({
            'date_start': current_date.isoformat(),
            'date_end': end_date.isoformat(),
            'open': 1
        })
        
    print(f"Calculated {len(free_intervals)} free intervals.")
    
    # 3. Push to Avito
    token = avito_api_service.get_access_token()
    url = f"https://api.avito.ru/realty/v1/items/intervals"
    payload = {
        "intervals": free_intervals,
        "item_id": item_id,
        "source": "EasyCamp"
    }
    
    print("Pushing intervals...")
    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_intervals())
