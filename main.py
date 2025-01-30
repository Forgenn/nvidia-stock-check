import asyncio
from playwright.async_api import async_playwright
from win10toast import ToastNotifier
import logging
import signal
from telegram.ext import Application
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

class StockChecker:
    def __init__(self, wanted_product: str, headless: str = False):
        self.running = True
        self.url = "https://marketplace.nvidia.com/es-es/consumer/graphics-cards/"
        self.params = {
            'locale': 'es-es',
            'page': '1',
            'limit': '12',
            'category': 'GPU',
            'gpu': 'RTX 5080'
        }
        self.toaster = ToastNotifier()
        self.browser = None
        self.page = None
        self.headless = headless
        # Telegram bot
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Application.builder().token(self.bot_token).build()
        # Config
        self.wanted_product = wanted_product.lower()
        

    async def setup(self):
        logging.info(f"Initializing stock checker for {self.url}")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        self.running = False

    async def check_stock(self):
        try:
            # Construct URL with parameters
            params_str = '&'.join(f"{k}={quote_plus(str(v))}" for k, v in self.params.items())
            self.url = f"{self.url}?{params_str}"
            await self.page.goto(self.url)
            await page.screenshot({path: "test.png", fullPage: true});
            # Wait for products to load
            await self.page.wait_for_selector('#resultsDiv')
            
            products = await self.page.query_selector_all(
                '#resultsDiv > div'
            )
#resultsDiv > div > div > div:nth-child(2) > h2
            for product in products:
                real_prod = await product.query_selector('div:nth-child(2) > h2')
                price = await product.query_selector('div:nth-child(2) > div.product_detail_78.nv-priceAndCTAContainer')
                price = await price.get_attribute('data-price')
                alt = await real_prod.get_attribute('data-producttitle')
                if self.wanted_product in (alt.lower() or ''):
                    status = await real_prod.get_attribute('data-ctatype')
                    if status and status == 'out_of_stock':
                        await self.notify_stock_available(alt)
                        return True

            return False

        except Exception as e:
            logging.error(f"Error checking stock: {str(e)}")
            return False

    async def notify_stock_available(self, name: str):
        try:
            message = f"🎮 {self.wanted_product} available!\nModel: {name}\nURL: {self.url}"
            logging.info(message)
            
            out = await self.bot.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Error in notification: {str(e)}")

async def main():
    checker = StockChecker("NVIDIA GeForce RTX 5080", headless=False)
    await checker.setup()
    
    try:
        while checker.running:
            if await checker.check_stock():
                print("Stock found! Check notification.")
            else:
                print("No stock available. Checking again in 5 minutes...")
            await asyncio.sleep(300)
    finally:
        await checker.cleanup()

if __name__ == "__main__":
    asyncio.run(main())