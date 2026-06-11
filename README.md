# ☕ BeanBuddy

A cloud-native conversational ordering agent for a coffee shop. Customers chat
naturally — *"show me the menu"*, *"add a large latte"*, *"track order #12"* —
and a Dialogflow ES agent forwards each intent to this FastAPI webhook, which
manages the cart and orders in a MySQL database.

## Architecture

```
Customer ──► Dialogflow ES ──► FastAPI webhook (this repo) ──► MySQL (AWS RDS)
              (NLU/intents)        deployed on AWS EC2
```

- **Dialogflow ES** handles natural-language understanding and intent matching.
- **FastAPI** exposes a single fulfillment webhook that routes each intent to the
  right handler.
- **MySQL (AWS RDS)** persists the menu, in-progress carts, and completed orders.
- **AWS EC2** hosts the webhook in production.

## Features

- 📋 Show the menu
- ➕ Add items to an order (with size-based pricing)
- ➖ Remove items from an order
- ✅ Complete an order and receive an order ID
- 🔎 Track an order by its ID

## Supported intents

| Intent           | Action                                      |
| ---------------- | ------------------------------------------- |
| `menu.show`      | Returns the formatted menu                  |
| `order.add`      | Adds a coffee (type + size) to the cart     |
| `order.remove`   | Removes a coffee from the cart              |
| `order.complete` | Finalizes the order and returns an order ID |
| `order.track`    | Returns the status of an order by ID        |

## Getting started

### Prerequisites

- Python 3.11+
- A MySQL database (local, or AWS RDS)

### Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your database credentials
cp .env.example .env           # then edit .env with your values

# 4. Create the tables and seed the menu
python db_helper.py

# 5. Run the webhook
uvicorn main:app --reload
```

The webhook listens on `http://127.0.0.1:8000/`. Point your Dialogflow ES agent's
fulfillment URL at this endpoint (use a tunnel such as ngrok during local
development, or your EC2 public URL in production).

## Configuration

All configuration is read from environment variables (see `.env.example`):

| Variable  | Description                  |
| --------- | ---------------------------- |
| `DB_HOST` | MySQL host                   |
| `DB_USER` | MySQL username               |
| `DB_PASS` | MySQL password               |
| `DB_NAME` | Database name (`beanbuddy`)  |

## Tech stack

FastAPI · Dialogflow ES · MySQL · AWS RDS · AWS EC2 · Uvicorn
