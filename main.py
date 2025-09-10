
import os, json, logging, random
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set. Exiting.")
    raise SystemExit("BOT_TOKEN not set")

# load cases
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, "cases.json"), "r", encoding="utf-8") as f:
    CASES = json.load(f)

def start(update: Update, context: CallbackContext):
    text = "أهلًا بك في *ECG with Abu Eid* 👋\nاختر من القائمة أدناه:"
    keyboard = [
        [InlineKeyboardButton("📚 قسم التعليم", callback_data="menu_teach")],
        [InlineKeyboardButton("🩺 حالات ECG", callback_data="menu_cases")],
        [InlineKeyboardButton("📝 اختبارات", callback_data="menu_quiz")],
    ]
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    query.answer()
    if data == "menu_teach":
        send_teach_intro(query)
    elif data == "menu_cases":
        send_cases_list(query, page=0)
    elif data == "menu_quiz":
        send_quiz_menu(query)

def send_teach_intro(query):
    text = ("قسم التعلم:\n\n"
            "مقدمة عن ECG وأساسية القراءة:\n"
            "1. موجة P: atrial depolarization.\n"
            "2. QRS: ventricular depolarization.\n"
            "3. T: ventricular repolarization.\n\n"
            "تقدر ترجع للقائمة بالأسفل.")
    keyboard = [[InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main")]]
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def send_cases_list(query, page=0, per_page=8):
    # show paginated list of cases
    start = page*per_page
    items = CASES[start:start+per_page]
    keyboard = []
    for c in items:
        keyboard.append([InlineKeyboardButton(f"{c['id']}. {c['title']}", callback_data=f"case_{c['id']}")])
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"cases_page_{page-1}"))
    if start+per_page < len(CASES):
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"cases_page_{page+1}"))
    nav.append(InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main"))
    keyboard.append(nav)
    query.edit_message_text("اختر الحالة من القائمة:", reply_markup=InlineKeyboardMarkup(keyboard))

def send_case_detail(query, case_id):
    case = next((c for c in CASES if c["id"]==case_id), None)
    if not case:
        query.answer("Case not found", show_alert=True)
        return
    caption = f"*{case['title']}*\n\n{case['short_description']}"
    keyboard = [
        [InlineKeyboardButton("📝 اختبار لهذه الحالة", callback_data=f"quiz_case_{case_id}")],
        [InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="menu_cases")]
    ]
    # send photo - edit_message_text can't include photo, so send a new message
    try:
        query.message.reply_photo(photo=open(os.path.join(os.path.dirname(__file__), case["image"]), "rb"), caption=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        # optionally delete previous menu message
        try:
            query.message.delete()
        except:
            pass
    except Exception as e:
        logger.exception("Failed to send image: %s", e)
        query.edit_message_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def send_quiz_menu(query):
    keyboard = [
        [InlineKeyboardButton("اختبار عشوائي", callback_data="quiz_random")],
        [InlineKeyboardButton("اختبار حسب رقم الحالة", callback_data="quiz_by_number")],
        [InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main")],
    ]
    query.edit_message_text("اختر نوع الاختبار:", reply_markup=InlineKeyboardMarkup(keyboard))

def send_quiz_for_case(query, case_id):
    case = next((c for c in CASES if c["id"]==case_id), None)
    if not case:
        query.answer("Case not found", show_alert=True)
        return
    q = case["quiz"]
    keyboard = []
    for idx, opt in enumerate(q["options"]):
        keyboard.append([InlineKeyboardButton(opt, callback_data=f"answer_{case_id}_{idx}")])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع للحالة", callback_data=f"case_{case_id}")])
    # send image + question
    try:
        query.message.reply_photo(photo=open(os.path.join(os.path.dirname(__file__), case["image"]), "rb"),
                                  caption=f"*سؤال للاختبار:*\n{q['question']}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        try:
            query.message.delete()
        except:
            pass
    except Exception as e:
        logger.exception("failed send quiz image: %s", e)
        query.edit_message_text(f"{q['question']}", reply_markup=InlineKeyboardMarkup(keyboard))

def handle_answer(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    query.answer()
    if data.startswith("answer_"):
        parts = data.split("_")
        case_id = int(parts[1]); idx = int(parts[2])
        case = next((c for c in CASES if c["id"]==case_id), None)
        correct = case["quiz"]["answer_index"]
        if idx == correct:
            query.edit_message_text("✅ صحيح! ممتاز.", parse_mode="Markdown")
        else:
            correct_text = case["quiz"]["options"][correct]
            query.edit_message_text(f"❌ خطأ. الإجابة الصحيحة: *{correct_text}*", parse_mode="Markdown")

def back_main(query):
    text = "رجعنا للقائمة الرئيسية:"
    keyboard = [
        [InlineKeyboardButton("📚 قسم التعليم", callback_data="menu_teach")],
        [InlineKeyboardButton("🩺 حالات ECG", callback_data="menu_cases")],
        [InlineKeyboardButton("📝 اختبارات", callback_data="menu_quiz")],
    ]
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def callback_router(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    # routing
    if data.startswith("cases_page_"):
        page = int(data.split("_")[-1])
        send_cases_list(query, page=page)
    elif data.startswith("case_") and data.startswith("case_") and data.count("_")==1:
        case_id = int(data.split("_")[-1])
        send_case_detail(query, case_id)
    elif data == "menu_teach" or data == "menu_cases" or data == "menu_quiz":
        menu_callback(update, context)
    elif data == "back_main":
        back_main(query)
    elif data.startswith("quiz_case_"):
        case_id = int(data.split("_")[-1])
        send_quiz_for_case(query, case_id)
    elif data == "quiz_random":
        case = random.choice(CASES)
        send_quiz_for_case(query, case["id"])
    elif data.startswith("answer_"):
        handle_answer(update, context)
    elif data == "quiz_by_number":
        # ask user to send a number
        query.message.reply_text("ارسِل رقم الحالة اللي تبغى تختبرها (مثال: 5)")
        try:
            query.message.delete()
        except:
            pass

def text_handler(update: Update, context: CallbackContext):
    txt = update.message.text.strip()
    if txt.isdigit():
        num = int(txt)
        if 1 <= num <= len(CASES):
            send_quiz_for_case(update, num)
        else:
            update.message.reply_text("رقم غير صالح.")
    else:
        update.message.reply_text("اكتب /start للرجوع للقائمة أو اختر زر من الواجهة.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callback_router))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
    updater.start_polling()
    logger.info("Bot started")
    updater.idle()

if __name__ == "__main__":
    main()
