import pandas as pd
import re, json

df = pd.read_excel("backend/data/stn1HMIAlamrs.xlsx", sheet_name="Sheet1")

def map_to_db_position(trigger_tag, trigger_bit, base_db=1020):
    match = re.match(r"([WA]W)(\d+)\(1\)", trigger_tag)
    if not match:
        return None
    prefix, offset = match.groups()
    offset = int(offset)
    byte = offset+1  # No +1 offset
    if trigger_bit >= 8:
        byte -= 1
        trigger_bit -= 8
    result = f"DB{base_db}.DBX{byte}.{trigger_bit}"
    return result
# Create mapping dictionary
alarm_map = {}
for _, row in df.iterrows():
    db_position = map_to_db_position(row["Trigger tag"], row["Trigger bit"])
    if db_position:
        alarm_map[db_position] = row["Alarm text [en-US], Alarm text 1"]

# Save to JSON
with open("backend/data/alarm_map.json", "w") as f:
    json.dump(alarm_map, f, indent=2)

print("Alarm map generated at backend/data/alarm_map.json")