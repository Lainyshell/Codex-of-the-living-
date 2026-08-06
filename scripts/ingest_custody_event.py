import argparse
import json
import sys
from pathlib import Path


def _load_payload(args) -> dict:
    if args.event_json:
        return json.loads(args.event_json)
    if args.event_file:
        return json.loads(Path(args.event_file).read_text(encoding="utf-8"))
    raise ValueError("Either --event-json or --event-file is required")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a custody event to a VBTN custody envelope.")
    parser.add_argument("--event-json", help="Raw JSON event payload")
    parser.add_argument("--event-file", help="Path to a JSON event payload file")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "app"))

    import custody  # noqa: PLC0415

    payload = _load_payload(args)
    envelope = custody.ingest_event_payload(payload)
    print(json.dumps({
        "transaction_id": envelope["transaction_id"],
        "custody_status": envelope["custody_status"],
        "event_count": len(envelope["events"]),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
