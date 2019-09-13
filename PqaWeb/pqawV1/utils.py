def silent_int(value: str) -> int:
    try:
        return int(value)
    except:
        return None


def format_probability(prob: float) -> str:
    perc = prob * 100
    if round(perc, 1) >= 100:
        return '100'
    elif round(perc, 2) >= 10:
        return '{0:.1f}'.format(perc)
    else:
        return '{0:.2f}'.format(perc)
