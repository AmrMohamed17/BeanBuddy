from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper

app = FastAPI()

@app.post("/")
async def handle_request(request: Request):
    # 1. Retrieve the JSON data from Dialogflow
    payload = await request.json()
    
    # 2. Extract key information
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    
    # Extract the session ID (e.g., "projects/agent-id/sessions/unique-id")
    # This identifies the specific user chatting with the bot
    session_id = payload['session']

    # --- INTENT HANDLER ---

    # 1. SHOW MENU
    if intent == "menu.show":
        menu_text = db_helper.get_formatted_menu()
        return JSONResponse(content={
            "fulfillmentText": menu_text
        })

    # 2. ADD ITEM TO ORDER
    elif intent == "order.add":
        item = parameters['coffee-type']
        size = parameters['coffee-size']
        
        # We default quantity to 1 for now
        result = db_helper.add_item_to_order(session_id, item, size, 1)
        
        if result == -1:
            fulfillment_text = f"Sorry, I couldn't find {item} in our menu."
        else:
            # Show the user what they have so far
            current_order_str = db_helper.get_current_order_items(session_id)
            fulfillment_text = f"Added {size} {item} to your order.\n{current_order_str}\nDo you want anything else?"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    # 3. REMOVE ITEM FROM ORDER
    elif intent == "order.remove":
        item = parameters['coffee-type']
        
        result = db_helper.remove_item_from_order(session_id, item)
        
        if result == -1:
            fulfillment_text = "You don't have an active order to remove items from."
        elif result == 0:
            fulfillment_text = f"I couldn't find {item} in your cart. You have:\n{db_helper.get_current_order_items(session_id)}"
        else:
            current_order_str = db_helper.get_current_order_items(session_id)
            fulfillment_text = f"Removed {item} from your order.\n{current_order_str}"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    # 4. COMPLETE ORDER
    elif intent == "order.complete":
        order_details = db_helper.complete_order(session_id)
        
        if order_details is None:
            fulfillment_text = "You don't have any active order to complete. Would you like to check the menu?"
        else:
            order_id, total_amount = order_details
            fulfillment_text = f"Awesome! Your order is placed. Your Order ID is #{order_id}. Your total is ${total_amount}. You can use this ID to track your order later."

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    # 5. TRACK ORDER
    elif intent == "order.track":
        # Check if Dialogflow sent 'order_id' or 'number' (depends on your parameter naming)
        order_id = parameters.get('order_id') or parameters.get('number')
        
        if order_id:
            status = db_helper.get_order_status(int(order_id))
            
            if status:
                fulfillment_text = f"The status of order #{int(order_id)} is: {status}"
            else:
                fulfillment_text = f"I couldn't find an order with ID #{int(order_id)}."
        else:
            fulfillment_text = "Please specify an order ID to track."

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    # Default Fallback
    return JSONResponse(content={
        "fulfillmentText": "I received your request, but my backend doesn't know how to handle this intent."
    })