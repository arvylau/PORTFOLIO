import csv
import json

# Parse CSV
tasks = []
with open('PORTFOLIO.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row.get('TYPE') == 'task':
            content = row.get('CONTENT', '').strip()
            priority_str = row.get('PRIORITY', '').strip()

            if priority_str == '':
                csv_priority = 1
            else:
                try:
                    csv_priority = int(priority_str)
                except:
                    csv_priority = 1

            # Apply @PROJECT override
            if '@PROJECT' in content.upper():
                final_priority = 4
            else:
                final_priority = csv_priority

            tasks.append({
                'content': content[:50],
                'csv_priority': csv_priority,
                'final_priority': final_priority,
                'overridden': final_priority != csv_priority
            })

# Write to file
with open('priority_report.txt', 'w', encoding='utf-8') as f:
    f.write("Priority Summary:\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total tasks: {len(tasks)}\n")
    f.write(f"Tasks with @PROJECT override: {sum(1 for t in tasks if t['overridden'])}\n\n")

    # Show high priority tasks
    f.write("High Priority Tasks (P1 = priority 4):\n")
    f.write("-" * 80 + "\n")
    for t in tasks:
        if t['final_priority'] == 4:
            override_marker = " (OVERRIDE from @PROJECT)" if t['overridden'] else ""
            f.write(f"  {t['content']}{override_marker}\n")

    f.write("\n")
    f.write("Medium-High Priority Tasks (P2 = priority 3):\n")
    f.write("-" * 80 + "\n")
    for t in tasks:
        if t['final_priority'] == 3:
            f.write(f"  {t['content']}\n")

    f.write("\n")
    f.write("Medium Priority Tasks (P3 = priority 2):\n")
    f.write("-" * 80 + "\n")
    for t in tasks:
        if t['final_priority'] == 2:
            f.write(f"  {t['content']}\n")

    f.write("\n")
    f.write("Low Priority Tasks (P4 = priority 1):\n")
    f.write("-" * 80 + "\n")
    for t in tasks:
        if t['final_priority'] == 1:
            f.write(f"  {t['content']}\n")

print("Priority report written to priority_report.txt")
