def silent_int(value: str) -> int:
    try:
        return int(value)
    except:
        return None
