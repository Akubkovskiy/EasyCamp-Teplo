import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.telegram.menus.guest import guest_menu_keyboard
from app.telegram.menus.admin import admin_menu_keyboard

async def main():
    print("Verifying Guest Menu Components...")
    
    # 1. Check Guest Keyboard creation
    try:
        kb = guest_menu_keyboard()
        buttons = kb.inline_keyboard
        print(f"Guest Keyboard created with {len(buttons)} rows")
        
        # Check first button
        btn = buttons[0][0]
        if btn.callback_data == "guest:availability":
             print(f"'Check Dates' button present: {btn.text} -> {btn.callback_data}")
        else:
             print(f"Error: Unexpected first button: {btn.callback_data}")
             
    except Exception as e:
        print(f"Error creating guest keyboard: {e}")

    # 2. Verify admin menu is still valid
    try:
        kb_admin = admin_menu_keyboard()
        print(f"Admin Keyboard created with {len(kb_admin.inline_keyboard)} rows")
    except Exception as e:
        print(f"Error creating admin keyboard: {e}")
        
    print("\nFunctional logic (start_handler, callbacks) requires manual testing in Telegram.")
    print("Please verify manually:")
    print("1. As Admin: /start -> Admin Panel")
    print("2. As Guest (simulated): /start -> Guest Menu")

if __name__ == "__main__":
    asyncio.run(main())
