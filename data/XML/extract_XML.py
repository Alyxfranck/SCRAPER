import os
import re
import json
import xml.etree.ElementTree as ET

# Specify the path to your directory containing XML files
directory_path = 'ml'  # Update with the correct path if necessary

# List to store extracted URLs
all_urls = []

# Iterate over each XML file in the directory
for filename in os.listdir(directory_path):
    if filename.endswith('.xml'):
        file_path = os.path.join(directory_path, filename)
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract URLs within <loc> tags
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                all_urls.append(url.text)
        
        except ET.ParseError as e:
            print(f"Error parsing {filename}: {e}")

# Save the extracted URLs as a JSON array
with open('extracted_urls.json', 'w', encoding='utf-8') as json_file:
    json.dump(all_urls, json_file, indent=2)

print("URLs have been extracted and saved to 'extracted_urls.json'")
