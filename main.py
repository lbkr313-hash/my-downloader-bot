import telebot
from telebot import types
import yt_dlp
import os
import time
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات البوت والقنوات ---
API_TOKEN = '8281760855:AAFzk0H_uL2HLPZxg7K63OK5bvavUhrNypg'
CHANNELS = ['@dhjbr', '@hhhhh3i'] 

bot = telebot.TeleBot(API_TOKEN)
executor = ThreadPoolExecutor(max_workers=4)
urls_map = {}

# دالة فحص الاشتراك
def check_sub(u_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, u_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            continue
    return True

@bot.message_handler(func=lambda m: True)
def handle_messages(m):
    u_id, c_id = m.from_user.id, m.chat.id
    
    if not check_sub(u_id):
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("قناة 1 ✅", url="https://t.me/dhjbr")
        btn2 = types.InlineKeyboardButton("قناة 2 ✅", url="https://t.me/hhhhh3i")
        btn_confirm = types.InlineKeyboardButton("تم الاشتراك ✨ (تفعيل)", callback_data="check_status")
        kb.add(btn1, btn2)
        kb.add(btn_confirm)
        bot.send_message(c_id, "عذراً، يجب عليك الاشتراك في قنوات البوت أولاً!", reply_markup=kb)
        return

    text = m.text
    if text.startswith('/start'):
        bot.reply_to(m, "أهلاً بك في بوت التحميل 🚀\nأرسل رابط فيديو أو اكتب اسم للبحث عنه.")
    elif "youtube.com" in text or "youtu.be" in text:
        show_formats(c_id, text)
    else:
        perform_search(c_id, text)

def perform_search(c_id, query):
    msg = bot.send_message(c_id, "🔍 جاري البحث عن نتائج...")
    try:
        ydl_opts = {
            'quiet': True, 
            'extract_flat': True, 
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
            kb = types.InlineKeyboardMarkup()
            for entry in res:
                v_id = entry['id']
                urls_map[v_id] = f"https://www.youtube.com/watch?v={v_id}"
                kb.add(types.InlineKeyboardButton(entry['title'][:50], callback_data=f"sel_{v_id}"))
            bot.edit_message_text("اختر الفيديو المطلوب:", c_id, msg.message_id, reply_markup=kb)
    except:
        bot.edit_message_text("❌ لم أتمكن من العثور على نتائج.", c_id, msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    c_id, u_id = call.message.chat.id, call.from_user.id
    
    if call.data == "check_status":
        if check_sub(u_id):
            bot.delete_message(c_id, call.message.message_id)
            bot.send_message(c_id, "تم تفعيل البوت بنجاح! 🚀")
        else:
            bot.answer_callback_query(call.id, "لم تشترك في القنوات بعد! ❌", show_alert=True)
        return

    if not check_sub(u_id): return

    if call.data.startswith("sel_"):
        v_id = call.data.split("_")[1]
        show_formats(c_id, urls_map.get(v_id))
        bot.delete_message(c_id, call.message.message_id)
    
    elif call.data.startswith(("q144_", "q360_", "aud_")):
        q, v_id = call.data.split("_")
        url = urls_map.get(v_id)
        executor.submit(start_download, c_id, url, q)
        bot.delete_message(c_id, call.message.message_id)

def show_formats(c_id, url):
    try:
        v_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
        v_id = v_id.split("&")[0].split("?")[0]
        urls_map[v_id] = url
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🎬 فيديو 144p", callback_data=f"q144_{v_id}"),
               types.InlineKeyboardButton("🎬 فيديو 360p", callback_data=f"q360_{v_id}"))
        kb.add(types.InlineKeyboardButton("🎵 ملف صوتي (MP3)", callback_data=f"aud_{v_id}"))
        bot.send_message(c_id, "اختر الصيغة والجودة:", reply_markup=kb)
    except:
        bot.send_message(c_id, "❌ رابط غير صحيح.")

def start_download(c_id, url, quality):
    status_msg = bot.send_message(c_id, "🚀 جاري التحميل، يرجى الانتظار...")
    try:
        fmt = 'best[height<=144]' if quality == 'q144' else 'best[height<=360]' if quality == 'q360' else 'bestaudio'
        out_path = f"file_{c_id}_{int(time.time())}.%(ext)s"
        
        ydl_opts = {
            'format': fmt,
            'outtmpl': out_path,
            'noplaylist': True,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
        
        with open(filename, 'rb') as f:
            if 'q' in quality:
                bot.send_video(c_id, f, caption=f"🎬 {title}\nتم التحميل بواسطة @ytyoutebot")
            else:
                bot.send_audio(c_id, f, title=title, caption=f"🎵 {title}\nتم التحميل بواسطة @ytyoutebot")
        
        if os.path.exists(filename):
            os.remove(filename)
        bot.delete_message(c_id, status_msg.message_id)
        
    except Exception as e:
        bot.send_message(c_id, f"❌ حدث خطأ أثناء التحميل: {str(e)}")

print("البوت يعمل الآن بكفاءة... ✅")
bot.infinity_polling()
        kb.add(btn_confirm)
        bot.send_message(c_id, "عذراً، يجب عليك الاشتراك في قنوات البوت أولاً!", reply_markup=kb)
        return

    text = m.text
    if text.startswith('/start'):
        bot.reply_to(m, "أهلاً بك في بوت التحميل 🚀\nأرسل رابط فيديو أو اكتب اسم للبحث عنه.")
    elif "youtube.com" in text or "youtu.be" in text:
        show_formats(c_id, text)
    else:
        perform_search(c_id, text)

def perform_search(c_id, query):
    msg = bot.send_message(c_id, "🔍 جاري البحث عن نتائج...")
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
            kb = types.InlineKeyboardMarkup()
            for entry in res:
                v_id = entry['id']
                urls_map[v_id] = f"https://www.youtube.com/watch?v={v_id}"
                kb.add(types.InlineKeyboardButton(entry['title'][:50], callback_data=f"sel_{v_id}"))
            bot.edit_message_text("اختر الفيديو المطلوب:", c_id, msg.message_id, reply_markup=kb)
    except:
        bot.edit_message_text("❌ لم أتمكن من العثور على نتائج.", c_id, msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    c_id, u_id = call.message.chat.id, call.from_user.id
    
    if call.data == "check_status":
        if check_sub(u_id):
            bot.delete_message(c_id, call.message.message_id)
            bot.send_message(c_id, "تم تفعيل البوت بنجاح! 🚀")
        else:
            bot.answer_callback_query(call.id, "لم تشترك في القنوات بعد! ❌", show_alert=True)
        return

    if not check_sub(u_id): return

    if call.data.startswith("sel_"):
        v_id = call.data.split("_")[1]
        show_formats(c_id, urls_map.get(v_id))
        bot.delete_message(c_id, call.message.message_id)
    
    elif call.data.startswith(("q144_", "q360_", "aud_")):
        q, v_id = call.data.split("_")
        url = urls_map.get(v_id)
        executor.submit(start_download, c_id, url, q)
        bot.delete_message(c_id, call.message.message_id)

def show_formats(c_id, url):
    try:
        v_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
        v_id = v_id.split("&")[0].split("?")[0]
        urls_map[v_id] = url
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🎬 فيديو 144p", callback_data=f"q144_{v_id}"),
               types.InlineKeyboardButton("🎬 فيديو 360p", callback_data=f"q360_{v_id}"))
        kb.add(types.InlineKeyboardButton("🎵 ملف صوتي (MP3)", callback_data=f"aud_{v_id}"))
        bot.send_message(c_id, "اختر الصيغة والجودة:", reply_markup=kb)
    except:
        bot.send_message(c_id, "❌ رابط غير صحيح.")

def start_download(c_id, url, quality):
    status_msg = bot.send_message(c_id, "🚀 جاري التحميل، يرجى الانتظار...")
    try:
        fmt = 'best[height<=144]' if quality == 'q144' else 'best[height<=360]' if quality == 'q360' else 'bestaudio'
        # تم تصحيح السطر أدناه: استخدام time.time() بدلاً من os.time.time()
        out_path = f"file_{c_id}_{int(time.time())}.%(ext)s"
        
        ydl_opts = {
            'format': fmt,
            'outtmpl': out_path,
            'noplaylist': True,
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
        
        with open(filename, 'rb') as f:
            if 'q' in quality:
                bot.send_video(c_id, f, caption=f"🎬 {title}\nتم التحميل بواسطة @ytyoutebot")
            else:
                bot.send_audio(c_id, f, title=title, caption=f"🎵 {title}\nتم التحميل بواسطة @ytyoutebot")
        
        if os.path.exists(filename):
            os.remove(filename)
        bot.delete_message(c_id, status_msg.message_id)
        
    except Exception as e:
        bot.send_message(c_id, f"❌ حدث خطأ أثناء التحميل: {str(e)}")

print("البوت يعمل الآن بكفاءة... ✅")
bot.infinity_polling()
