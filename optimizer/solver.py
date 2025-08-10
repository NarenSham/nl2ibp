import sqlite3
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpStatus

DB_PATH = "db/optiguide.db"

def get_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    warehouses = cursor.execute("SELECT id, name FROM warehouses").fetchall()
    retailers = cursor.execute("SELECT id, name, demand FROM retailers").fetchall()
    routes = cursor.execute("SELECT warehouse_id, retailer_id, cost FROM routes").fetchall()

    conn.close()
    return warehouses, retailers, routes


def solve_routing(constraints=None):
    """
    Solve routing problem with flexible constraints list.
    Example constraints:
    [
        {"type": "exclude_warehouse", "warehouse": "W1"},
        {"type": "max_cost", "value": 500},
        {"type": "min_inventory", "warehouse": "W2", "value": 50}
    ]
    """
    constraints = constraints or []
    warehouses, retailers, routes = get_data()

    # ---------------------------
    # 1. Apply "exclude_warehouse"
    # ---------------------------
    unavailable_ids = []
    for c in constraints:
        if c["type"] == "exclude_warehouse":
            # Find matching warehouse id by name/code
            match = next((w[0] for w in warehouses if w[1].lower() == c["warehouse"].lower()), None)
            if match:
                unavailable_ids.append(match)

    warehouses = [w for w in warehouses if w[0] not in unavailable_ids]

    # ---------------------------
    # 2. Apply "max_cost"
    # ---------------------------
    max_cost = None
    for c in constraints:
        if c["type"] == "max_cost":
            max_cost = c["value"]

    # ---------------------------
    # Prepare model sets
    # ---------------------------
    warehouse_ids = [w[0] for w in warehouses]
    retailer_ids = [r[0] for r in retailers]
    demand_dict = {r[0]: r[2] for r in retailers}
    cost_dict = {(r[0], r[1]): r[2] for r in routes}

    filtered_routes = [
        (wh, rt, cost)
        for (wh, rt, cost) in routes
        if wh in warehouse_ids and (max_cost is None or cost <= max_cost)
    ]

    # ---------------------------
    # 3. Optimization Model
    # ---------------------------
    prob = LpProblem("Warehouse_to_Retailer_Routing", LpMinimize)

    x = LpVariable.dicts("route",
                         ((w, r) for w in warehouse_ids for r in retailer_ids),
                         lowBound=0, upBound=1, cat='Binary')

    # Objective: minimize total cost
    prob += lpSum(
        cost * x[(w, r)]
        for (w, r, cost) in filtered_routes
        if (w, r) in x
    ), "Total Routing Cost"

    # Demand coverage constraint
    for r in retailer_ids:
        prob += lpSum(x[(w, r)] for w in warehouse_ids if (w, r) in x) >= 1, f"DemandCoverage_Retailer_{r}"

    # ---------------------------
    # 4. Solve
    # ---------------------------
    prob.solve()
    status = LpStatus[prob.status]

    assignments = []
    if status == "Optimal":
        for (w, r) in x:
            if x[(w, r)].varValue > 0.5:
                assignments.append({
                    "warehouse_id": w,
                    "retailer_id": r,
                    "cost": cost_dict.get((w, r), None)
                })

    return {
        "status": status,
        "assignments": assignments
    }
