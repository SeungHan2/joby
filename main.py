import json
import yfinance as yf
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# -------------------
# 텔레그램 봇 설정
# -------------------
TELEGRAM_TOKEN = "8379079791:AAFYysLmNqZ5caivlqrMZOMbS9f6X4_PQOI"
CHAT_ID = "1898196235"

# -------------------
# 포트폴리오 데이터 파일
# -------------------
PORTFOLIO_FILE = "portfolio.json"

# -------------------
# Conversation 상태
# -------------------
TICKER, QTY, AVG_PRICE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("등록할 티커를 입력해주세요 (예: AAPL)")
    return TICKER

async def ticker_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ticker'] = update.message.text.upper()
    await update.message.reply_text(f"{context.user_data['ticker']} 보유 수량을 입력해주세요")
    return QTY

async def qty_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['qty'] = float(update.message.text)
    await update.message.reply_text(f"{context.user_data['ticker']} 매수단가를 입력해주세요")
    return AVG_PRICE

async def avg_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['avg_price'] = float(update.message.text)
    
    # JSON에 저장
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            portfolio = json.load(f)
    except FileNotFoundError:
        portfolio = {}
        
    t = context.user_data['ticker']
    portfolio[t] = {
        "qty": context.user_data['qty'],
        "avg_price": context.user_data['avg_price']
    }
    
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)
    
    await update.message.reply_text(f"{t} 등록 완료!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("등록 취소되었습니다.")
    return ConversationHandler.END

# -------------------
# 아침 리포트 함수
# -------------------
async def send_daily_report(application):
    from telegram import Bot
    bot: Bot = application.bot
    
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            portfolio = json.load(f)
    except FileNotFoundError:
        await bot.send_message(chat_id=CHAT_ID, text="등록된 포트폴리오가 없습니다.")
        return
    
    # 오늘/어제 주가 조회
    messages_change = []
    total_delta = 0
    current_values = {}
    yesterday_values = {}
    
    for t, info in portfolio.items():
        stock = yf.Ticker(t)
        hist = stock.history(period="2d")
        if len(hist) < 2:
            continue
        
        today_close = hist['Close'][-1]
        yesterday_close = hist['Close'][-2]
        qty = info['qty']
        avg_price = info['avg_price']
        
        pct_change = (today_close - yesterday_close) / yesterday_close * 100
        messages_change.append(f"{t}: {pct_change:+.2f}%")
        
        total_delta += (today_close - avg_price) * qty
        current_values[t] = today_close * qty
        yesterday_values[t] = yesterday_close * qty
    
    msg1 = "오늘의 미국 주식 변동률:\n" + "\n".join(messages_change)
    msg2 = f"총 보유 자산 변동액: {total_delta:+.2f}$"
    
    total_today = sum(current_values.values())
    total_yesterday = sum(yesterday_values.values())
    msg3_lines = []
    for t in portfolio.keys():
        pct_today = current_values[t] / total_today * 100 if total_today else 0
        pct_yesterday = yesterday_values[t] / total_yesterday * 100 if total_yesterday else 0
        msg3_lines.append(f"{t}: {pct_today:.0f}% (어제: {pct_yesterday:.0f}%)")
    msg3 = "총 자산 비중:\n" + "\n".join(msg3_lines)
    
    await bot.send_message(chat_id=CHAT_ID, text=msg1)
    await bot.send_message(chat_id=CHAT_ID, text=msg2)
    await bot.send_message(chat_id=CHAT_ID, text=msg3)
    print("아침 리포트 발송 완료!")

# -------------------
# 봇 실행
# -------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TICKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ticker_input)],
            QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty_input)],
            AVG_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_price_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    
    # 봇 실행
    app.run_polling()

if __name__ == "__main__":
    main()
