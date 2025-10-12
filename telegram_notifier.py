"""
Telegram Notifier for HomePi Security System
Sends notifications, photos, and videos via Telegram bot
"""

import json
import os
import asyncio
import threading
from datetime import datetime

# Telegram bot modules
telegram_available = False
try:
    from telegram import Bot
    from telegram.error import TelegramError
    telegram_available = True
except ImportError as e:
    print(f"⚠ Telegram modules not available: {e}")

# Global bot state
bot = None
telegram_config = {}
telegram_enabled = False
event_loop = None
loop_thread = None


def load_config():
    """Load Telegram configuration from config.json"""
    global telegram_config
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            telegram_config = config.get('security', {}).get('notifications', {})
            return telegram_config
    except Exception as e:
        print(f"Error loading Telegram config: {e}")
        return {
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'send_photo': True,
            'send_video': False
        }


def start_event_loop():
    """Start asyncio event loop in background thread"""
    global event_loop
    
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def init_telegram(bot_token=None, chat_id=None):
    """
    Initialize Telegram bot
    
    Args:
        bot_token: Telegram bot token from BotFather
        chat_id: Chat ID to send messages to
    """
    global bot, telegram_enabled, telegram_config, loop_thread, event_loop
    
    if not telegram_available:
        print("Telegram modules not available")
        return False
    
    telegram_config = load_config()
    
    if not bot_token:
        bot_token = telegram_config.get('telegram_bot_token', '')
    if not chat_id:
        chat_id = telegram_config.get('telegram_chat_id', '')
    
    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID not configured")
        print("Please set telegram_bot_token and telegram_chat_id in config.json")
        return False
    
    try:
        # Start event loop in background
        if not loop_thread or not loop_thread.is_alive():
            loop_thread = threading.Thread(target=start_event_loop, daemon=True, name="TelegramLoop")
            loop_thread.start()
        
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Store chat ID in config
        telegram_config['telegram_chat_id'] = chat_id
        telegram_config['telegram_bot_token'] = bot_token
        
        telegram_enabled = True
        print("✓ Telegram bot initialized")
        
        # Test connection
        try:
            future = asyncio.run_coroutine_threadsafe(
                bot.get_me(),
                event_loop
            )
            bot_info = future.result(timeout=5)
            print(f"  Bot: @{bot_info.username}")
            return True
        except Exception as e:
            print(f"Warning: Could not verify bot: {e}")
            return True  # Still return True as bot is initialized
        
    except Exception as e:
        print(f"Error initializing Telegram bot: {e}")
        telegram_enabled = False
        return False


async def _send_message_async(message, chat_id=None):
    """Async function to send message"""
    if not chat_id:
        chat_id = telegram_config.get('telegram_chat_id')
    
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')


def send_notification(message, chat_id=None):
    """
    Send text notification
    
    Args:
        message: Text message to send
        chat_id: Optional chat ID (uses config if not provided)
    """
    global bot, telegram_enabled, event_loop
    
    if not telegram_enabled or not bot:
        print(f"Telegram not enabled. Would send: {message}")
        return False
    
    try:
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"🏠 <b>HomePi Security</b>\n⏰ {timestamp}\n\n{message}"
        
        # Send via event loop
        future = asyncio.run_coroutine_threadsafe(
            _send_message_async(formatted_message, chat_id),
            event_loop
        )
        future.result(timeout=10)
        
        print(f"✓ Telegram notification sent")
        return True
        
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


async def _send_photo_async(photo_path, caption=None, chat_id=None):
    """Async function to send photo"""
    if not chat_id:
        chat_id = telegram_config.get('telegram_chat_id')
    
    with open(photo_path, 'rb') as photo_file:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_file,
            caption=caption,
            parse_mode='HTML'
        )


