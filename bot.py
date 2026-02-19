import os
import random
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Bot ka token
BOT_TOKEN = "8297167976:AAGaVZqC-HQVX2iPllBEiZbjHbNvJM2khy0"

# Apka public channel ka username
CHANNEL_USERNAME = "@vipxofficial_video"

# Display channel for normal users
DISPLAY_CHANNEL = "@WebBot_Lab"

# Config file
CONFIG_FILE = "vipbot_config.json"

# Default values
DEFAULT_MIN_ID = 3
DEFAULT_MAX_ID = 153

# VIP levels ke buttons - Updated with unique emojis
VIP_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("💎 VIP 1 — Basic Access", callback_data='vip1')],
    [InlineKeyboardButton("✨ VIP 2 — Premium Collection", callback_data='vip2')],
    [InlineKeyboardButton("👑 VIP 3 — Royal Selection", callback_data='vip3')],
    [InlineKeyboardButton("🚀 VIP 4 — Ultra Exclusive", callback_data='vip4')],
    [InlineKeyboardButton("🔥 VIP 5 — Legendary Content", callback_data='vip5')]
])

# Admin panel keyboard - Updated emojis
ADMIN_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Dashboard Stats", callback_data='admin_view')],
    [InlineKeyboardButton("⚡ Change Min ID", callback_data='admin_min')],
    [InlineKeyboardButton("⚡ Change Max ID", callback_data='admin_max')],
    [InlineKeyboardButton("🔍 Auto Scan IDs", callback_data='admin_scan')],
    [InlineKeyboardButton("📈 Analytics Report", callback_data='admin_stats')],
    [InlineKeyboardButton("🚪 Close Panel", callback_data='admin_close')]
])

