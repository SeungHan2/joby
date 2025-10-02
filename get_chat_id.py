from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8379079791:AAFYysLmNqZ5caivlqrMZOMbS9f6X4_PQOI"

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"Chat ID: {chat_id}")  # 터미널 출력
    await update.message.reply_text(f"당신의 chat_id는 {chat_id} 입니다!")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 모든 텍스트 메시지에 반응
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_id))

print("봇 실행 중입니다. 봇에게 메시지를 보내보세요.")
app.run_polling()
