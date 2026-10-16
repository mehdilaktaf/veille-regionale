from src.clients.clients import build_client
import logging

logging.basicConfig(level=logging.INFO)

def test():
    dept = "Seine-Saint-Denis"
    year = "2026"
    month = "09"
    print(f"Testing {dept} {year}-{month}...")
    client = build_client(dept, year)
    docs = client.documents_for_month(month)
    print(f"Found {len(docs)} documents:")
    for url, name in docs:
        print(f"- {name}: {url}")

if __name__ == "__main__":
    test()