def send_photo(photo_path, caption=None, chat_id=None):
    """
    Send photo with optional caption
    
    Args:
        photo_path: Path to image file
        caption: Optional caption text
        chat_id: Optional chat ID
    """
    global bot, telegram_enabled, telegram_config, event_loop
    
    if not telegram_enabled or not bot:
        print(f"Telegram not enabled. Would send photo: {photo_path}")
        return False
    
    if not telegram_config.get('send_photo', True):
        print("Photo sending disabled in config")
        return False
    
    if not os.path.exists(photo_path):
        print(f"Photo not found: {photo_path}")
        return False
    
    try:
        # Add timestamp to caption
        timestamp = datetime.now().strftime("%H:%M:%S")
        if caption:
            full_caption = f"🏠 <b>HomePi Security</b>\n⏰ {timestamp}\n\n{caption}"
        else:
            full_caption = f"🏠 HomePi Security\n⏰ {timestamp}"
        
        # Send via event loop
        future = asyncio.run_coroutine_threadsafe(
            _send_photo_async(photo_path, full_caption, chat_id),
            event_loop
        )
        future.result(timeout=15)
        
        print(f"✓ Telegram photo sent: {photo_path}")
        return True
        
    except Exception as e:
        print(f"Error sending Telegram photo: {e}")
        return False


async def _send_video_async(video_path, caption=None, chat_id=None):
    """Async function to send video"""
    if not chat_id:
        chat_id = telegram_config.get('telegram_chat_id')
    
    with open(video_path, 'rb') as video_file:
        await bot.send_video(
            chat_id=chat_id,
            video=video_file,
            caption=caption,
            parse_mode='HTML',
            supports_streaming=True
        )


def send_video(video_path, caption=None, chat_id=None):
    """
    Send video with optional caption
    
    Args:
        video_path: Path to video file
        caption: Optional caption text
        chat_id: Optional chat ID
    """
    global bot, telegram_enabled, telegram_config, event_loop
    
    if not telegram_enabled or not bot:
        print(f"Telegram not enabled. Would send video: {video_path}")
        return False
    
    if not telegram_config.get('send_video', False):
        print("Video sending disabled in config")
        return False
    
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return False
    
    try:
        # Add timestamp to caption
        timestamp = datetime.now().strftime("%H:%M:%S")
        if caption:
            full_caption = f"🏠 <b>HomePi Security</b>\n⏰ {timestamp}\n\n{caption}"
        else:
            full_caption = f"🏠 HomePi Security\n⏰ {timestamp}"
        
        # Send via event loop
        future = asyncio.run_coroutine_threadsafe(
            _send_video_async(video_path, full_caption, chat_id),
            event_loop
        )
        future.result(timeout=30)
        
        print(f"✓ Telegram video sent: {video_path}")
        return True
        
    except Exception as e:
        print(f"Error sending Telegram video: {e}")
        return False


def is_enabled():
    """Check if Telegram is enabled"""
    return telegram_enabled


def get_status():
    """Get Telegram status"""
    return {
        'enabled': telegram_enabled,
        'bot_configured': bool(telegram_config.get('telegram_bot_token')),
        'chat_configured': bool(telegram_config.get('telegram_chat_id')),
        'send_photo': telegram_config.get('send_photo', True),
        'send_video': telegram_config.get('send_video', False)
    }


def cleanup():
    """Cleanup Telegram resources"""
    global event_loop
    
    if event_loop and event_loop.is_running():
        event_loop.call_soon_threadsafe(event_loop.stop)
    
    print("Telegram notifier cleanup complete")


if __name__ == "__main__":
    # Test Telegram functionality
    print("Testing Telegram notifier...")
    print("\nTo test Telegram:")
    print("1. Create bot with @BotFather on Telegram")
    print("2. Get your chat ID (use @userinfobot)")
    print("3. Add credentials to config.json")
    
    bot_token = input("\nEnter bot token (or press Enter to skip): ").strip()
    chat_id = input("Enter chat ID (or press Enter to skip): ").strip()
    
    if bot_token and chat_id:
        if init_telegram(bot_token, chat_id):
            print("\nTelegram initialized successfully")
            print(f"Status: {get_status()}")
            
            # Test message
            print("\nSending test message...")
            send_notification("🎉 Test notification from HomePi Security!")
            
            # Test photo (if exists)
            test_photo = "test_image.jpg"
            if os.path.exists(test_photo):
                print("\nSending test photo...")
                send_photo(test_photo, "📸 Test photo from HomePi")
            
            cleanup()
        else:
            print("\nTelegram initialization failed")
    else:
        print("\nTest skipped - credentials not provided")

