# nlg.py

def generate_nlg(result, intent=None):
    """
    Generate a human-readable summary (NLG) string based on the result data and intent.

    Args:
        result (dict or list or str): The raw structured data returned from the query.
        intent (str, optional): The intent type to tailor the summary.

    Returns:
        str: A natural language summary of the result.
    """

    if isinstance(result, str):
        # If the result is already a string (like an error or message), just return it
        return result

    if intent == "list_warehouses":
        if isinstance(result, list) and result:
            names = [w.get("name", "Unknown") for w in result]
            return f"Warehouses: {', '.join(names)}."
        else:
            return "No warehouses found."

    elif intent == "list_retailers":
        if isinstance(result, list) and result:
            names = [r.get("name", "Unknown") for r in result]
            return f"Retailers: {', '.join(names)}."
        else:
            return "No retailers found."

    elif intent == "find_routes":
        if isinstance(result, list) and result:
            sample = result[:3]  # Show up to 3 routes
            assignments = []
            for r in sample:
                wh_id = r.get("warehouse_id", "N/A")
                rt_id = r.get("retailer_id", "N/A")
                cost = r.get("cost", "N/A")
                assignments.append(f"WH_{wh_id} -> RT_{rt_id} (cost ${cost})")
            return f"Found {len(result)} routes. Sample assignments: {', '.join(assignments)}."
        else:
            return "No routes found."

    elif intent == "calculate_demand":
        if isinstance(result, dict) and result.get("warehouse"):
            warehouse = result.get("warehouse")
            total_demand = result.get("total_demand", "unknown")
            nearby_count = result.get("nearby_retailers", "unknown")
            return (f"Total demand near warehouse '{warehouse}' is {total_demand} "
                    f"from {nearby_count} nearby retailers.")
        else:
            return "Demand data not available."

    elif intent == "what_if":
        if isinstance(result, dict):
            status = result.get("status", "Unknown")
            assignments = result.get("assignments", [])
            if assignments:
                sample = assignments[:3]
                assign_strs = []
                for a in sample:
                    wh = a.get("warehouse_id", "N/A")
                    rt = a.get("retailer_id", "N/A")
                    cost = a.get("cost", "N/A")
                    assign_strs.append(f"WH_{wh} -> RT_{rt} (cost ${cost})")
                return (f"What-if scenario completed with status '{status}'. "
                        f"Sample assignments: {', '.join(assign_strs)}.")
            else:
                return f"What-if scenario completed with status '{status}'. No assignments found."
        else:
            return "No what-if data found."

    else:
        # Fallback summary
        return "Here is the result of your query."
