import json
import pandas as pd

with open("contact_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

parsed_data = []
for entry in data:
    contact_lines = entry["contact"].split("\n")
    
    # Define the contact information, handling optional second phone number
    contact_info = {
        "URL": entry["url"],
        "Company": contact_lines[1] if len(contact_lines) > 1 else None,
        "Address": contact_lines[2] if len(contact_lines) > 2 else None,
        "Postal Code & City": contact_lines[3] if len(contact_lines) > 3 else None,
        "Phone 1": contact_lines[4] if len(contact_lines) > 4 else None,
        "Phone 2": contact_lines[5] if len(contact_lines) > 5 and "@" not in contact_lines[5] else None,
        "Email": contact_lines[5] if len(contact_lines) > 5 and "@" in contact_lines[5] else contact_lines[6] if len(contact_lines) > 6 and "@" in contact_lines[6] else None,
        "Notes": " ".join(contact_lines[7:]) if len(contact_lines) > 7 else None
    }
    parsed_data.append(contact_info)

# Convert to DataFrame
df_contacts = pd.DataFrame(parsed_data)


output_excel_path = "digitalone_site.xlsx" #"local_ch.xlsx"
df_contacts.to_excel(output_excel_path, index=False, engine="openpyxl")

print(f"Data saved successfully to {output_excel_path}")
