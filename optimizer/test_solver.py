from solver import solve_routing

def test_basic():
    result = solve_routing()
    print("Status:", result["status"])
    print("Assignments:")
    for a in result["assignments"]:
        print(a)

if __name__ == "__main__":
    test_basic()
