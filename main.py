import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

import os
TOKEN = os.getenv("TOKEN")
DATA_FILE = "data.json"

# ---------- DATA ----------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------- ГОЛОВНЕ МЕНЮ (хелпер) ----------
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Манга", callback_data="manga")],
        [InlineKeyboardButton("🎬 Аніме", callback_data="anime")],
        [InlineKeyboardButton("🎥 Серіали", callback_data="series")],
        [InlineKeyboardButton("📋 Мій список", callback_data="list")]
    ])

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Обери категорію:",
        reply_markup=main_menu_keyboard()
    )

# ---------- MENU COMMAND ----------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Обери категорію:",
        reply_markup=main_menu_keyboard()
    )

# ---------- ADD COMMAND ----------  ← НОВА КОМАНДА
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📖 Манга", callback_data="manga")],
        [InlineKeyboardButton("🎬 Аніме", callback_data="anime")],
        [InlineKeyboardButton("🎥 Серіали", callback_data="series")],
    ]
    await update.message.reply_text(
        "Що додаємо?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- CALLBACK ----------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"manga": [], "anime": [], "series": []}

    choice = query.data

    # --- ГОЛОВНЕ МЕНЮ ---
    if choice == "main_menu":
        context.user_data.clear()
        await query.message.reply_text(
            "Обери категорію:",
            reply_markup=main_menu_keyboard()
        )

    # --- ДОДАТИ ---
    elif choice in ["manga", "anime", "series"]:
        context.user_data.clear()
        context.user_data["type"] = choice
        await query.message.reply_text("Введи назву:")

    # --- СПИСОК ---
    elif choice == "list":
        keyboard = [
            [InlineKeyboardButton("📖 Манга", callback_data="list_manga")],
            [InlineKeyboardButton("🎬 Аніме", callback_data="list_anime")],
            [InlineKeyboardButton("🎥 Серіали", callback_data="list_series")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
        ]
        await query.message.reply_text("Обери:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif choice.startswith("list_"):
        category = choice.split("_")[1]
        items = data[user_id][category]

        if not items:
            await query.message.reply_text(
                "Пусто 😢",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
                ])
            )
            return

        keyboard = []
        for i, item in enumerate(items):
            keyboard.append([
                InlineKeyboardButton(
                    f"{item['title']} ({item['status']})",
                    callback_data=f"item_{category}_{i}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")])

        await query.message.reply_text(
            "Обери тайтл:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- КОНКРЕТНИЙ ТАЙТЛ ---
    elif choice.startswith("item_"):
        _, category, index = choice.split("_")
        index = int(index)

        context.user_data["edit"] = (category, index)
        item = data[user_id][category][index]

        keyboard = [
            [InlineKeyboardButton("🔗 Відкрити", url=item["link"])],
            [InlineKeyboardButton("✏️ Змінити статус", callback_data="edit_status")],
            [InlineKeyboardButton("🗑️ Видалити", callback_data="delete")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
        ]

        await query.message.reply_text(
            f"{item['title']}\nСтатус: {item['status']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- ВИДАЛЕННЯ ---
    elif choice == "delete":
        category, index = context.user_data["edit"]
        del data[user_id][category][index]

        save_data(data)
        context.user_data.clear()

        await query.message.reply_text(
            "🗑️ Видалено!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
            ])
        )

    # --- РЕДАГУВАННЯ ---
    elif choice == "edit_status":
        keyboard = [
            [InlineKeyboardButton("📖 Дивлюсь/Читаю", callback_data="status_watching")],
            [InlineKeyboardButton("✅ Завершено", callback_data="status_done")],
            [InlineKeyboardButton("⏸️ На паузі", callback_data="status_pause")],
            [InlineKeyboardButton("❌ Кинув", callback_data="status_drop")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
        ]

        await query.message.reply_text(
            "Обери новий статус:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- ЗБЕРЕГТИ СТАТУС ---
    elif choice.startswith("status_"):
        status = choice.replace("status_", "")

        if "edit" in context.user_data:
            category, index = context.user_data["edit"]
            data[user_id][category][index]["status"] = status

            save_data(data)
            context.user_data.clear()

            await query.message.reply_text(
                "✏️ Оновлено!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
                ])
            )

        else:
            title = context.user_data["title"]
            category = context.user_data["type"]
            link = context.user_data.get("link", "—")

            data[user_id][category].append({
                "title": title,
                "status": status,
                "link": link
            })

            save_data(data)
            context.user_data.clear()

            await query.message.reply_text(
                "✅ Додано!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")]
                ])
            )

# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "type" in context.user_data and "title" not in context.user_data:
        context.user_data["title"] = text
        await update.message.reply_text("Надішли посилання або напиши 'skip'")

    elif "title" in context.user_data and "link" not in context.user_data:
        if text.lower() == "skip":
            context.user_data["link"] = "—"
        else:
            context.user_data["link"] = text

        keyboard = [
            [InlineKeyboardButton("📖 Дивлюсь/Читаю", callback_data="status_watching")],
            [InlineKeyboardButton("✅ Завершено", callback_data="status_done")],
            [InlineKeyboardButton("⏸️ На паузі", callback_data="status_pause")],
            [InlineKeyboardButton("❌ Кинув", callback_data="status_drop")]
        ]

        await update.message.reply_text(
            "Обери статус:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        # Якщо юзер пише щось не в контексті — показуємо меню  ← НОВЕ
        await update.message.reply_text(
            "Обери категорію:",
            reply_markup=main_menu_keyboard()
        )

# ---------- RUN ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))  
app.add_handler(CommandHandler("add", add))    
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()
