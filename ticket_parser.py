import csv
from collections import defaultdict
import statistics


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
    learned_complexity = {}

    for tag, times in tag_resolution_times.items():
        if len(times) >= 1:
            tag_average = statistics.mean(times)
            #calculate complexity: if a tag takes 2x the average, it gets score -10
            complexity_score = (tag_average / overall_average) * 5
            learned_complexity[tag] = {
                'score': complexity_score,
                'avg_time': tag_average,
                'ticket_count': len(times),
            }
    return learned_complexity

def predict_ticket_complexity(row, learned_complexity):

    #if no tags in row or no learned complexity data
    if not row['Tags'] or not learned_complexity:
        return 5.0, 'No data available' #output default score

    #split the comma-seperated tags into individual tags
    individual_tags = [tag.strip() for tag in row['Tags'].split(',')]

    total_score = 0 #for accumulating scores
    contributed_tags = [] #track which tags contributed

    for tag in individual_tags:
        if tag in learned_complexity:
            total_score += learned_complexity[tag]['score']
            contributed_tags.append(f"{tag}({total_score:.1f})")

    if not contributed_tags:
        return 5.0, 'Unknown tags'

    predicted_score = total_score / len(contributed_tags)
    explanation = "Based on: " + ','.join(contributed_tags)

    return predicted_score, explanation

#Convert complexity score to readable category
def classify_by_complexity(score):
    if score <= 3:
        return "Simple"
    elif score <= 7:
        return "Moderate"
    else:
        return "Complex"

#Generate insights based on what we learned from the data
def generate_learned_insights(learned_complexity, resolution_data):
    print("\n🔍 WHAT THE SYSTEM LEARNED FROM THE DATA")

    if not learned_complexity:
        print("Not enough data to generte insights")
        return

    #Find the most and least complex tags
    sorted_by_complexity = sorted(learned_complexity.items(), key=lambda x: x[1]['score'], reverse=True)

    print(f"\n📈 MOST COMPLEX ISSUES")
    for tag, data in sorted_by_complexity[:5]: #Top 5 most complex
        print(f"{tag}: {data['avg_time']:.1f}h average ({data['ticket_count']} tickets)")

    print(f"\n📉 SIMPLEST ISSUES")
    for tag, data in sorted_by_complexity[-5:]:  # Bottom 5 (simplest)
        print(f"• {tag}: {data['avg_time']:.1f}h average ({data['ticket_count']} tickets)")

    # Categorize all issues
    complexity_distribution = {'Simple': 0, 'Moderate': 0, 'Complex': 0}
    for tag, data in learned_complexity.items():
        category = classify_by_complexity(data['score'])
        complexity_distribution[category] += data['ticket_count']

    print(f"\n📊 COMPLEXITY DISTRIBUTION:")
    total_tickets = sum(complexity_distribution.values())
    for category, count in complexity_distribution.items():
        percentage = (count / total_tickets) * 100 if total_tickets > 0 else 0
        print(f"• {category}: {count} tickets ({percentage:.1f}%)")


def predict_open_tickets(resolution_data, learned_complexity):
    """Make predictions for tickets that are still open"""
    print(f"\n🔮 PREDICTIONS FOR OPEN/IN-PROGRESS TICKETS:")

    predictions = []
    for row in resolution_data:
        # Only predict for unresolved tickets
        if row['Status'] in ['open', 'pending']:
            complexity_score, explanation = predict_ticket_complexity(row, learned_complexity)
            complexity_category = classify_by_complexity(complexity_score)

            prediction = {
                'ticket_id': row.get('Conversation ID', 'Unknown'),
                'tags': row.get('Tags', 'No tags'),
                'status': row.get('Status', 'Unknown'),
                'complexity_score': complexity_score,
                'complexity_category': complexity_category,
                'explanation': explanation
            }
            predictions.append(prediction)

    if not predictions:
        print("✅ No open tickets found!")
        return predictions

    # Sort by complexity (most complex first)
    predictions.sort(key=lambda x: x['complexity_score'], reverse=True)

    print(f"Found {len(predictions)} open tickets:")
    for pred in predictions[:10]:  # Show top 10 most complex
        print(f"• Ticket {pred['ticket_id']}: {pred['complexity_category']} "
              f"(score: {pred['complexity_score']:.1f}) - {pred['tags']}")

    return predictions


