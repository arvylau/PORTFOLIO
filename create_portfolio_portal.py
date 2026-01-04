"""
Smart Portfolio Management Portal Generator
Parses Todoist CSV export and creates interactive web portal
"""
import csv
import json
from datetime import datetime
from collections import defaultdict

def parse_csv(filename):
    """Parse Todoist CSV export"""
    sections = []
    current_section = None
    tasks = []
    task_notes = defaultdict(list)
    last_task_id = 0

    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_type = row.get('TYPE', '').strip()

            if row_type == 'section':
                current_section = {
                    'id': f"section_{len(sections)}",
                    'name': row.get('CONTENT', '').strip(),
                    'is_collapsed': row.get('IS_COLLAPSED', 'False') == 'True'
                }
                sections.append(current_section)

            elif row_type == 'task':
                last_task_id += 1
                task = {
                    'id': last_task_id,
                    'content': row.get('CONTENT', '').strip(),
                    'description': row.get('DESCRIPTION', '').strip(),
                    'priority': int(row.get('PRIORITY', 1)),
                    'indent': int(row.get('INDENT', 1)),
                    'section': current_section['name'] if current_section else 'No Section',
                    'author': row.get('AUTHOR', '').strip(),
                    'responsible': row.get('RESPONSIBLE', '').strip(),
                    'date': row.get('DATE', '').strip(),
                    'deadline': row.get('DEADLINE', '').strip(),
                    'deadline_lang': row.get('DEADLINE_LANG', '').strip(),
                    'notes': []
                }
                tasks.append(task)

            elif row_type == 'note' and last_task_id > 0:
                note = {
                    'content': row.get('CONTENT', '').strip(),
                    'author': row.get('AUTHOR', '').strip(),
                    'date': row.get('DATE', '').strip()
                }
                tasks[last_task_id - 1]['notes'].append(note)

    return sections, tasks

def build_task_hierarchy(tasks):
    """Build hierarchical task structure based on indent levels"""
    root_tasks = []
    task_stack = []  # Stack to track parent tasks at each indent level

    for task in tasks:
        task['children'] = []
        indent = task['indent']

        # Adjust stack size to current indent level
        while len(task_stack) >= indent:
            task_stack.pop()

        if indent == 1:
            # Root level task
            root_tasks.append(task)
            task_stack = [task]
        else:
            # Subtask - add to parent
            if task_stack:
                parent = task_stack[-1]
                parent['children'].append(task)
            task_stack.append(task)

    return root_tasks

