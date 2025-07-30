import csv
from collections import defaultdict

category_counts = defaultdict(int)
tag_counts = defaultdict(int) #tag counts

with open('C:/Users/Ddr3/Documents/CyberSecurity/help desk ticket parser and reporter/intercom_report_csv.csv',
          'r') as file:
    read = csv.DictReader(file)

    for row in read:
        category = row['Status']
        category_counts[category] += 1

        tags = row['Tags']
        if tags: #if ticket contains tags
            individual_tag = tags.split(',')
            for tag in individual_tag:
                if tag:
                    tag_counts[tag] += 1

# Print a report
print("Ticket Summary")

for category, count in category_counts.items():
    print(f"{category}: {count} tickets")

for tag, count in tag_counts.items():
    print(f"{tag}: {count} tickets")