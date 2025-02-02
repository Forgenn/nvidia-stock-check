import os
import logging
import asyncio
import requests
from requests.adapters import HTTPAdapter, Retry
from signal import SIGTERM, SIGINT
from telegram import Bot
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

load_dotenv()

class NvidiaStockChecker:
    def __init__(self, sku: str, locale: str = 'es-es'):
        self.running = True
        self.stop_event = asyncio.Event()
        self.api_url = "https://api.store.nvidia.com/partner/v1/feinventory"
        self.sku = sku
        self.locale = locale
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        # Telegram setup
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        request = HTTPXRequest(connection_pool_size=8)
        self.bot = Bot(token=self.bot_token, request=request)

    async def _send_message(self, text: str):
        """Generic message sending method with retry"""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")

    async def notify_stock_available(self, price):
        await self._send_message(f"🎮 {self.sku} available!\nPrice: {price}€")

    async def notify_error(self, error_msg: str):
        await self._send_message(f"❌ Error checking {self.sku}:\n{error_msg}")

    async def check_stock(self):
        try:
            params = {
                'status': '1',
                'skus': self.sku,
                'locale': self.locale
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                'Accept': 'application/json'
            }
            
            response = self.session.get(
                self.api_url, 
                params=params, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            logging.debug(f"Response: {data}")

            if data.get('success') and data.get('listMap'):
                product = data['listMap'][0]
                is_active = product.get('is_active') == 'true'
                price = product.get('price')
                
                if is_active:
                    await self.notify_stock_available(price)
                    return True
            return False
                
        except Exception as e:
            logging.error(f"Error checking stock: {str(e)}")
            await self.notify_error(str(e))
            return False

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.session.close()

async def main():
    # Configuration
    check_interval = int(os.getenv('STOCK_CHECK_INTERVAL', 300))
    sku = os.getenv('NVIDIA_SKU', 'NVGFT580')
    locale = os.getenv('NVIDIA_LOCALE', 'es-es')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    # Setup logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Starting NvidiaStockChecker with configuration: "
                 f"SKU={sku}, Locale={locale}, Check Interval={check_interval}s, Log Level={log_level}")

    checker = NvidiaStockChecker(sku=sku, locale=locale)

    # Setup signal handling
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        shutdown_event.set()

    for sig in (SIGINT, SIGTERM):
       loop.add_signal_handler(sig, signal_handler)

    try:
        while not shutdown_event.is_set():
            stock_found = await checker.check_stock()
            if stock_found:
                logging.info("Stock found! Notification sent.")
            else:
                logging.info(f"No stock available. Checking again in {check_interval}s...")
            
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=check_interval)
            except asyncio.TimeoutError:
                pass  # Normal interval timeout, continue checking
                
    except Exception as e:
        logging.error(f"Critical error: {str(e)}", exc_info=True)
        await checker.notify_error(f"Critical error: {str(e)}")
    finally:
        checker.stop()
        logging.info("Stock checker stopped gracefully.")

if __name__ == "__main__":
    asyncio.run(main())