def generate_html(sections, tasks):
    """Generate HTML portal"""

    # Get unique sections and priorities
    section_names = sorted(set(task['section'] for task in tasks))
    priorities = sorted(set(task['priority'] for task in tasks), reverse=True)

    # Priority labels (Todoist style: 4=highest, 1=lowest)
    priority_labels = {
        4: 'P1 (Highest)',
        3: 'P2 (High)',
        2: 'P3 (Medium)',
        1: 'P4 (Low)'
    }

    priority_colors = {
        4: '#d1453b',  # Red
        3: '#eb8909',  # Orange
        2: '#246fe0',  # Blue
        1: '#808080'   # Gray
    }

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Management Portal</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f8f9fa;
            color: #202020;
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .filters {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .filter-group label {{
            font-weight: 600;
            font-size: 14px;
            color: #555;
        }}

        .filter-group select {{
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            background: white;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-group select:hover {{
            border-color: #667eea;
        }}

        .filter-group select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .stats {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            display: flex;
            gap: 30px;
            align-items: center;
        }}

        .stat-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .stat-label {{
            font-size: 14px;
            color: #666;
        }}

        .stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: #667eea;
        }}

        .section-group {{
            margin-bottom: 30px;
        }}

        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px 8px 0 0;
            font-weight: 600;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-count {{
            background: rgba(255,255,255,0.2);
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 14px;
        }}

        .tasks-container {{
            background: white;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .task-card {{
            border-bottom: 1px solid #f0f0f0;
            padding: 16px 20px;
            transition: all 0.2s;
            cursor: pointer;
        }}

        .task-card:last-child {{
            border-bottom: none;
        }}

        .task-card:hover {{
            background: #f8f9ff;
        }}

        .task-card.subtask {{
            margin-left: 40px;
            border-left: 3px solid #e0e0e0;
            background: #fafafa;
        }}

        .task-card.subtask:hover {{
            background: #f5f5ff;
        }}

        .task-header {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 8px;
        }}

        .priority-badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            white-space: nowrap;
        }}

        .task-content {{
            flex: 1;
            font-size: 16px;
            font-weight: 500;
            color: #202020;
        }}

        .task-meta {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .meta-icon {{
            font-size: 14px;
        }}

        .description-toggle {{
            color: #667eea;
            font-size: 13px;
            font-weight: 600;
            margin-top: 8px;
            display: inline-block;
        }}

        .description-toggle:hover {{
            text-decoration: underline;
        }}

        .task-description {{
            display: none;
            margin-top: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            font-size: 14px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .task-description.expanded {{
            display: block;
        }}

        .task-notes {{
            display: none;
            margin-top: 12px;
            padding: 12px;
            background: #fff9e6;
            border-left: 3px solid #eb8909;
            border-radius: 4px;
        }}

        .task-notes.expanded {{
            display: block;
        }}

        .note-item {{
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f0e5c5;
        }}

        .note-item:last-child {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }}

        .note-content {{
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 5px;
        }}

        .note-meta {{
            font-size: 11px;
            color: #888;
        }}

        .deadline {{
            color: #d1453b;
            font-weight: 600;
        }}

        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
            font-size: 16px;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 24px;
            }}

            .filters {{
                grid-template-columns: 1fr;
            }}

            .stats {{
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }}

            .task-card.subtask {{
                margin-left: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>📋 Portfolio Management Portal</h1>
            <p>Smart task and project management system</p>
        </div>
    </div>

    <div class="container">
        <div class="filters">
            <div class="filter-group">
                <label for="filter-section">📂 Section</label>
                <select id="filter-section">
                    <option value="all">All Sections</option>
                    {generate_section_options(section_names)}
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-priority">🎯 Priority</label>
                <select id="filter-priority">
                    <option value="all">All Priorities</option>
                    {generate_priority_options(priorities, priority_labels)}
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-search">🔍 Search</label>
                <select id="filter-search" style="border: 2px solid #667eea;">
                    <option value="">Search tasks...</option>
                </select>
            </div>
        </div>

        <div class="stats">
            <div class="stat-item">
                <span class="stat-label">Total Tasks:</span>
                <span class="stat-value" id="total-tasks">{len(tasks)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Visible:</span>
                <span class="stat-value" id="visible-tasks">{len(tasks)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Sections:</span>
                <span class="stat-value">{len(section_names)}</span>
            </div>
        </div>

        <div id="tasks-container"></div>
    </div>

    <script>
        const allTasks = {json.dumps(tasks, ensure_ascii=False, indent=2)};
        const priorityColors = {json.dumps(priority_colors)};
        const priorityLabels = {json.dumps(priority_labels)};

        // Replace select with input for search
        const searchSelect = document.getElementById('filter-search');
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.id = 'filter-search';
        searchInput.placeholder = 'Search tasks...';
        searchInput.style.cssText = searchSelect.style.cssText;
        searchSelect.parentNode.replaceChild(searchInput, searchSelect);

        function renderTasks(tasks) {{
            const container = document.getElementById('tasks-container');

            if (tasks.length === 0) {{
                container.innerHTML = '<div class="no-results">No tasks match the current filters</div>';
                return;
            }}

            // Group tasks by section
            const tasksBySection = {{}};
            tasks.forEach(task => {{
                if (!tasksBySection[task.section]) {{
                    tasksBySection[task.section] = [];
                }}
                tasksBySection[task.section].push(task);
            }});

            // Render each section
            let html = '';
            Object.keys(tasksBySection).sort().forEach(section => {{
                const sectionTasks = tasksBySection[section];
                html += `
                    <div class="section-group">
                        <div class="section-header">
                            <span>${{section}}</span>
                            <span class="section-count">${{sectionTasks.length}}</span>
                        </div>
                        <div class="tasks-container">
                            ${{sectionTasks.map(task => renderTask(task)).join('')}}
                        </div>
                    </div>
                `;
            }});

            container.innerHTML = html;

            // Update stats
            document.getElementById('visible-tasks').textContent = tasks.length;
        }}

        function renderTask(task) {{
            const priorityColor = priorityColors[task.priority] || '#808080';
            const priorityLabel = priorityLabels[task.priority] || `P${{task.priority}}`;
            const isSubtask = task.indent > 1;
            const hasDescription = task.description && task.description.trim().length > 0;
            const hasNotes = task.notes && task.notes.length > 0;

            let metaItems = [];
            if (task.deadline) {{
                metaItems.push(`<span class="meta-item deadline"><span class="meta-icon">⏰</span>${{task.deadline}}</span>`);
            }}
            if (task.responsible) {{
                metaItems.push(`<span class="meta-item"><span class="meta-icon">👤</span>${{task.responsible.split('(')[0].trim()}}</span>`);
            }}
            if (hasNotes) {{
                metaItems.push(`<span class="meta-item"><span class="meta-icon">💬</span>${{task.notes.length}} note(s)</span>`);
            }}

            return `
                <div class="task-card ${{isSubtask ? 'subtask' : ''}}" data-task-id="${{task.id}}">
                    <div class="task-header">
                        <span class="priority-badge" style="background: ${{priorityColor}}">${{priorityLabel}}</span>
                        <div class="task-content">${{task.content}}</div>
                    </div>
                    ${{metaItems.length > 0 ? `<div class="task-meta">${{metaItems.join('')}}</div>` : ''}}
                    ${{hasDescription ? `
                        <span class="description-toggle" onclick="toggleDescription(${{task.id}})">
                            📝 Show Description
                        </span>
                        <div class="task-description" id="desc-${{task.id}}">${{task.description}}</div>
                    ` : ''}}
                    ${{hasNotes ? `
                        <span class="description-toggle" onclick="toggleNotes(${{task.id}})" style="margin-left: 15px;">
                            💬 Show Notes (${{task.notes.length}})
                        </span>
                        <div class="task-notes" id="notes-${{task.id}}">
                            ${{task.notes.map(note => `
                                <div class="note-item">
                                    <div class="note-content">${{note.content}}</div>
                                    <div class="note-meta">${{note.author.split('(')[0].trim()}} • ${{note.date ? new Date(note.date).toLocaleDateString() : ''}}</div>
                                </div>
                            `).join('')}}
                        </div>
                    ` : ''}}
                </div>
            `;
        }}

        function toggleDescription(taskId) {{
            const desc = document.getElementById(`desc-${{taskId}}`);
            const toggle = desc.previousElementSibling;
            desc.classList.toggle('expanded');
            toggle.textContent = desc.classList.contains('expanded') ? '📝 Hide Description' : '📝 Show Description';
        }}

        function toggleNotes(taskId) {{
            const notes = document.getElementById(`notes-${{taskId}}`);
            const toggle = notes.previousElementSibling;
            notes.classList.toggle('expanded');
            const count = allTasks.find(t => t.id === taskId).notes.length;
            toggle.textContent = notes.classList.contains('expanded') ? `💬 Hide Notes (${{count}})` : `💬 Show Notes (${{count}})`;
        }}

        function applyFilters() {{
            const sectionFilter = document.getElementById('filter-section').value;
            const priorityFilter = document.getElementById('filter-priority').value;
            const searchQuery = document.getElementById('filter-search').value.toLowerCase();

            const filtered = allTasks.filter(task => {{
                if (sectionFilter !== 'all' && task.section !== sectionFilter) return false;
                if (priorityFilter !== 'all' && task.priority !== parseInt(priorityFilter)) return false;
                if (searchQuery && !task.content.toLowerCase().includes(searchQuery) &&
                    !task.description.toLowerCase().includes(searchQuery)) return false;
                return true;
            }});

            renderTasks(filtered);
        }}

        // Event listeners
        document.getElementById('filter-section').addEventListener('change', applyFilters);
        document.getElementById('filter-priority').addEventListener('change', applyFilters);
        document.getElementById('filter-search').addEventListener('input', applyFilters);

        // Initial render
        renderTasks(allTasks);
    </script>
</body>
</html>'''

    return html

def generate_section_options(sections):
    return '\n'.join(f'<option value="{section}">{section}</option>' for section in sections)

def generate_priority_options(priorities, priority_labels):
    return '\n'.join(f'<option value="{p}">{priority_labels.get(p, f"P{p}")}</option>' for p in priorities)

if __name__ == '__main__':
    print("=" * 60)
    print("Portfolio Management Portal Generator")
    print("=" * 60)
    print()

    # Parse CSV
    print("Parsing PORTFOLIO.csv...")
    sections, tasks = parse_csv('PORTFOLIO.csv')
    print(f"Found {len(sections)} sections")
    print(f"Found {len(tasks)} tasks")
    print()

    # Generate HTML
    print("Generating HTML portal...")
    html = generate_html(sections, tasks)

    # Write HTML file
    output_file = 'portfolio_portal.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Portal created: {output_file}")
    print()
    print("=" * 60)
    print("DONE! Open portfolio_portal.html in your browser")
    print("=" * 60)
