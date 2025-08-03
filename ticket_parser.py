import csv
from collections import defaultdict
import statistics

category_counts = defaultdict(int)
tag_counts = defaultdict(int) #tag counts
resolution_counts = defaultdict(int)
resolution_data = []

# Classify ticket resolution speed
def classify_resolution_speed(hours):

    if hours <= 1.5:
        return "Fast"
    elif hours <= 6.0:
        return "Normal"
    else:
        return "Slow"

#learn ticket complexity
def learn_complexity_from_data(resolution_data):
    """learn tag complexity based on resolution data"""
    tag_resolution_times = defaultdict(list)

    #collect resolution times from each tag
    for row in resolution_data:
        if row['Tags'] and row['Resolution Time (hours)']:
            try:
                hours = float(row['Resolution Time (hours)'])
                individual_tags = [tag.strip() for tag in row['Tags'].split(',')]
                for tag in individual_tags:
                    if tag:
                        tag_resolution_times[tag].append(hours)
            except ValueError:
                continue

    #calculate the overall average resolution time
    all_times = []
    for row in resolution_data:
        if row['Resolution Time (hours)']:
            try:
                all_times.append(float(row['Resolution Time (hours)']))
            except ValueError:
                continue

    if not all_times:
        print("❌ No resolution data found!")
        return {}

    overall_average = statistics.mean(all_times)
    print(f"Overall average resolution time: {overall_average:.1f} hours")

    #Calculate complexity scores based on how much longer than average each tag takes
    learn_complexity = {}

    for tag, times in tag_resolution_times.items():
        if len(times) >= 1:
            tag_average = statistics.mean(times)
            #calculate complexity: if a tag takes 2x the average, it gets score -10
            complexity_score = (tag_average / overall_average) * 5
            learn_complexity[tag] = {
                'score': complexity_score,
                'avg_time': tag_average,
                'ticket_count': len(times),
            }
    return learn_complexity

with open('C:/Users/Ddr3/Documents/CyberSecurity/help desk ticket parser and reporter/intercom_report_csv.csv',
          'r') as file:
    read = csv.DictReader(file)

    for row in read:
        category = row['Status']
        category_counts[category] += 1

        tags = row['Tags']
        if tags: #check if not empty
            individual_tag = tags.split(',')
            for tag in individual_tag:
                if tag:
                    tag_counts[tag] += 1

        if row['Resolution Time (hours)']: #check if not empty
            hours = float(row['Resolution Time (hours)'])
            specific_resolution_speed = classify_resolution_speed(hours)
            resolution_counts[specific_resolution_speed] += 1

# Print a report
print("Ticket Summary")

for category, count in category_counts.items():
    print(f"{category}: {count} tickets")

for tag, count in tag_counts.items():
    print(f"{tag}: {count} tickets")

for speed in ['Fast', 'Normal', 'Slow']:
    print(f"{speed}: {resolution_counts[speed]} tickets")