import json
import yfinance as yf
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# -------------------
# 텔레그램 봇 설정
# -------------------
TELEGRAM_TOKEN = "여기에_봇_토큰_입력"
CHAT_ID = "여기에_사용자_채팅ID"
bot = Bot(token=TELEGRAM_TOKEN)

# -------------------
# 포트폴리오 데이터 파일
# -------------------
PORTFOLIO_FILE = "portfolio.json"

# -------------------
# Conversation 상태
# -------------------
TICKER, QTY, AVG_PRICE = range(3)

def start(update, context):
    update.message.reply_text("등록할 티커를 입력해주세요 (예: AAPL)")
    return TICKER

def ticker_input(update, context):
    context.user_data['ticker'] = update.message.text.upper()
    update.message.reply_text(f"{context.user_data['ticker']} 보유 수량을 입력해주세요")
    return QTY

def qty_input(update, context):
    context.user_data['qty'] = float(update.message.text)
    update.message.reply_text(f"{context.user_data['ticker']} 매수단가를 입력해주세요")
    return AVG_PRICE

def avg_price_input(update, context):
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
    
    update.message.reply_text(f"{t} 등록 완료!")
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("등록 취소되었습니다.")
    return ConversationHandler.END

# -------------------
# 아침 리포트 함수
# -------------------
def send_daily_report():
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            portfolio = json.load(f)
    except FileNotFoundError:
        bot.send_message(chat_id=CHAT_ID, text="등록된 포트폴리오가 없습니다.")
        return
    
    # 오늘/어제 주가 조회
    messages_change = []
    total_delta = 0
    current_values = {}
    yesterday_values = {}
    
    for t, info in portfolio.items():
        stock = yf.Ticker(t)
        hist = stock.history(period="2d")  # 최근 2일
        
        if len(hist) < 2:
            continue
        
        today_close = hist['Close'][-1]
        yesterday_close = hist['Close'][-2]
        qty = info['qty']
        avg_price = info['avg_price']
        
        # 1️⃣ 오늘 변동률
        pct_change = (today_close - yesterday_close) / yesterday_close * 100
        messages_change.append(f"{t}: {pct_change:+.2f}%")
        
        # 2️⃣ 총 변동액 계산
        total_delta += (today_close - avg_price) * qty
        
        # 3️⃣ 자산 비중
        current_values[t] = today_close * qty
        yesterday_values[t] = yesterday_close * qty
    
    # 1️⃣ 메시지
    msg1 = "오늘의 미국 주식 변동률:\n" + "\n".join(messages_change)
    
    # 2️⃣ 메시지
    msg2 = f"총 보유 자산 변동액: {total_delta:+.2f}$"
    
    # 3️⃣ 메시지 (오늘 비중 / 어제 비중)
    total_today = sum(current_values.values())
    total_yesterday = sum(yesterday_values.values())
    msg3_lines = []
    for t in portfolio.keys():
        pct_today = current_values[t] / total_today * 100 if total_today else 0
        pct_yesterday = yesterday_values[t] / total_yesterday * 100 if total_yesterday else 0
        msg3_lines.append(f"{t}: {pct_today:.0f}% (어제: {pct_yesterday:.0f}%)")
    msg3 = "총 자산 비중:\n" + "\n".join(msg3_lines)
    
    # 텔레그램 전송
    bot.send_message(chat_id=CHAT_ID, text=msg1)
    bot.send_message(chat_id=CHAT_ID, text=msg2)
    bot.send_message(chat_id=CHAT_ID, text=msg3)
    print("아침 리포트 발송 완료!")

# -------------------
# 봇 실행
# -------------------
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TICKER: [MessageHandler(Filters.text & ~Filters.command, ticker_input)],
            QTY: [MessageHandler(Filters.text & ~Filters.command, qty_input)],
            AVG_PRICE: [MessageHandler(Filters.text & ~Filters.command, avg_price_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