class ConfigManager:
    """Configuration manager"""
    
    def __init__(self):
        self.min_id = DEFAULT_MIN_ID
        self.max_id = DEFAULT_MAX_ID
        self.working_ids = []
        self.recently_sent = []  # Track recently sent IDs (last 20)
        self.stats = {
            'total_requests': 0,
            'total_videos_sent': 0,
            'unique_videos_sent': 0,
            'last_updated': None
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.min_id = data.get('min_id', DEFAULT_MIN_ID)
                    self.max_id = data.get('max_id', DEFAULT_MAX_ID)
                    self.working_ids = data.get('working_ids', [])
                    self.recently_sent = data.get('recently_sent', [])
                    self.stats = data.get('stats', self.stats)
                print(f"✅ Config loaded: {self.min_id} to {self.max_id}")
                print(f"✅ Working IDs: {len(self.working_ids)}")
                return True
        except Exception as e:
            print(f"❌ Error loading config: {e}")
        return False
    
    def save_config(self):
        """Save configuration to file"""
        try:
            data = {
                'min_id': self.min_id,
                'max_id': self.max_id,
                'working_ids': self.working_ids,
                'recently_sent': self.recently_sent[-50:],  # Keep last 50
                'stats': self.stats,
                'last_saved': asyncio.get_event_loop().time()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
        return False
    
    def update_stats(self, videos_sent=0, unique_videos=0):
        """Update statistics"""
        self.stats['total_requests'] += 1
        self.stats['total_videos_sent'] += videos_sent
        self.stats['unique_videos_sent'] += unique_videos
        self.stats['last_updated'] = asyncio.get_event_loop().time()
        self.save_config()
    
    def get_video_ids_for_user(self, user_id):
        """
        Get video IDs for a user - RANDOM every time!
        1. First try from working IDs (but not recently sent)
        2. If not enough, try random IDs from range
        3. Always random selection
        """
        all_possible_ids = list(range(self.min_id, self.max_id + 1))
        
        # Step 1: Filter out recently sent IDs (avoid repetition)
        available_working = [
            id for id in self.working_ids 
            if id not in self.recently_sent[-10:]  # Last 10 se avoid kare
        ]
        
        selected_ids = []
        
        # Step 2: If we have enough working IDs, use them RANDOMLY
        if available_working:
            # Take random working IDs (not all, random selection)
            num_from_working = min(random.randint(2, 4), len(available_working))
            selected_ids = random.sample(available_working, num_from_working)
        
        # Step 3: Add random new IDs to make total 10
        remaining_needed = 10 - len(selected_ids)
        
        if remaining_needed > 0:
            # Get random IDs from full range (excluding already selected)
            available_new = [
                id for id in all_possible_ids 
                if id not in selected_ids and id not in self.working_ids
            ]
            
            if available_new:
                num_new = min(remaining_needed, len(available_new))
                new_ids = random.sample(available_new, num_new)
                selected_ids.extend(new_ids)
        
        # Shuffle the final list for complete randomness
        random.shuffle(selected_ids)
        
        return selected_ids
    
    def mark_as_sent(self, video_id, success=True):
        """Mark a video as sent (for tracking)"""
        if success:
            # Add to recently sent
            self.recently_sent.append(video_id)
            
            # Keep only last 50
            if len(self.recently_sent) > 50:
                self.recently_sent = self.recently_sent[-50:]
            
            # Add to working IDs if not already there
            if video_id not in self.working_ids:
                self.working_ids.append(video_id)
        
        self.save_config()

# Global config manager
config = ConfigManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler - Updated with unique style and owner name"""
    user = update.effective_user
    
    # Create stylish welcome message with owner name
    welcome_text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>• VIP X OFFICIAL VIDEO BOT •</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"👋 <b>Hello {user.first_name}!</b>\n"
        f"🎉 Welcome to our <b>Exclusive VIP Collection</b>\n\n"
        
        f"📌 <b>Bot Owner:</b> @VIP_X_OFFICIAL\n"
        f"📢 <b>Our Channel:</b> {DISPLAY_CHANNEL}\n\n"
        
        f"💫 <b>Features:</b>\n"
        f"├─ 🎯 Fresh Random Videos Every Time\n"
        f"├─ 🔄 No Repetition Guarantee\n"
        f"├─ ⚡ Instant Delivery\n"
        f"└─ 🏆 Premium Quality Content\n\n"
        
        f"👇 <b>Choose Your VIP Tier:</b>"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=VIP_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

async def send_videos_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send RANDOM videos to user - Fresh every time!"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Loading message with unique style
    await query.edit_message_text(
        text=f"⏳ <b>Curating Your VIP Collection...</b>\n\n"
             f"👤 <i>For:</i> {user_name}\n"
             f"🎲 <i>Selecting Random Videos...</i>",
        parse_mode=ParseMode.HTML
    )
    
    # Get RANDOM video IDs for this user
    all_candidate_ids = config.get_video_ids_for_user(user_id)
    
    # Try to send videos
    sent_count = 0
    attempts = 0
    max_attempts = 15
    
    successful_ids = []
    failed_ids = []
    
    for video_id in all_candidate_ids:
        if sent_count >= 5:
            break
        
        if attempts >= max_attempts:
            break
            
        try:
            attempts += 1
            
            # Forward video
            await context.bot.forward_message(
                chat_id=user_id,
                from_chat_id=CHANNEL_USERNAME,
                message_id=video_id,
                disable_notification=True
            )
            
            sent_count += 1
            successful_ids.append(video_id)
            
            # Mark as sent and working
            config.mark_as_sent(video_id, success=True)
            
            await asyncio.sleep(0.3)
            
        except Exception as e:
            error_msg = str(e).lower()
            failed_ids.append(video_id)
            
            if "message not found" in error_msg or "not enough rights" in error_msg:
                # Remove from working IDs if it doesn't exist
                if video_id in config.working_ids:
                    config.working_ids.remove(video_id)
            continue
    
    # Update statistics
    unique_videos = len(set(successful_ids))
    config.update_stats(videos_sent=sent_count, unique_videos=unique_videos)
    
    # Result message with unique style
    if sent_count > 0:
        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>• VIP DELIVERY SUCCESSFUL •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"🎉 <b>Congratulations {user_name}!</b>\n"
            f"✨ Your VIP Package has been delivered\n\n"
            
            f"📊 <b>Delivery Report:</b>\n"
            f"├─ 📦 Videos Sent: <b>{sent_count}/5</b>\n"
            f"├─ 🎯 Unique Content: <b>{unique_videos}</b>\n"
            f"├─ 📦 Total Attempts: <b>{attempts}</b>\n"
            f"└─ 🔄 Next Batch: <b>100% Fresh</b>\n\n"
            
            f"💎 <b>Bot Stats:</b>\n"
            f"├─ 🏪 Our Channel: {DISPLAY_CHANNEL}\n"
            f"├─ 🎬 Working IDs: {len(config.working_ids)}\n"
            f"└─ 🔢 ID Range: {config.min_id} - {config.max_id}\n\n"
            
            f"⚡ <b>Ready for more exclusive content?</b>\n"
            f"👇 <i>Choose another VIP tier:</i>"
        )
    else:
        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>• DELIVERY ISSUE DETECTED •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"😔 <b>We couldn't deliver your videos</b>\n"
            f"📦 Attempted: <b>{attempts}</b> different IDs\n\n"
            
            f"🔍 <b>Troubleshooting:</b>\n"
            f"├─ Check if channel exists\n"
            f"├─ Verify ID range: {config.min_id}-{config.max_id}\n"
            f"├─ Contact: @VIP_X_OFFICIAL\n"
            f"└─ Try again in few minutes\n\n"
            
            f"🔄 <b>Will you give it another try?</b>\n"
            f"👇 <i>Select any VIP button:</i>"
        )
    
    await query.edit_message_text(
        text=result_text,
        reply_markup=VIP_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

async def vip_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """VIP buttons handler"""
    await send_videos_simple(update, context)

# ================== ADMIN COMMANDS ==================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel - Updated style"""
    user = update.effective_user
    
    # Check if user is admin
    ADMIN_IDS = [7459756974]
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            f"🚫 <b>ACCESS DENIED!</b>\n\n"
            f"<i>This area is restricted to administrators only.</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    admin_text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔐 <b>• ADMINISTRATOR PANEL •</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"👑 <b>Logged in as:</b> {user.first_name}\n"
        f"📅 <b>Session:</b> Administrator Mode\n\n"
        
        f"⚙️ <b>System Status:</b>\n"
        f"├─ 🔢 ID Range: {config.min_id} ↔️ {config.max_id}\n"
        f"├─ ✅ Working IDs: {len(config.working_ids)}\n"
        f"├─ 📊 Total Sent: {config.stats['total_videos_sent']}\n"
        f"├─ 🎯 Unique Videos: {config.stats['unique_videos_sent']}\n"
        f"└─ 🤖 Bot Owner: @VIP_X_OFFICIAL\n\n"
        
        f"📋 <b>Available Controls:</b>"
    )
    
    await update.message.reply_text(
        admin_text,
        reply_markup=ADMIN_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks - Updated style"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    ADMIN_IDS = [7459756974]
    
    if user.id not in ADMIN_IDS:
        await query.edit_message_text(
            f"🔒 <b>UNAUTHORIZED ACCESS</b>\n\n"
            f"<i>Your credentials don't match administrator records.</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    action = query.data
    
    if action == 'admin_view':
        # View current settings - Updated style
        settings_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>• SYSTEM CONFIGURATION •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"📊 <b>Current Settings:</b>\n"
            f"├─ 🔢 Minimum ID: <code>{config.min_id}</code>\n"
            f"├─ 🔢 Maximum ID: <code>{config.max_id}</code>\n"
            f"├─ 📏 Total Range: {config.max_id - config.min_id + 1}\n"
            f"├─ ✅ Working IDs: {len(config.working_ids)}\n"
            f"├─ 🔄 Recently Sent: {len(config.recently_sent)}/50\n"
            f"├─ 📊 Total Sent: {config.stats['total_videos_sent']}\n"
            f"├─ 🎯 Unique Videos: {config.stats['unique_videos_sent']}\n"
            f"└─ 🔄 Total Requests: {config.stats['total_requests']}\n\n"
            
            f"🏪 <b>Channel Info:</b>\n"
            f"├─ Display Channel: {DISPLAY_CHANNEL}\n"
            f"├─ Source Channel: {CHANNEL_USERNAME}\n"
            f"└─ Owner: @VIP_X_OFFICIAL\n\n"
            
            f"⚡ <b>System:</b> <i>Operational</i>\n"
            f"🔄 <b>Randomization:</b> <i>Active</i>"
        )
        
        await query.edit_message_text(
            text=settings_text,
            reply_markup=ADMIN_KEYBOARD,
            parse_mode=ParseMode.HTML
        )
    
    elif action == 'admin_min':
        # Change minimum ID - Updated style
        await query.edit_message_text(
            text=f"🔧 <b>• ADJUST MINIMUM ID •</b>\n\n"
                 f"📊 <b>Current Value:</b> <code>{config.min_id}</code>\n\n"
                 f"📝 <b>How to Change:</b>\n"
                 f"Send command: <code>/setmin NUMBER</code>\n\n"
                 f"💡 <b>Example:</b>\n"
                 f"<code>/setmin 25</code>\n\n"
                 f"⚠️ <b>Note:</b> Must be less than current max ({config.max_id})",
            parse_mode=ParseMode.HTML
        )
    
    elif action == 'admin_max':
        # Change maximum ID - Updated style
        await query.edit_message_text(
            text=f"🔧 <b>• ADJUST MAXIMUM ID •</b>\n\n"
                 f"📊 <b>Current Value:</b> <code>{config.max_id}</code>\n\n"
                 f"📝 <b>How to Change:</b>\n"
                 f"Send command: <code>/setmax NUMBER</code>\n\n"
                 f"💡 <b>Example:</b>\n"
                 f"<code>/setmax 300</code>\n\n"
                 f"⚠️ <b>Note:</b> Must be greater than current min ({config.min_id})",
            parse_mode=ParseMode.HTML
        )
    
    elif action == 'admin_scan':
        # Auto scan for working IDs - Updated style
        await query.edit_message_text(
            text="🔍 <b>• INITIATING SYSTEM SCAN •</b>\n\n"
                 "⚡ Scanning for active video IDs...\n"
                 "📊 This process may take 1-2 minutes\n"
                 "⏳ Please do not interrupt\n\n"
                 "💡 <i>Scanning range:</i> "
                 f"<code>{config.min_id} to {config.max_id}</code>",
            parse_mode=ParseMode.HTML
        )
        
        working_found = await scan_working_ids(context.bot)
        
        if working_found:
            scan_text = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>• SCAN COMPLETED •</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                
                f"🎉 <b>Scan Results:</b>\n"
                f"├─ 🔍 Status: <b>SUCCESS</b>\n"
                f"├─ ✅ Working IDs: <b>{len(config.working_ids)}</b>\n"
                f"├─ 📏 Range: {config.min_id} ↔️ {config.max_id}\n"
                f"└─ 💾 Database: <i>Updated Successfully</i>\n\n"
                
                f"⚡ <b>System Optimized</b>\n"
                f"<i>Ready for VIP deliveries!</i>"
            )
        else:
            scan_text = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>• SCAN UNSUCCESSFUL •</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                
                f"😔 <b>Scan Results:</b>\n"
                f"├─ 🔍 Status: <b>NO ACTIVE IDs FOUND</b>\n"
                f"├─ 📏 Range: {config.min_id} ↔️ {config.max_id}\n"
                f"└─ 💡 Suggestion: Adjust ID range\n\n"
                
                f"🔧 <b>Troubleshooting:</b>\n"
                f"1. Check channel access\n"
                f"2. Verify ID range\n"
                f"3. Contact: @VIP_X_OFFICIAL"
            )
        
        await query.edit_message_text(
            text=scan_text,
            reply_markup=ADMIN_KEYBOARD,
            parse_mode=ParseMode.HTML
        )
    
    elif action == 'admin_stats':
        # Show statistics - Updated style
        stats_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>• ANALYTICS DASHBOARD •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"📊 <b>Performance Metrics:</b>\n"
            f"├─ 👥 Total Users: {config.stats['total_requests']}\n"
            f"├─ 📦 Videos Delivered: {config.stats['total_videos_sent']}\n"
            f"└─ 🎯 Unique Content: {config.stats['unique_videos_sent']}\n"
        )
        
        if config.stats['total_requests'] > 0:
            avg = config.stats['total_videos_sent'] / config.stats['total_requests']
            uniqueness = (config.stats['unique_videos_sent'] / config.stats['total_videos_sent']) * 100 if config.stats['total_videos_sent'] > 0 else 0
            stats_text += f"├─ 📈 Avg per User: {avg:.1f} videos\n"
            stats_text += f"└─ 🔄 Uniqueness Rate: {uniqueness:.1f}%\n\n"
        else:
            stats_text += "\n"
        
        stats_text += (
            f"💾 <b>System Data:</b>\n"
            f"├─ ✅ Working IDs: {len(config.working_ids)}\n"
            f"├─ 🔢 Active Range: {config.min_id} ↔️ {config.max_id}\n"
            f"├─ 🏪 Display Channel: {DISPLAY_CHANNEL}\n"
            f"├─ 🔗 Source Channel: {CHANNEL_USERNAME}\n"
            f"└─ 👑 Owner: @VIP_X_OFFICIAL\n\n"
            
            f"⚡ <b>Bot Status:</b> <i>Optimal</i>\n"
            f"🔄 <b>Randomization:</b> <i>100% Active</i>"
        )
        
        await query.edit_message_text(
            text=stats_text,
            reply_markup=ADMIN_KEYBOARD,
            parse_mode=ParseMode.HTML
        )
    
    elif action == 'admin_close':
        # Close admin panel - Updated style
        await query.edit_message_text(
            text="✅ <b>• ADMIN PANEL CLOSED •</b>\n\n"
                 f"👋 <i>Goodbye {user.first_name}!</i>\n"
                 f"🔒 <i>Session terminated securely</i>",
            parse_mode=ParseMode.HTML
        )

