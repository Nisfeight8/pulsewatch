class InvalidEventError(Exception):
    pass


def parse_event(fields: dict[str, str]) -> dict:
    try:
        return {
            "action": fields["action"],
            "monitor_id": fields["monitor_id"],
            "version": int(fields["version"]),
            "url": fields.get("url", ""),
            "name": fields.get("name", ""),
            "interval_seconds": int(fields.get("interval_seconds", 60)),
            "is_active": fields.get("is_active") == "True",
        }
    except (KeyError, ValueError) as exc:
        raise InvalidEventError(f"malformed monitor event: {exc}") from exc
