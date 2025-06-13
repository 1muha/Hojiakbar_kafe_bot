import logging
import os
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
    format='%(asctime)s - %(nexitame)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7850850916:AAFuFUgr6-X-L96Eik2lpuX1kMkw2LrBeKA"
ADMIN_CHAT_ID = -1002848735369
ADMIN_ID = 397556747  # Your brother's Telegram user ID

# Create images directory if it doesn't exist
if not os.path.exists('images'):
    os.makedirs('images')

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
        price = item.get("price", item.get("narxi", 0))
        keyboard.append([InlineKeyboardButton(f"{item['name']} - {price} UZS", callback_data=f"add_{cat_id}_{item_id}")])
    
    if is_admin(query.from_user.id):
        keyboard.append([InlineKeyboardButton("Tahrirlash ✏️", callback_data=f"admin_edit_category_{cat_id}")])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data="view_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if category has an image and it exists
    if category.get("image") and os.path.exists(category["image"]):
        try:
            with open(category["image"], 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=category["name"],
                    reply_markup=reply_markup
                )
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await query.edit_message_text(text=category["name"], reply_markup=reply_markup)
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
        keyboard = [[InlineKeyboardButton("Menyuga qaytish 🔙", callback_data="view_categories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Savat bo'sh!", reply_markup=reply_markup)
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
        [InlineKeyboardButton("Buyurtma berish ✅", callback_data="request_phone")],
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
    
    keyboard = [[InlineKeyboardButton("Menyuga qaytish 🔙", callback_data="view_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Savat tozalandi!", reply_markup=reply_markup)

async def request_phone(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if "cart" not in context.user_data or not context.user_data["cart"]:
        await query.edit_message_text(text="Savat bo'sh!")
        return
    
    context.user_data["awaiting_phone"] = True
    keyboard = [[InlineKeyboardButton("Bekor qilish", callback_data="view_cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="📞 Iltimos, telefon raqamingizni yuboring (masalan: +998901234567):",
        reply_markup=reply_markup
    )

async def place_order(update: Update, context: CallbackContext):
    phone_number = context.user_data.get("phone_number")
    
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
    order_text += f"👤 Mijoz: {update.effective_user.mention_markdown()}\n"
    order_text += f"🆔 ID: {update.effective_user.id}\n"
    order_text += f"📞 Telefon: {phone_number}"
    
    # Send to admin group
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )
    
    # Clear cart and phone number, and confirm to user
    context.user_data["cart"] = {}
    context.user_data["awaiting_phone"] = False
    context.user_data["phone_number"] = None
    await update.message.reply_text(
        text="✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Asosiy menyu", callback_data="back_to_start")]
        ])
    )

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
    await query.edit_message_text(
        "Yangi kategoriya nomini yuboring (masalan: 'Shirinliklar 🍰'):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bekor qilish", callback_data="admin_panel")]
        ])
    )
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

async def admin_view_items(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    category = menu_db["categories"][cat_id]
    
    if not category["items"]:
        await query.edit_message_text(
            text=f"Kategoriyada hech qanday mahsulot yo'q: {category['name']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Mahsulot qo'shish", callback_data=f"admin_add_item_{cat_id}")],
                [InlineKeyboardButton("Ortga 🔙", callback_data=f"admin_edit_category_{cat_id}")]
            ])
        )
        return
    
    items_text = f"Mahsulotlar ({category['name']}):\n\n"
    keyboard = []
    for item_id, item in category["items"].items():
        items_text += f"- {item['name']} - {item['price']} UZS\n"
        keyboard.append([InlineKeyboardButton(f"Tahrirlash: {item['name']}", callback_data=f"admin_edit_item_{cat_id}_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("Ortga 🔙", callback_data=f"admin_edit_category_{cat_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=items_text, reply_markup=reply_markup)

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
    await query.edit_message_text(
        f"Yangi mahsulot nomini yuboring (masalan: 'Pepsi'):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{cat_id}")]
        ])
    )

async def admin_change_category_name(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    context.user_data["admin_action"] = "awaiting_new_category_name"
    context.user_data["current_category"] = cat_id
    await query.edit_message_text(
        f"Joriy nom: {menu_db['categories'][cat_id]['name']}\nYangi nomni yuboring:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{cat_id}")]
        ])
    )

