import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    filters
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8037134302:AAGqZikLopxQ8x7Klb3C_IeYonsRHBtrR1k"
ADMIN_CHAT_ID = -1002848735369
ADMIN_ID = 397556747  # Your brother's Telegram user ID

# Database structure
menu_db = {
    "categories": {
        "drinks": {
            "name": "Ichimliklar 🥤",
            "image": None,
            "items": {
                "coffee": {"name": "Kofe", "price": 15000, "image": None},
                "tea": {"name": "Choy", "price": 10000, "image": None}
            }
        },
        "foods": {
            "name": "Yeguliklar 🍽️",
            "image": None,
            "items": {
                "sandwich": {"name": "Sendvich", "price": 25000, "image": None},
                "plov": {"name": "Osh", "price": 30000, "image": None},
                "salat": {"name": "Salat", "price": 30000, "image": None}
            }
        }
    }
}

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Menyu 🍽️", callback_data="view_categories")],
        [InlineKeyboardButton("Savatim 🛒", callback_data="view_cart")]
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("Admin Panel ⚙️", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            f"HojiAkbar onlayn kafesiga Hush kelibsiz, {user.first_name}!",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            f"HojiAkbar onlayn kafesiga Hush kelibsiz, {user.first_name}!",
            reply_markup=reply_markup
        )

async def view_categories(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for cat_id, category in menu_db["categories"].items():
        keyboard.append([InlineKeyboardButton(category["name"], callback_data=f"view_category_{cat_id}")])
    
    if is_admin(query.from_user.id):
        keyboard.append([InlineKeyboardButton("Admin Panel ⚙️", callback_data="admin_panel")])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data="back_to_start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Kategoriya tanlang:", reply_markup=reply_markup)

async def view_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    category = menu_db["categories"][cat_id]
    
    keyboard = []
    for item_id, item in category["items"].items():
        price = item.get("price", item.get("narxi", 0))  # Handle both "price" and "narxi"
        keyboard.append([InlineKeyboardButton(f"{item['name']} - {price} UZS", callback_data=f"add_{cat_id}_{item_id}")])
    
    if is_admin(query.from_user.id):
        keyboard.append([InlineKeyboardButton("Tahrirlash ✏️", callback_data=f"admin_edit_category_{cat_id}")])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data="view_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if category.get("image"):
        await query.edit_message_media(
            media=InputMediaPhoto(media=category["image"], caption=category["name"]),
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(text=category["name"], reply_markup=reply_markup)

async def add_to_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    # Extract category and item IDs
    _, cat_id, item_id = query.data.split("_")
    item = menu_db["categories"][cat_id]["items"][item_id]
    
    # Initialize cart if not exists
    if "cart" not in context.user_data:
        context.user_data["cart"] = {}
    
    # Initialize item in cart if not exists
    if item_id not in context.user_data["cart"]:
        context.user_data["cart"][item_id] = {
            "name": item["name"],
            "price": item["price"],
            "quantity": 0,
            "category": cat_id
        }
    
    # Update quantity
    context.user_data["cart"][item_id]["quantity"] += 1
    
    await query.answer(f"✅ {item['name']} savatga qo'shildi!")

async def view_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if "cart" not in context.user_data or not context.user_data["cart"]:
        await query.edit_message_text(text="Savat bo'sh!")
        return
    
    cart_text = "🛒 Savatingiz:\n\n"
    total = 0
    
    for item_id, item_data in context.user_data["cart"].items():
        quantity = item_data["quantity"]
        price = item_data["price"]
        item_total = quantity * price
        total += item_total
        
        cart_text += (
            f"{item_data['name']}\n"
            f"  - Miqdor: {quantity}\n"
            f"  - Narx: {price} UZS\n"
            f"  - Jami: {item_total} UZS\n\n"
        )
    
    cart_text += f"💵 Umumiy summa: {total} UZS"
    
    keyboard = [
        [InlineKeyboardButton("Buyurtma berish ✅", callback_data="place_order")],
        [InlineKeyboardButton("Menyuga qaytish 🔙", callback_data="view_categories")],
        [InlineKeyboardButton("Savatni tozalash 🗑️", callback_data="clear_cart")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=cart_text, reply_markup=reply_markup)

async def clear_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if "cart" in context.user_data:
        context.user_data["cart"] = {}
    
    await query.edit_message_text(text="Savat tozalandi!")

async def place_order(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if "cart" not in context.user_data or not context.user_data["cart"]:
        await query.edit_message_text(text="Savat bo'sh!")
        return
    
    # Prepare order details
    order_text = "📝 Yangi buyurtma!\n\n"
    total = 0
    
    for item_id, item_data in context.user_data["cart"].items():
        quantity = item_data["quantity"]
        price = item_data["price"]
        item_total = quantity * price
        total += item_total
        
        order_text += (
            f"{item_data['name']}\n"
            f"  - Miqdor: {quantity}\n"
            f"  - Narx: {price} UZS\n"
            f"  - Jami: {item_total} UZS\n\n"
        )
    
    order_text += f"💵 Umumiy summa: {total} UZS\n\n"
    order_text += f"👤 Mijoz: {query.from_user.mention_markdown()}\n"
    order_text += f"🆔 ID: {query.from_user.id}"
    
    # Send to admin group
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )
    
    # Clear cart and confirm to user
    context.user_data["cart"] = {}
    await query.edit_message_text(
        text="✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Asosiy menyu", callback_data="back_to_start")]
        ])
    )

