import time
import requests
import telebot
import logging
from datetime import datetime


BOT_TOKEN = "BOT_TOKEN"
CHAT_ID = "CHAT_ID"


GENDER = "Men"

URL = f"https://www.sheinindia.in/api/category/sverse-5939-37961?fields=SITE&currentPage=0&pageSize=40&format=json&query=%3Arelevance%3Agenderfilter%3A{GENDER}&sortBy=relevance&gridColumns=2&facets=genderfilter%3A{GENDER}&includeUnratedProducts=false&segmentIds=&advfilter=true&platform=Msite&showAdsOnNextPage=false&is_ads_enable_plp=true&displayRatings=true&&store=shein"

CHECK_INTERVAL_SECONDS = 20 


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


bot = telebot.TeleBot(BOT_TOKEN)


def get_product_count():
    try:
        resp = requests.get(URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
        count = len(products)
        return count
    except Exception as e:
        logger.error(f"Error fetching product count: {e}", exc_info=True)
        return None


def send_alert(new_count, old_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"📦 Stock Alert!\n"
        f"Gender: {GENDER}\n"
        f"➡️ Product count increased: {old_count} → {new_count}\n"
        f"Check it now!\nhttps://www.sheinindia.in/c/sverse-5939-37961"
    )
    try:
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}", exc_info=True)


def main_loop():
    last_count = None
    
    while last_count is None:
        last_count = get_product_count()
        if last_count is None:
            logger.info("Initial fetch failed — retrying in 30 seconds…")
            time.sleep(30)
    logger.info(f"Bot started. Initial product count = {last_count}")

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        count = get_product_count()
        if count is None:
            logger.warning("Fetch failed this cycle — continuing.")
            continue
        
        if count > last_count:
            logger.info(f"Stock ↑ {last_count} → {count}") 
            send_alert(count, last_count)
        
        last_count = count

if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        while True:
            time.sleep(60)