def generate_recommendations(learned_complexity, predictions):
    """Generate actionable recommendations based on learned data"""
    print(f"\n💡 AI RECOMMENDATIONS:")

    if not learned_complexity:
        print("❌ Need more data to generate recommendations")
        return

    # Find problem areas
    complex_tags = [(tag, data) for tag, data in learned_complexity.items()
                    if data['score'] > 7 and data['ticket_count'] >= 2]

    if complex_tags:
        print(f"\n🚨 HIGH-COMPLEXITY AREAS NEEDING ATTENTION:")
        for tag, data in sorted(complex_tags, key=lambda x: x[1]['score'], reverse=True)[:3]:
            print(f"• {tag}: {data['avg_time']:.1f}h average - Consider:")

            # Specific recommendations based on tag type
            if tag in ['ssl', 'certificate', 'security']:
                print("  - Create SSL troubleshooting checklist")
                print("  - Provide security certification training")
            elif tag in ['dns', 'propagation', 'nameservers']:
                print("  - Document DNS change procedures")
                print("  - Create DNS diagnostic tools")
            elif tag in ['integration', 'api', 'webhook']:
                print("  - Develop integration testing scripts")
                print("  - Create API troubleshooting guide")
            elif tag in ['performance', 'slow', 'optimization']:
                print("  - Invest in performance monitoring tools")
                print("  - Create performance baseline documentation")
            else:
                print(f"  - Create detailed procedures for {tag} issues")
                print(f"  - Consider specialist training for {tag}")

    # Staffing recommendations
    high_volume_complex = [(tag, data) for tag, data in learned_complexity.items()
                           if data['score'] > 5 and data['ticket_count'] > 5]

    if high_volume_complex:
        print(f"\n👥 STAFFING RECOMMENDATIONS:")
        print("Consider assigning specialists for these high-volume complex areas:")
        for tag, data in sorted(high_volume_complex, key=lambda x: x[1]['ticket_count'], reverse=True)[:3]:
            print(f"• {tag}: {data['ticket_count']} tickets, {data['avg_time']:.1f}h avg")


# ==================================================
# STEP 3: MAIN EXECUTION FUNCTION
# ==================================================

def main():
    """
    Main function that runs everything step by step
    """
    print("🚀 STARTING AI-POWERED HELP DESK ANALYSIS")
    print("=" * 50)

    # Step 1: Read and store all the data
    print("📖 Reading CSV file...")

    category_counts = defaultdict(int)  # Count tickets by status
    tag_counts = defaultdict(int)  # Count tickets by tag
    resolution_data = []  # Store all ticket data

    try:
        with open('C:/Users/Ddr3/Documents/CyberSecurity/help desk ticket parser and reporter/intercom_report_csv.csv',
                  'r') as file:
            csv_reader = csv.DictReader(file)  # This reads CSV as dictionaries

            for row in csv_reader:
                resolution_data.append(row)  # Store each row

                # Count by status
                if row['Status']:
                    category_counts[row['Status']] += 1

                # Count by individual tags
                if row['Tags']:
                    individual_tags = [tag.strip() for tag in row['Tags'].split(',')]
                    for tag in individual_tags:
                        if tag:
                            tag_counts[tag] += 1

        print(f"✅ Successfully read {len(resolution_data)} tickets")

    except FileNotFoundError:
        print("❌ CSV file not found! Please check the file path.")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Step 2: Learn complexity from the data
    learned_complexity = learn_complexity_from_data(resolution_data)

    # Step 3: Generate basic reports
    print("\n" + "=" * 50)
    print("📊 BASIC TICKET SUMMARY")
    print("=" * 50)

    print(f"\n📋 STATUS BREAKDOWN:")
    for status, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"• {status}: {count} tickets")

    print(f"\n🏷️ TOP TAGS:")
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:10]:  # Show top 10 tags
        print(f"• {tag}: {count} tickets")

    # Step 4: Generate AI insights
    print("\n" + "=" * 50)
    print("🤖 AI ANALYSIS RESULTS")
    print("=" * 50)

    generate_learned_insights(learned_complexity, resolution_data)
    predictions = predict_open_tickets(resolution_data, learned_complexity)
    generate_recommendations(learned_complexity, predictions)

    print(f"\n✨ Analysis complete! The AI has learned from {len(resolution_data)} tickets.")


# ==================================================
# STEP 4: RUN THE PROGRAM
# ==================================================

if __name__ == "__main__":
    main()