# ADMIN FUNCTIONS
async def admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("⚠️ Sizda admin huquqlari yo'q!")
        return
    
    keyboard = [
        [InlineKeyboardButton("Kategoriya qo'shish", callback_data="admin_add_category")],
        [InlineKeyboardButton("Kategoriyalarni ko'rish", callback_data="admin_view_categories")],
        [InlineKeyboardButton("Mahsulot qo'shish", callback_data="admin_add_item_select_category")],
        [InlineKeyboardButton("Ortga 🔙", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="⚙️ Admin Panel:", reply_markup=reply_markup)

async def admin_add_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Yangi kategoriya nomini yuboring (masalan: 'Shirinliklar 🍰'):")
    context.user_data["admin_action"] = "awaiting_category_name"

async def admin_view_categories(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for cat_id, category in menu_db["categories"].items():
        keyboard.append([
            InlineKeyboardButton(category["name"], callback_data=f"admin_edit_category_{cat_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Tahrirlash uchun kategoriyani tanlang:", reply_markup=reply_markup)

async def admin_edit_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    category = menu_db["categories"][cat_id]
    
    keyboard = [
        [InlineKeyboardButton("Nomni o'zgartirish", callback_data=f"admin_change_category_name_{cat_id}")],
        [InlineKeyboardButton("Rasmni o'zgartirish", callback_data=f"admin_change_category_image_{cat_id}")],
        [InlineKeyboardButton("Mahsulot qo'shish", callback_data=f"admin_add_item_{cat_id}")],
        [InlineKeyboardButton("Mahsulotlarni ko'rish", callback_data=f"admin_view_items_{cat_id}")],
        [InlineKeyboardButton("O'chirish", callback_data=f"admin_delete_category_{cat_id}")],
        [InlineKeyboardButton("Ortga 🔙", callback_data="admin_view_categories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Kategoriya: {category['name']}", reply_markup=reply_markup)

async def admin_add_item_select_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for cat_id, category in menu_db["categories"].items():
        keyboard.append([
            InlineKeyboardButton(category["name"], callback_data=f"admin_add_item_{cat_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Mahsulot qo'shish uchun kategoriyani tanlang:", reply_markup=reply_markup)

async def admin_add_item(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    context.user_data["admin_action"] = "awaiting_item_name"
    context.user_data["current_category"] = cat_id
    await query.edit_message_text(f"Yangi mahsulot nomini yuboring (masalan: 'Pepsi'):")

async def admin_handle_messages(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return
    
    action = context.user_data.get("admin_action")
    
    if action == "awaiting_category_name":
        category_name = update.message.text
        cat_id = category_name.lower().replace(" ", "_").replace("'", "")
        menu_db["categories"][cat_id] = {
            "name": category_name,
            "image": None,
            "items": {}
        }
        await update.message.reply_text(
            f"Kategoriya '{category_name}' qo'shildi! Endi kategoriya uchun rasm yuboring.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bekor qilish", callback_data="admin_panel")]
            ])
        )
        context.user_data["admin_action"] = "awaiting_category_image"
        context.user_data["current_category"] = cat_id
    
    elif action == "awaiting_category_image":
        if update.message.photo:
            cat_id = context.user_data["current_category"]
            photo_file = await update.message.photo[-1].get_file()
            menu_db["categories"][cat_id]["image"] = photo_file.file_path
            await update.message.reply_text(
                "Kategoriya rasmi saqlandi!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Admin Panel", callback_data="admin_panel")]
                ])
            )
        else:
            await update.message.reply_text("Iltimos, rasm yuboring!")
    
    elif action == "awaiting_item_name":
        item_name = update.message.text
        context.user_data["item_name"] = item_name
        context.user_data["admin_action"] = "awaiting_item_price"
        await update.message.reply_text(f"Mahsulot narxini yuboring (masalan: 15000):")
    
    elif action == "awaiting_item_price":
        try:
            price = int(update.message.text)
            cat_id = context.user_data["current_category"]
            item_name = context.user_data["item_name"]
            item_id = item_name.lower().replace(" ", "_").replace("'", "")
            
            menu_db["categories"][cat_id]["items"][item_id] = {
                "name": item_name,
                "price": price,
                "image": None
            }
            
            await update.message.reply_text(
                f"Mahsulot '{item_name}' qo'shildi! Endi mahsulot uchun rasm yuboring.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{cat_id}")]
                ])
            )
            context.user_data["admin_action"] = "awaiting_item_image"
        
        except ValueError:
            await update.message.reply_text("Noto'g'ri format! Faqat raqam kiriting (masalan: 15000)")
    
    elif action == "awaiting_item_image":
        if update.message.photo:
            cat_id = context.user_data["current_category"]
            item_name = context.user_data["item_name"]
            item_id = item_name.lower().replace(" ", "_").replace("'", "")
            photo_file = await update.message.photo[-1].get_file()
            menu_db["categories"][cat_id]["items"][item_id]["image"] = photo_file.file_path
            await update.message.reply_text(
                "Mahsulot rasmi saqlandi!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Kategoriyaga qaytish", callback_data=f"admin_edit_category_{cat_id}")]
                ])
            )
        else:
            await update.message.reply_text("Iltimos, rasm yuboring!")
    
    context.user_data["admin_action"] = None

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern="back_to_start"))
    application.add_handler(CallbackQueryHandler(view_categories, pattern="view_categories"))
    application.add_handler(CallbackQueryHandler(view_category, pattern="view_category_"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="add_"))
    application.add_handler(CallbackQueryHandler(view_cart, pattern="view_cart"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="clear_cart"))
    application.add_handler(CallbackQueryHandler(place_order, pattern="place_order"))
    
    # Admin commands
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="admin_panel"))
    application.add_handler(CallbackQueryHandler(admin_add_category, pattern="admin_add_category"))
    application.add_handler(CallbackQueryHandler(admin_view_categories, pattern="admin_view_categories"))
    application.add_handler(CallbackQueryHandler(admin_edit_category, pattern="admin_edit_category_"))
    application.add_handler(CallbackQueryHandler(admin_add_item_select_category, pattern="admin_add_item_select_category"))
    application.add_handler(CallbackQueryHandler(admin_add_item, pattern="admin_add_item_"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, admin_handle_messages))
    
    application.run_polling()

if __name__ == "__main__":
    main()