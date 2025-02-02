# Nvidia Stock Checker

This application periodically checks the stock availability of Nvidia GPUs and sends notifications via Telegram when stock is available.

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-telegram-chat-id>
NVIDIA_SKU=<nvidia-sku-to-check>
NVIDIA_LOCALE=<locale-code>
STOCK_CHECK_INTERVAL=<interval-in-seconds>
LOG_LEVEL=<log-level>
```

Example `.env` file:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
NVIDIA_SKU=NVGFT580
NVIDIA_LOCALE=es-es
STOCK_CHECK_INTERVAL=300
LOG_LEVEL=INFO
```

For info on how to setup a telegram bot, go [here](https://core.telegram.org/bots/features#botfather).

## Running the Application

### Using Docker

1. Build the Docker image:

    ```sh
    docker build -t nvidia-stock-checker .
    ```

2. Run the Docker container:

    ```sh
    docker run --env-file .env nvidia-stock-checker
    ```

### Using Docker Compose

1. Start the application:

    ```sh
    docker-compose up -d
    ```

### Running Locally

1. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

2. Run the application:

    ```sh
    python main.py
    ```