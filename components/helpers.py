from datetime import datetime
import re


def calc_timestamp():
    return int(datetime.now().timestamp())


def extract_channel_from_label(text):
    # Extract channel number from "(ChN)" pattern only
    # This avoids picking up numbers from custom channel names like "tt22"
    match = re.search(r'\(Ch(\d+)\)', text)
    if match:
        ch_num = int(match.group(1))
        return ch_num - 1
    # Fallback to first number if pattern not found (shouldn't happen with current format)
    ch = re.search(r'\d+', text)
    if ch:
        ch_num = int(ch.group())
        return ch_num - 1
    return 0

