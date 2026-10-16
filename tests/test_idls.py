
from src.clients.clients import build_client
import logging

logging.basicConfig(level=logging.WARNING)

try:
    client = build_client("Indre-et-Loire", 2026)
    print(f"Client created: {client}")
    docs = client.documents_for_month("09")
    print(f"Documents found: {len(docs)}")
    for d in docs:
        print(d)
except Exception as e:
    print(f"Error: {e}")
