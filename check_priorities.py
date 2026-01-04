import csv
import sys

# Set UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('PORTFOLIO.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    print("Tasks and their priorities:")
    print("=" * 80)

    count = 0
    for row in reader:
        if row.get('TYPE') == 'task':
            content = row.get('CONTENT', '').strip()
            priority = row.get('PRIORITY', '').strip()

            # Encode safely for display
            try:
                display_content = content[:60]
            except:
                display_content = content.encode('ascii', 'ignore').decode()[:60]

            print(f"Priority '{priority}': {display_content}")

            if '@PROJECT' in content.upper():
                print(f"  ^^^ @PROJECT task detected")

            count += 1
            if count > 30:  # Limit output
                break
