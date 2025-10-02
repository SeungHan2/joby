import yfinance as yf
from telegram import Bot

TOKEN = "텔레그램 봇 토큰"
CHAT_ID = "텔레그램 채팅 ID"
bot = Bot(TOKEN)

sp500 = yf.Ticker("^GSPC")
price = sp500.history(period="1d")['Close'][0]

bot.send_message(chat_id=CHAT_ID, text=f"오늘 S&P500 종가: {price:.2f}")