async def scan_working_ids(bot, batch_size=20):
    """Scan for working video IDs"""
    print(f"🔍 Scanning range {config.min_id} to {config.max_id}")
    
    new_working_ids = []
    scanned = 0
    
    # Scan in batches
    for start_id in range(config.min_id, config.max_id + 1, batch_size):
        end_id = min(start_id + batch_size - 1, config.max_id)
        
        for test_id in range(start_id, end_id + 1):
            try:
                # Try to forward to bot itself
                msg = await bot.forward_message(
                    chat_id=bot.id,
                    from_chat_id=CHANNEL_USERNAME,
                    message_id=test_id
                )
                
                # Check if it's a video
                if msg.video:
                    if test_id not in config.working_ids:
                        new_working_ids.append(test_id)
                        config.working_ids.append(test_id)
                    print(f"✅ Found working ID: {test_id}")
                
                # Delete test message
                await msg.delete()
                
            except Exception as e:
                continue
        
        scanned += batch_size
        print(f"📊 Scanned {scanned}/{config.max_id - config.min_id + 1} IDs")
    
    # Save updated working IDs
    config.save_config()
    
    return len(new_working_ids) > 0

async def set_min_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set minimum ID - Updated style"""
    user = update.effective_user
    ADMIN_IDS = [7459756974]
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🚫 <b>ACCESS RESTRICTED</b>\n\n"
            "<i>Administrator privileges required.</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 <b>Usage:</b> <code>/setmin &lt;new_min_id&gt;</code>\n\n"
            "💡 <b>Example:</b>\n"
            "<code>/setmin 25</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        new_min = int(context.args[0])
        if new_min < 1:
            await update.message.reply_text(
                "❌ <b>INVALID VALUE</b>\n\n"
                "<i>Minimum ID must be at least 1</i>",
                parse_mode=ParseMode.HTML
            )
            return
        
        if new_min >= config.max_id:
            await update.message.reply_text(
                f"❌ <b>RANGE ERROR</b>\n\n"
                f"<i>Minimum ID must be less than current max ({config.max_id})</i>",
                parse_mode=ParseMode.HTML
            )
            return
        
        old_min = config.min_id
        config.min_id = new_min
        config.save_config()
        
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>• SETTING UPDATED •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"⚙️ <b>Minimum ID Changed</b>\n\n"
            f"📊 <b>Change Details:</b>\n"
            f"├─ 📅 Previous: <code>{old_min}</code>\n"
            f"├─ 📅 New: <code>{new_min}</code>\n"
            f"└─ 📏 Current Range: {new_min} ↔️ {config.max_id}\n\n"
            
            f"💾 <b>Status:</b> <i>Saved to database</i>\n"
            f"⚡ <b>Effect:</b> <i>Immediate</i>",
            parse_mode=ParseMode.HTML
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ <b>INPUT ERROR</b>\n\n"
            "<i>Please enter a valid number</i>",
            parse_mode=ParseMode.HTML
        )

async def set_max_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set maximum ID - Updated style"""
    user = update.effective_user
    ADMIN_IDS = [7459756974]
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🚫 <b>ACCESS RESTRICTED</b>\n\n"
            "<i>Administrator privileges required.</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 <b>Usage:</b> <code>/setmax &lt;new_max_id&gt;</code>\n\n"
            "💡 <b>Example:</b>\n"
            "<code>/setmax 500</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        new_max = int(context.args[0])
        if new_max <= config.min_id:
            await update.message.reply_text(
                f"❌ <b>RANGE ERROR</b>\n\n"
                f"<i>Maximum ID must be greater than current min ({config.min_id})</i>",
                parse_mode=ParseMode.HTML
            )
            return
        
        old_max = config.max_id
        config.max_id = new_max
        config.save_config()
        
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>• SETTING UPDATED •</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"⚙️ <b>Maximum ID Changed</b>\n\n"
            f"📊 <b>Change Details:</b>\n"
            f"├─ 📅 Previous: <code>{old_max}</code>\n"
            f"├─ 📅 New: <code>{new_max}</code>\n"
            f"└─ 📏 Current Range: {config.min_id} ↔️ {new_max}\n\n"
            
            f"💾 <b>Status:</b> <i>Saved to database</i>\n"
            f"⚡ <b>Effect:</b> <i>Immediate</i>",
            parse_mode=ParseMode.HTML
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ <b>INPUT ERROR</b>\n\n"
            "<i>Please enter a valid number</i>",
            parse_mode=ParseMode.HTML
        )

