# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from asyncio.exceptions import TimeoutError
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from database.db import db

SESSION_STRING_SIZE = 351

# Regex format to detect Telegram bot start links
BOT_LINK_REGEX = r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/([a-zA-Z0-9_]+bot)\?start=([a-zA-Z0-9_-]+)"

# --- LOGOUT COMMAND ---
@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_data = await db.get_session(message.from_user.id)  
    if user_data is None:
        await message.reply("**Aap pehle se hi logged out hain!**")
        return 
    await db.set_session(message.from_user.id, session=None)  
    await message.reply("**Logout Successfully** ♦")

# --- LOGIN COMMAND ---
@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is not None:
        await message.reply("**Your Are Already Logged In. First /logout Your Old Session. Then Do Login.**")
        return 
    user_id = int(message.from_user.id)
    await message.reply("**How To Create Api Id And Api Hash.\n\nVideo Link :- https://youtu.be/LDtgwpI-N7M**")
    api_id_msg = await bot.ask(user_id, "<b>Send Your API ID.\n\nClick On /skip To Skip This Process\n\nNOTE :- If You Skip This Then Your Account Ban Chance Is High.</b>", filters=filters.text)
    
    if api_id_msg.text == "/skip":
        api_id = API_ID
        api_hash = API_HASH
    else:
        try:
            api_id = int(api_id_msg.text)
        except ValueError:
            await api_id_msg.reply("**Api id must be an integer, start your process again by /login**", quote=True)
            return
        api_hash_msg = await bot.ask(user_id, "**Now Send Me Your API HASH**", filters=filters.text)
        api_hash = api_hash_msg.text
        
    phone_number_msg = await bot.ask(chat_id=user_id, text="<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>")
    if phone_number_msg.text == '/cancel':
        return await phone_number_msg.reply('<b>process cancelled !</b>')
    phone_number = phone_number_msg.text
    
    client = Client(":memory:", api_id, api_hash)
    await client.connect()
    await phone_number_msg.reply("Sending OTP...")
    
    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "Please check for an OTP in official telegram account. If you got it, send OTP here after reading the below format. \n\nIf OTP is `12345`, **please send it as** `1 2 3 4 5`.\n\n**Enter /cancel to cancel The Procces**", filters=filters.text, timeout=600)
    except PhoneNumberInvalid:
        await phone_number_msg.reply('`PHONE_NUMBER` **is invalid.**')
        return
        
    if phone_code_msg.text == '/cancel':
        return await phone_code_msg.reply('<b>process cancelled !</b>')
        
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await phone_code_msg.reply('**OTP is invalid.**')
        return
    except PhoneCodeExpired:
        await phone_code_msg.reply('**OTP is expired.**')
        return
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, '**Your account has enabled two-step verification. Please provide the password.\n\nEnter /cancel to cancel The Procces**', filters=filters.text, timeout=300)
        if two_step_msg.text == '/cancel':
            return await two_step_msg.reply('<b>process cancelled !</b>')
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply('**Invalid Password Provided**')
            return
            
    string_session = await client.export_session_string()
    await client.disconnect()
    
    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply('<b>invalid session sring</b>')
        
    try:
        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            uclient = Client(":memory:", session_string=string_session, api_id=api_id, api_hash=api_hash)
            await uclient.connect()
            await db.set_session(message.from_user.id, session=string_session)
            await db.set_api_id(message.from_user.id, api_id=api_id)
            await db.set_api_hash(message.from_user.id, api_hash=api_hash)
            try:
                await uclient.disconnect()
            except:
                pass
    except Exception as e:
        return await message.reply_text(f"<b>ERROR IN LOGIN:</b> `{e}`")
        
    await bot.send_message(message.from_user.id, "<b>Account Login Successfully.\n\nIf You Get Any Error Related To AUTH KEY Then /logout first and /login again</b>")


# --- BOT LINK DATA FETCH & BYPASS FEATURE ---
@Client.on_message(filters.private & filters.text & ~filters.forwarded)
async def handle_bot_start_links(bot: Client, message: Message):
    text = message.text
    match = re.search(BOT_LINK_REGEX, text, re.IGNORECASE)
    
    # Agar message text bot link nahi hai, toh baki commands/messages ke liye return kar dein
    if not match:
        return 
        
    user_id = message.from_user.id
    bot_username = match.group(1)
    start_param = match.group(2)
    
    # 1. Verification: User logged in hai ya nahi
    session_string = await db.get_session(user_id)
    if not session_string:
        await message.reply_text(
            "❌ **Aap Logged In Nahi Hain!**\n\n"
            "Restricted bot links se data nikalne ke liye pehle `/login` karein."
        )
        return
        
    status_msg = await message.reply_text("⏳ **Bot Link Detected! Aapka account connect kiya ja raha hai...**")
    
    # 2. Database se user ke api credentials nikalna
    try:
        api_id = await db.get_api_id(user_id)
        api_hash = await db.get_api_hash(user_id)
    except Exception:
        api_id = None
        api_hash = None
        
    if not api_id or not api_hash:
        api_id = API_ID
        api_hash = API_HASH

    # 3. Temp client setup user session ke saath
    uclient = Client(":memory:", session_string=session_string, api_id=int(api_id), api_hash=str(api_hash))
    
    try:
        await uclient.connect()
        await status_msg.edit(f"🤖 **Target Bot (@{bot_username}) ko command bheji ja rahi hai...**")
        
        # Target bot ko start param bhejenge user profile se
        await uclient.send_message(bot_username, f"/start {start_param}")
        
        # Response generate hone ke liye pause (5 seconds)
        await asyncio.sleep(5)
        
        await status_msg.edit("📥 **Data fetch kiya ja raha hai...**")
        
        messages = []
        async for msg in uclient.get_chat_history(bot_username, limit=10):
            # Agar hum apni purani sent command tak pahunch gaye, to uske baad wale messages skip karein
            if msg.text and msg.text.startswith(f"/start {start_param}"):
                break
            messages.append(msg)
            
        if not messages:
            await status_msg.edit("❌ **Target bot ne koi response nahi diya ya link expire ho chuka hai.**")
            return
            
        # Sahi sequential line order ke liye messages list ko reverse karenge
        messages.reverse()
        
        for msg in messages:
            # Agar text data hai
            if msg.text:
                await bot.send_message(chat_id=user_id, text=msg.text)
                
            # Agar content media/restricted file hai (Bypass Engine)
            elif msg.media:
                await status_msg.edit("⚡ **Restricted lock bypass ho raha hai... Downloading...**")
                
                # File download pipeline
                file_path = await uclient.download_media(msg)
                
                if file_path:
                    await status_msg.edit("📤 **File fresh link ke saath aapko send ki ja rahi hai...**")
                    
                    # Main bot se user ko re-upload karke bhejna (taaki content download/forward lock toot sake)
                    await bot.send_document(
                        chat_id=user_id,
                        document=file_path,
                        caption=msg.caption or "**Bypassed Successfully By VJ Bots**"
                    )
                    # Temp files ko disk se remove karna
                    os.remove(file_path)
                else:
                    await bot.send_message(chat_id=user_id, text="❌ File processing failed.")
                    
        await status_msg.delete()
        
    except Exception as e:
        traceback.print_exc()
        await status_msg.edit(f"❌ **Error Occurred:** `{str(e)}`")
        
    finally:
        # Dynamic connection disconnect karna taaki resources use na ho
        try:
            await uclient.disconnect()
        except:
            pass

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
