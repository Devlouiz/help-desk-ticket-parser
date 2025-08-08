import csv
from collections import defaultdict
import statistics
import argparse
from pathlib import Path
from typing import List, Dict

# ==================================================
# STEP 1: DATA LEARNING FUNCTIONS
# ==================================================

def learn_tag_complexity_from_data(resolution_data):
    """
    This function learns how complex each tag is based on actual resolution times.
    Instead of guessing, we let the data teach us!
    """
    print("🧠 Learning from your data...")

    # Step 1a: Collect all resolution times for each tag
    tag_resolution_times = defaultdict(list)  # This will store lists of times for each tag

    for row in resolution_data:
        # Only process rows that have both tags and resolution time
        if row['Tags'] and row['Resolution Time (hours)']:
            try:
                hours = float(row['Resolution Time (hours)'])  # Convert text to number
                # Split multiple tags (like "dns, ssl, critical")
                individual_tags = [tag.strip() for tag in row['Tags'].split(',')]

                # Add this resolution time to each tag's list
                for tag in individual_tags:
                    if tag:  # Make sure tag isn't empty
                        tag_resolution_times[tag].append(hours)
            except ValueError:
                # Skip if resolution time isn't a valid number
                continue

    # Step 1b: Calculate the overall average resolution time
    all_times = []
    for row in resolution_data:
        if row['Resolution Time (hours)']:
            try:
                all_times.append(float(row['Resolution Time (hours)']))
            except ValueError:
                continue

    if not all_times:
        print("❌ No valid resolution time data found!")
        return {}

    overall_average = statistics.mean(all_times)
    print(f"📊 Overall average resolution time: {overall_average:.1f} hours")

    # Step 1c: Calculate complexity scores based on how much longer than average each tag takes
    learned_complexity = {}

    for tag, times in tag_resolution_times.items():
        if len(times) >= 1:  # Need at least 1 data point
            tag_average = statistics.mean(times)
            # Calculate complexity: if a tag takes 2x the average, it gets score ~10
            complexity_score = (tag_average / overall_average) * 5
            learned_complexity[tag] = {
                'score': complexity_score,
                'avg_time': tag_average,
                'ticket_count': len(times)
            }

    return learned_complexity


def predict_ticket_complexity(row, learned_complexity):
    """
    Predict how complex a ticket will be based on its tags and our learned data
    """
    if not row['Tags'] or not learned_complexity:
        return 5.0, "No data available"  # Default middle score

    # Split the tags for this ticket
    individual_tags = [tag.strip() for tag in row['Tags'].split(',')]

    # Calculate predicted complexity based on the tags
    total_score = 0
    contributing_tags = []

    for tag in individual_tags:
        if tag in learned_complexity:
            tag_score = learned_complexity[tag]['score']
            total_score += tag_score
            contributing_tags.append(f"{tag}({tag_score:.1f})")

    if not contributing_tags:
        return 5.0, "Unknown tags"

    # Average the scores from all tags
    predicted_score = total_score / len(contributing_tags)
    explanation = f"Based on: {', '.join(contributing_tags)}"

    return predicted_score, explanation


# ==================================================
# STEP 2: ANALYSIS AND INSIGHTS FUNCTIONS
# ==================================================

def classify_by_complexity(score):
    """Convert numeric complexity score to human-readable category"""
    if score <= 3:
        return "Simple"
    elif score <= 7:
        return "Moderate"
    else:
        return "Complex"


def generate_learned_insights(learned_complexity, resolution_data):
    """Generate insights based on what we learned from the data"""
    print("\n🔍 WHAT THE AI LEARNED FROM YOUR DATA:")

    if not learned_complexity:
        print("❌ Not enough data to generate insights")
        return

    # Find the most and least complex tags
    sorted_by_complexity = sorted(learned_complexity.items(),
                                  key=lambda x: x[1]['score'],
                                  reverse=True)

    print(f"\n📈 MOST COMPLEX ISSUES (take longest to resolve):")
    for tag, data in sorted_by_complexity[:5]:  # Top 5 most complex
        print(f"• {tag}: {data['avg_time']:.1f}h average ({data['ticket_count']} tickets)")

    print(f"\n📉 SIMPLEST ISSUES (resolve quickly):")
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


def load_csv(path: Path) -> tuple[List[Dict[str, str]], Dict[str, int], Dict[str, int]]:
    #Load CSV file and generate stats
    #Return : tuple: (resolution_data, category_counts, tag_counts)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File {path} not found")

    resolution_data = []
    category_counts = defaultdict(int)  # Count tickets by status
    tag_counts = defaultdict(int)  # Count tickets by tag

    try:
        with path.open('r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
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
        if not resolution_data:
            raise ValueError("<UNK> CSV file contains not data!")

        return resolution_data, category_counts, tag_counts


    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")


# ==================================================
# STEP 3: MAIN EXECUTION FUNCTION
# ==================================================

def main(csv_path: str):
    """
    Main function that runs everything step by step
    """
    print("🚀 STARTING AI-POWERED HELP DESK ANALYSIS")
    print("=" * 50)

    # Convert to Path object and validate
    try:
        csv_path = Path(csv_path).resolve()  # Convert string to absolute Path
        print(f"📖 Reading CSV file from: {csv_path}...")

        resolution_data, category_counts, tag_counts = load_csv(csv_path)  # Store all ticket data
        print(f"Successfully Loaded {len(resolution_data)} rows from {csv_path}")

        learned_complexity = learn_tag_complexity_from_data(resolution_data)

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

    except FileNotFoundError as e:
        print(f"❌ File error: {e}")
        return
    except ValueError as e:
        print(f"❌ Data error: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return


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
    parser = argparse.ArgumentParser(description="<UNK> HelpDesk Analyzer")
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("-o", "--output", help="Optional output file path", default="analysis_report.txt")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    args = parser.parse_args()

    #csv_path = args.csv_path
    try:
        main(args.csv_path)
    except FileNotFoundError as e:
        print(f"<UNK> {e}")