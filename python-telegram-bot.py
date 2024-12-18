import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import random
import string

# Токен вашего бота
TOKEN = '8016473336:AAFA6ETe4LwK2vd8H4KiWVHWeL59IJJfEk8'

# Устанавливаем соединение с Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Открываем таблицу
sheet = client.open("TransactionData").sheet1

# Определяем состояния для ConversationHandler
ADDRESS, SENDER_NAME, RECIPIENT_NAME, RECIPIENT_PHONE, DELIVERY_METHOD, TRANSACTION_AMOUNT = range(6)

# Функция начала работы
async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Создать транзакцию", callback_data='create_transaction')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать! Нажмите кнопку для создания транзакции:', reply_markup=reply_markup)
    return ADDRESS

# Функция для создания транзакции
async def create_transaction(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Ввести данные", callback_data='enter_data')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Пожалуйста, введите данные транзакции:', reply_markup=reply_markup)
    return ADDRESS

# Функция для ввода данных
async def enter_data(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Введите адрес отправителя (Израиль):')
    return ADDRESS

# Функция обработки введенных данных
async def handle_address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    await update.message.reply_text('Введите имя отправителя:')
    return SENDER_NAME

async def handle_sender_name(update: Update, context: CallbackContext) -> int:
    context.user_data['sender_name'] = update.message.text
    await update.message.reply_text('Введите имя получателя:')
    return RECIPIENT_NAME

async def handle_recipient_name(update: Update, context: CallbackContext) -> int:
    context.user_data['recipient_name'] = update.message.text
    await update.message.reply_text('Введите номер телефона получателя:')
    return RECIPIENT_PHONE

async def handle_recipient_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['recipient_phone'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Доставка", callback_data='delivery')],
        [InlineKeyboardButton("Сам получатель", callback_data='pickup')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите метод доставки:', reply_markup=reply_markup)
    return DELIVERY_METHOD

# Функция для выбора метода доставки
async def handle_delivery(update: Update, context: CallbackContext) -> int:
    context.user_data['delivery_method'] = 'Delivery' if update.callback_query.data == 'delivery' else 'Pickup'
    await update.callback_query.answer()
    await update.callback_query.edit_message_text('Введите сумму транзакции в долларах:')
    return TRANSACTION_AMOUNT

async def handle_transaction_amount(update: Update, context: CallbackContext) -> int:
    context.user_data['transaction_amount'] = update.message.text
    
    # Генерация уникального кода
    unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    context.user_data['unique_code'] = unique_code
    
    # Добавление данных в Google Sheets
    sheet.append_row([context.user_data['address'], context.user_data['sender_name'], context.user_data['recipient_name'], 
                      context.user_data['recipient_phone'], context.user_data['delivery_method'], 
                      context.user_data['transaction_amount'], unique_code])
    
    # Отправка уникального кода пользователю
    await update.message.reply_text(f'Транзакция успешно отправлена. Ваш уникальный код: {unique_code}')
    return ConversationHandler.END

# Основная функция
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Создайте ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(create_transaction, pattern='create_transaction')],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)],
            SENDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sender_name)],
            RECIPIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recipient_name)],
            RECIPIENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recipient_phone)],
            DELIVERY_METHOD: [CallbackQueryHandler(handle_delivery, pattern='delivery|pickup')],
            TRANSACTION_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction_amount)],
        },
        fallbacks=[],
    )

    # Добавьте обработчик для начала общения с ботом
    application.add_handler(conversation_handler)

    # Запустите бота
    application.run_polling()

if __name__ == '__main__':
    main()
