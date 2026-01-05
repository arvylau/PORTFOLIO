#!/usr/bin/env python3
"""
Project Task Matrix Generator
Combines Kumu network data with Todoist portfolio to create a comprehensive matrix
"""

import pandas as pd
import json
from datetime import datetime

def load_kumu_data():
    """Load and process Kumu network export"""
    elements = pd.read_excel('kumu-arvylau-network.xlsx', sheet_name='Elements')
    connections = pd.read_excel('kumu-arvylau-network.xlsx', sheet_name='Connections')

    # Separate by type
    people = elements[elements['Type'] == 'Person'].copy()
    tasks = elements[elements['Type'] == 'Task'].copy()
    projects = elements[elements['Type'] == 'Project'].copy()

    return people, tasks, projects, connections

def load_portfolio_data():
    """Load Todoist portfolio data"""
    import csv
    tasks = []

    with open('PORTFOLIO.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('TYPE') == 'task':
                tasks.append({
                    'content': row.get('CONTENT', '').strip(),
                    'priority': row.get('PRIORITY', '').strip(),
                    'section': '',
                    'date': row.get('DATE', '').strip(),
                    'deadline': row.get('DEADLINE', '').strip()
                })

    return pd.DataFrame(tasks)

def create_project_task_matrix(people, tasks, projects, connections, portfolio_tasks):
    """Create comprehensive project-task-person matrix"""

    # Extract major projects from connections
    major_projects = ['ONCOINTEGRA', 'PPM4ML', 'VU SMEC Kidnex', 'NEPHROSCAN.LT', 'Hex4Path']

    # Create set of Todoist task names for quick lookup
    todoist_tasks = set(portfolio_tasks['content'].str.lower().tolist()) if len(portfolio_tasks) > 0 else set()

    matrix_data = []

    for _, task in tasks.iterrows():
        task_name = task['Label']
        tags = task['Tags'] if pd.notna(task['Tags']) else ''
        status = 'ACTIVE' if 'ACTIVE' in str(tags) else ('IDEA' if 'IDEA' in str(tags) else 'DONE' if 'DONE' in str(tags) else 'Unknown')

        # Check if this task is in Todoist
        in_todoist = any(task_name.lower() in todoist_task or todoist_task in task_name.lower() for todoist_task in todoist_tasks)

        # Find which major project this task belongs to
        task_connections = connections[(connections['From'] == task_name) | (connections['To'] == task_name)]

        related_projects = []
        related_people = []
        related_people_data = []

        for _, conn in task_connections.iterrows():
            other = conn['To'] if conn['From'] == task_name else conn['From']
            if other in major_projects:
                related_projects.append(other)
            # Check if it's a person
            if other in people['Label'].values:
                related_people.append(other)
                # Get person data including image
                person_data = people[people['Label'] == other].iloc[0]
                image_url = person_data.get('Image', '')
                if pd.notna(image_url) and image_url:
                    related_people_data.append({
                        'name': other,
                        'image': image_url
                    })
                else:
                    related_people_data.append({
                        'name': other,
                        'image': ''
                    })

        matrix_data.append({
            'Task': task_name,
            'Status': status,
            'Tags': tags,
            'In_Todoist': in_todoist,
            'Projects': ', '.join(related_projects) if related_projects else 'Independent',
            'People': ', '.join(related_people[:3]) if related_people else 'Unassigned',
            'People_Data': related_people_data,
            'Team_Size': len(related_people),
            'Description': task['Description'] if pd.notna(task['Description']) else ''
        })

    return pd.DataFrame(matrix_data)

def create_project_summary(projects, tasks, connections):
    """Create project summary showing tasks per project"""

    major_projects = ['ONCOINTEGRA', 'PPM4ML', 'VU SMEC Kidnex', 'NEPHROSCAN.LT', 'Hex4Path']
    summary = []

    for proj in major_projects:
        # Find all tasks connected to this project
        proj_connections = connections[(connections['From'] == proj) | (connections['To'] == proj)]

        related_tasks = []
        for _, conn in proj_connections.iterrows():
            other = conn['To'] if conn['From'] == proj else conn['From']
            if other in tasks['Label'].values:
                related_tasks.append(other)

        summary.append({
            'Project': proj,
            'Tasks': len(related_tasks),
            'Task_List': '; '.join(related_tasks[:5]) + ('...' if len(related_tasks) > 5 else '')
        })

    return pd.DataFrame(summary)

def generate_html_matrix(matrix_df, project_summary):
    """Generate interactive HTML matrix visualization"""

    status_colors = {
        'ACTIVE': '#4CAF50',
        'IDEA': '#2196F3',
        'DONE': '#9E9E9E',
        'Unknown': '#FFC107'
    }

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Task Matrix</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .header h1 {{
            color: #333;
            font-size: 32px;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            color: #666;
            font-size: 16px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-card .number {{
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .section h2 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        tbody tr {{
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s;
        }}

        tbody tr:hover {{
            background: #f8f9ff;
        }}

        td {{
            padding: 15px;
            font-size: 14px;
            color: #333;
        }}

        .task-name {{
            font-weight: 600;
            color: #667eea;
            max-width: 400px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }}

        .people-list {{
            color: #666;
            font-size: 13px;
        }}

        .team-size {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
        }}

        .filters {{
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            background: #f0f4ff;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}

        select {{
            padding: 10px 15px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            color: #667eea;
            background: white;
            cursor: pointer;
            min-width: 180px;
        }}

        select:focus {{
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }}

        .person-avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            object-fit: cover;
            margin-right: 8px;
            border: 2px solid #e0e0e0;
            vertical-align: middle;
        }}

        .person-chip {{
            display: inline-flex;
            align-items: center;
            margin: 2px;
            padding: 4px 8px;
            background: #f5f5f5;
            border-radius: 16px;
            font-size: 12px;
        }}

        .todoist-badge {{
            display: inline-block;
            padding: 2px 8px;
            background: #e44232;
            color: white;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Project Task Matrix</h1>
            <div class="subtitle">Integrated view of Kumu Network and Todoist Portfolio</div>
            <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="number">{len(matrix_df)}</div>
                <div class="label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(matrix_df[matrix_df['Status'] == 'ACTIVE'])}</div>
                <div class="label">Active Tasks</div>
            </div>
            <div class="stat-card">
                <div class="number">{len(project_summary)}</div>
                <div class="label">Major Projects</div>
            </div>
            <div class="stat-card">
                <div class="number">{matrix_df['Team_Size'].sum()}</div>
                <div class="label">Total Connections</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Project Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Project</th>
                        <th>Tasks</th>
                        <th>Task Examples</th>
                    </tr>
                </thead>
                <tbody>
'''

    for _, row in project_summary.iterrows():
        html += f'''
                    <tr>
                        <td><strong>{row['Project']}</strong></td>
                        <td><span class="team-size">{row['Tasks']}</span></td>
                        <td class="people-list">{row['Task_List']}</td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📋 Task Matrix</h2>
            <div class="filters">
                <button class="filter-btn active" onclick="filterByStatus('all')">All Tasks</button>
                <button class="filter-btn" onclick="filterByStatus('ACTIVE')">Active</button>
                <button class="filter-btn" onclick="filterByStatus('IDEA')">Ideas</button>
                <button class="filter-btn" onclick="filterByStatus('DONE')">Done</button>
            </div>
            <div class="filters">
                <select id="todoistFilter" onchange="applyFilters()">
                    <option value="all">All Tasks</option>
                    <option value="in-todoist">In Todoist</option>
                    <option value="not-in-todoist">Not in Todoist</option>
                </select>

                <select id="tagsFilter" onchange="applyFilters()">
                    <option value="all">All Tags</option>
'''

    # Get unique tags
    all_tags = set()
    for tags_str in matrix_df['Tags'].unique():
        if tags_str and pd.notna(tags_str) and str(tags_str).strip():
            for tag in str(tags_str).split('|'):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

    for tag in sorted(all_tags):
        html += f'                    <option value="{tag}">{tag}</option>\n'

    html += '''                </select>
            </div>
            <table id="taskTable">
                <thead>
                    <tr>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Projects</th>
                        <th>Team</th>
                        <th>People</th>
                    </tr>
                </thead>
                <tbody>
'''

    for _, row in matrix_df.sort_values(['Status', 'Task']).iterrows():
        status_color = status_colors.get(row['Status'], '#999')

        # Create task name with Todoist badge if applicable
        task_display = row['Task']
        if row['In_Todoist']:
            task_display += '<span class="todoist-badge">TODOIST</span>'

        # Create people display with images
        people_html = ''
        if row['People_Data'] and len(row['People_Data']) > 0:
            for person in row['People_Data'][:3]:
                if person['image']:
                    people_html += f'<span class="person-chip"><img src="{person["image"]}" class="person-avatar" alt="{person["name"]}">{person["name"]}</span>'
                else:
                    people_html += f'<span class="person-chip">{person["name"]}</span>'
            if len(row['People_Data']) > 3:
                people_html += f'<span class="person-chip">+{len(row["People_Data"]) - 3} more</span>'
        else:
            people_html = '<span class="people-list">Unassigned</span>'

        html += f'''
                    <tr class="task-row" data-status="{row['Status']}" data-todoist="{str(row['In_Todoist']).lower()}" data-tags="{row['Tags']}">
                        <td class="task-name">{task_display}</td>
                        <td><span class="status-badge" style="background: {status_color};">{row['Status']}</span></td>
                        <td>{row['Projects']}</td>
                        <td><span class="team-size">{row['Team_Size']}</span></td>
                        <td>{people_html}</td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let currentStatusFilter = 'all';

        function filterByStatus(status) {
            currentStatusFilter = status;
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            applyFilters();
        }

        function applyFilters() {
            const todoistFilter = document.getElementById('todoistFilter').value;
            const tagsFilter = document.getElementById('tagsFilter').value;
            const rows = document.querySelectorAll('.task-row');

            rows.forEach(row => {
                let show = true;

                // Status filter
                if (currentStatusFilter !== 'all' && row.dataset.status !== currentStatusFilter) {
                    show = false;
                }

                // Todoist filter
                if (todoistFilter === 'in-todoist' && row.dataset.todoist !== 'true') {
                    show = false;
                }
                if (todoistFilter === 'not-in-todoist' && row.dataset.todoist === 'true') {
                    show = false;
                }

                // Tags filter
                if (tagsFilter !== 'all') {
                    const rowTags = row.dataset.tags || '';
                    if (!rowTags.includes(tagsFilter)) {
                        show = false;
                    }
                }

                row.style.display = show ? '' : 'none';
            });

            // Update visible count
            const visibleCount = document.querySelectorAll('.task-row:not([style*="display: none"])').length;
            console.log(`Showing ${visibleCount} tasks`);
        }
    </script>
</body>
</html>'''

    return html

def main():
    print("=" * 70)
    print("Project Task Matrix Generator")
    print("=" * 70)
    print()

    print("Loading Kumu network data...")
    people, tasks, projects, connections = load_kumu_data()
    print(f"  - {len(people)} people")
    print(f"  - {len(tasks)} tasks")
    print(f"  - {len(projects)} projects")
    print(f"  - {len(connections)} connections")

    print("\nLoading Todoist portfolio...")
    portfolio_tasks = load_portfolio_data()
    print(f"  - {len(portfolio_tasks)} portfolio tasks")

    print("\nCreating project task matrix...")
    matrix_df = create_project_task_matrix(people, tasks, projects, connections, portfolio_tasks)

    print("Creating project summary...")
    project_summary = create_project_summary(projects, tasks, connections)

    print("\nGenerating HTML visualization...")
    html = generate_html_matrix(matrix_df, project_summary)

    with open('project_task_matrix.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Export data to Excel
    print("Exporting to Excel...")
    with pd.ExcelWriter('project_task_matrix.xlsx', engine='openpyxl') as writer:
        matrix_df.to_excel(writer, sheet_name='Task Matrix', index=False)
        project_summary.to_excel(writer, sheet_name='Project Summary', index=False)

    print()
    print("=" * 70)
    print("DONE!")
    print("=" * 70)
    print("Generated files:")
    print("  - project_task_matrix.html (interactive visualization)")
    print("  - project_task_matrix.xlsx (Excel export)")
    print("=" * 70)

if __name__ == "__main__":
    main()