async def admin_change_category_image(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    context.user_data["admin_action"] = "awaiting_new_category_image"
    context.user_data["current_category"] = cat_id
    await query.edit_message_text(
        "Yangi rasmni yuboring:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{cat_id}")]
        ])
    )

async def admin_delete_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[-1]
    del menu_db["categories"][cat_id]
    await query.edit_message_text(
        f"Kategoriya o'chirildi!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ortga 🔙", callback_data="admin_view_categories")]
        ])
    )

async def admin_handle_messages(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id) and not context.user_data.get("awaiting_phone"):
        return
    
    if context.user_data.get("awaiting_phone"):
        phone_number = update.message.text.strip()
        # Basic phone number validation
        if not phone_number.startswith("+") or not phone_number[1:].isdigit():
            await update.message.reply_text(
                "❌ Noto'g'ri telefon raqami! Iltimos, to'g'ri formatda yuboring (masalan: +998901234567):",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Bekor qilish", callback_data="view_cart")]
                ])
            )
            return
        
        context.user_data["phone_number"] = phone_number
        await place_order(update, context)
        return
    
    action = context.user_data.get("admin_action")
    
    if action == "awaiting_category_name":
        category_name = update.message.text
        # Create a safe ID from the category name
        cat_id = category_name.lower().replace(" ", "_").replace("'", "").replace("🍰", "").replace("🥤", "").replace("🍽️", "").strip("_")
        
        menu_db["categories"][cat_id] = {
            "name": category_name,
            "image": None,
            "items": {}
        }
        
        await update.message.reply_text(
            f"✅ Kategoriya '{category_name}' qo'shildi!\n\nEndi kategoriya uchun rasm yuboring:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Rasmni o'tkazib yuborish", callback_data="admin_panel")],
                [InlineKeyboardButton("Bekor qilish", callback_data="admin_panel")]
            ])
        )
        context.user_data["admin_action"] = "awaiting_category_image"
        context.user_data["current_category"] = cat_id
    
    elif action == "awaiting_category_image":
        if update.message.photo:
            try:
                cat_id = context.user_data["current_category"]
                photo_file = await update.message.photo[-1].get_file()
                
                # Create a unique filename
                file_extension = photo_file.file_path.split('.')[-1] if '.' in photo_file.file_path else 'jpg'
                local_filename = f"images/category_{cat_id}.{file_extension}"
                
                # Download the file
                await photo_file.download_to_drive(local_filename)
                
                # Save the local path to database
                menu_db["categories"][cat_id]["image"] = local_filename
                
                await update.message.reply_text(
                    "✅ Kategoriya rasmi muvaffaqiyatli saqlandi!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Admin Panel", callback_data="admin_panel")]
                    ])
                )
                
                # Clear the admin action
                context.user_data["admin_action"] = None
                context.user_data["current_category"] = None
                
            except Exception as e:
                logger.error(f"Error saving category image: {e}")
                await update.message.reply_text(
                    "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Admin Panel", callback_data="admin_panel")]
                    ])
                )
        else:
            await update.message.reply_text(
                "❌ Iltimos, rasm yuboring yoki 'Rasmni o'tkazib yuborish' tugmasini bosing!"
            )
    
    elif action == "awaiting_item_name":
        item_name = update.message.text
        context.user_data["item_name"] = item_name
        context.user_data["admin_action"] = "awaiting_item_price"
        await update.message.reply_text(
            f"Mahsulot '{item_name}' uchun narxini yuboring (masalan: 15000):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{context.user_data['current_category']}")]
            ])
        )
    
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
                f"✅ Mahsulot '{item_name}' qo'shildi!\n\nEndi mahsulot uchun rasm yuboring:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Rasmni o'tkazib yuborish", callback_data=f"admin_edit_category_{cat_id}")],
                    [InlineKeyboardButton("Bekor qilish", callback_data=f"admin_edit_category_{cat_id}")]
                ])
            )
            context.user_data["admin_action"] = "awaiting_item_image"
            context.user_data["current_item"] = item_id
        
        except ValueError:
            await update.message.reply_text(
                "❌ Noto'g'ri format! Faqat raqam kiriting (masalan: 15000)"
            )
    
    elif action == "awaiting_item_image":
        if update.message.photo:
            try:
                cat_id = context.user_data["current_category"]
                item_id = context.user_data["current_item"]
                photo_file = await update.message.photo[-1].get_file()
                
                # Create a unique filename
                file_extension = photo_file.file_path.split('.')[-1] if '.' in photo_file.file_path else 'jpg'
                local_filename = f"images/item_{cat_id}_{item_id}.{file_extension}"
                
                # Download the file
                await photo_file.download_to_drive(local_filename)
                
                # Save the local path to database
                menu_db["categories"][cat_id]["items"][item_id]["image"] = local_filename
                
                await update.message.reply_text(
                    "✅ Mahsulot rasmi muvaffaqiyatli saqlandi!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Kategoriyaga qaytish", callback_data=f"admin_edit_category_{cat_id}")],
                        [InlineKeyboardButton("Admin Panel", callback_data="admin_panel")]
                    ])
                )
                
                # Clear the admin action
                context.user_data["admin_action"] = None
                context.user_data["current_category"] = None
                context.user_data["current_item"] = None
                
            except Exception as e:
                logger.error(f"Error saving item image: {e}")
                await update.message.reply_text(
                    "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Kategoriyaga qaytish", callback_data=f"admin_edit_category_{context.user_data['current_category']}")]
                    ])
                )
        else:
            await update.message.reply_text(
                "❌ Iltimos, rasm yuboring yoki 'Rasmni o'tkazib yuborish' tugmasini bosing!"
            )
    
    elif action == "awaiting_new_category_name":
        new_name = update.message.text
        cat_id = context.user_data["current_category"]
        menu_db["categories"][cat_id]["name"] = new_name
        context.user_data["admin_action"] = None
        context.user_data["current_category"] = None
        await update.message.reply_text(
            f"✅ Kategoriya nomi muvaffaqiyatli o'zgartirildi: {new_name}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ortga 🔙", callback_data=f"admin_edit_category_{cat_id}")]
            ])
        )
    
    elif action == "awaiting_new_category_image":
        if update.message.photo:
            try:
                cat_id = context.user_data["current_category"]
                photo_file = await update.message.photo[-1].get_file()
                
                file_extension = photo_file.file_path.split('.')[-1] if '.' in photo_file.file_path else 'jpg'
                local_filename = f"images/category_{cat_id}.{file_extension}"
                
                await photo_file.download_to_drive(local_filename)
                menu_db["categories"][cat_id]["image"] = local_filename
                
                await update.message.reply_text(
                    "✅ Kategoriya rasmi muvaffaqiyatli o'zgartirildi!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Ortga 🔙", callback_data=f"admin_edit_category_{cat_id}")]
                    ])
                )
                context.user_data["admin_action"] = None
                context.user_data["current_category"] = None
            except Exception as e:
                logger.error(f"Error saving category image: {e}")
                await update.message.reply_text(
                    "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Ortga 🔙", callback_data=f"admin_edit_category_{cat_id}")]
                    ])
                )
        else:
            await update.message.reply_text(
                "❌ Iltimos, rasm yuboring!"
            )

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
    application.add_handler(CallbackQueryHandler(request_phone, pattern="request_phone"))
    
    # Admin commands
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="admin_panel"))
    application.add_handler(CallbackQueryHandler(admin_add_category, pattern="admin_add_category"))
    application.add_handler(CallbackQueryHandler(admin_view_categories, pattern="admin_view_categories"))
    application.add_handler(CallbackQueryHandler(admin_edit_category, pattern="admin_edit_category_"))
    application.add_handler(CallbackQueryHandler(admin_view_items, pattern="admin_view_items_"))
    application.add_handler(CallbackQueryHandler(admin_add_item_select_category, pattern="admin_add_item_select_category"))
    application.add_handler(CallbackQueryHandler(admin_add_item, pattern="admin_add_item_"))
    application.add_handler(CallbackQueryHandler(admin_change_category_name, pattern="admin_change_category_name_"))
    application.add_handler(CallbackQueryHandler(admin_change_category_image, pattern="admin_change_category_image_"))
    application.add_handler(CallbackQueryHandler(admin_delete_category, pattern="admin_delete_category_"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, admin_handle_messages))
    
    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()