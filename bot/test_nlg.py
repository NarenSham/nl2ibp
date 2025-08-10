import sys
import os

# Ensure imports work when running from bot folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.nlg import generate_nlg

# Example structured output from solve_routing
sample_result = {
    "status": "Optimal",
    "total_cost": 30.5,
    "assignments": [
        {
            "warehouse_id": 1,
            "warehouse_name": "Warehouse A",
            "retailer_id": 1,
            "retailer_name": "Retailer X",
            "cost": 12.0
        },
        {
            "warehouse_id": 2,
            "warehouse_name": "Warehouse B",
            "retailer_id": 2,
            "retailer_name": "Retailer Y",
            "cost": 18.5
        }
    ]
}

if __name__ == "__main__":
    # Call NLG function directly
    friendly_text = generate_nlg(sample_result)
    print("Generated NLG Output:", repr(friendly_text))
    print(friendly_text)
