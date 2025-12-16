import re

# Persian \u0600-\u06FF
# Arabic \u0627-\u064a


def guess_text_direction(text):
    try:
        lang = ["left", "right"]
        # you need to add other languages pattern here
        pattern = re.compile("[\u0627-\u064a]|[\u0600-\u06FF]")

        return lang[len(re.findall(pattern, text)) > (len(text) / 2)]
    except Exception as e:
        print(f"exception {e} found while detect text direction!")
        return None


def human_readable_number(num):
    if num >= 1_000_000_000:
        return f"{num // 1_000_000_000}B"
    elif num >= 1_000_000:
        return f"{num // 1_000_000}M"
    elif num >= 1_000:
        return f"{num // 1_000}K"
    else:
        return str(num)