async def clear_recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear recently sent list - Updated style"""
    user = update.effective_user
    ADMIN_IDS = [7459756974]
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🚫 <b>ACCESS RESTRICTED</b>\n\n"
            "<i>Administrator privileges required.</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    old_count = len(config.recently_sent)
    config.recently_sent = []
    config.save_config()
    
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧹 <b>• CACHE CLEARED •</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"🔄 <b>History Reset Complete</b>\n\n"
        f"📊 <b>Cleared Items:</b>\n"
        f"├─ 🗑️ Recently Sent IDs: <b>{old_count}</b>\n"
        f"└─ 💾 Database: <i>Optimized</i>\n\n"
        
        f"⚡ <b>Effect:</b>\n"
        f"<i>Bot will now deliver 100% fresh content</i>\n"
        f"<i>No repetition in next deliveries</i>",
        parse_mode=ParseMode.HTML
    )

def main():
    """Bot start karein"""
    # Application create karein
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(vip_button_handler, pattern='^vip[1-5]$'))
    
    # Admin command handlers
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("setmin", set_min_id))
    application.add_handler(CommandHandler("setmax", set_max_id))
    application.add_handler(CommandHandler("clearrecent", clear_recent_command))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^admin_'))
    
    # Bot start karein
    print("=" * 60)
    print("🤖 • VIP X OFFICIAL VIDEO BOT •")
    print("=" * 60)
    print(f"🏪 Display Channel: {DISPLAY_CHANNEL}")
    print(f"🔗 Source Channel: {CHANNEL_USERNAME}")
    print(f"👑 Owner: @VIP_X_OFFICIAL")
    print(f"🔢 Range: {config.min_id} ↔️ {config.max_id}")
    print(f"✅ Working IDs: {len(config.working_ids)}")
    print(f"🔄 Recently Sent: {len(config.recently_sent)}")
    print("=" * 60)
    print("🎯 • PREMIUM FEATURES •")
    print("  ✅ 100% Random Selection Every Time")
    print("  ✅ No Content Repetition")
    print("  ✅ Premium VIP Tiers")
    print("  ✅ Instant Video Delivery")
    print("  ✅ Advanced Admin Controls")
    print("=" * 60)
    print("🔧 • ADMIN COMMANDS •")
    print("  /admin - Access Control Panel")
    print("  /setmin <id> - Adjust Minimum ID")
    print("  /setmax <id> - Adjust Maximum ID")
    print("  /clearrecent - Clear Recent History")
    print("=" * 60)
    print(f"\n⚡ Bot Status: READY")
    print(f"👑 Owner: @VIP_X_OFFICIAL")
    print(f"🎬 Delivering premium content since 2024")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()