## data processing unit

import pandas as pd
import json
import re

file_path = 'contact_data.json'
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    print(f"File {file_path} not found.")
    exit()
except json.JSONDecodeError:
    print("Error decoding JSON.")
    exit()

phone_pattern = re.compile(r'^\+?\d[\d\s\-]{7,}$')
email_pattern = re.compile(r'^\S+@\S+\.\S+$')

processed_data = []
for entry in data:
    contact_info = [elem.strip() for elem in entry.get('contact', '').split('\t')]
    
    contact_info = [elem for elem in contact_info if elem]
    

    label = company = street_address = postal_code = city = ""
    phones = []
    emails = []
    additional_info = []
    languages = []

    idx = 0
    total_elements = len(contact_info)


    if idx < total_elements:
        label = contact_info[idx]
        idx += 1

    if idx < total_elements:
        company = contact_info[idx]
        idx += 1

    if idx < total_elements:
        street_address = contact_info[idx]
        idx += 1

    if idx < total_elements and re.match(r'^\d{4}$', contact_info[idx]):
        postal_code = contact_info[idx]
        idx += 1
    else:
        postal_code = ""

    while idx < total_elements and contact_info[idx].strip() == "":
        idx += 1

    if idx < total_elements:
        city = contact_info[idx]
        idx += 1

    while idx < total_elements:
        element = contact_info[idx]
        if phone_pattern.match(element):
            phones.append(element)
        elif email_pattern.match(element):
            emails.append(element)
        elif element in ['Sprachen', 'Langues', 'Lingue']:
            # Collect languages
            idx += 1
            while idx < total_elements and contact_info[idx] not in ['Zahlungsmethoden', 'Payment Methods', 'Opzioni di pagamento']:
                languages.append(contact_info[idx])
                idx += 1
            idx -= 1  
        else:
            additional_info.append(element)
        idx += 1

    structured_entry = {
        "URL": entry.get("url", ""),
        "Label": label,
        "Company": company,
        "Street Address": street_address,
        "Postal Code": postal_code,
        "City": city,
        "Phones": "; ".join(phones),
        "Emails": "; ".join(emails),
        "Additional Info": "; ".join(additional_info),
        "Languages": "; ".join(languages)
    }

    processed_data.append(structured_entry)

# Convert to DataFrame and save as Excel
df = pd.DataFrame(processed_data)
output_file_path = 'data.xlsx'
df.to_excel(output_file_path, index=False)

print("Data has been processed and saved to:", output_file_path)
