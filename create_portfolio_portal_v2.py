"""
Smart Portfolio Management Portal Generator v2
- Expandable sections and hierarchical tasks
- Gantt timeline view
"""
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re

def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None

    date_str = date_str.strip()

    # Handle "today"
    if date_str.lower() == 'today':
        return datetime.now().strftime('%Y-%m-%d')

    # Try ISO format first
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        pass

    # Try common formats
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue

    return None

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

                # Parse priority - handle empty/None values
                content = row.get('CONTENT', '').strip()
                priority_str = row.get('PRIORITY', '').strip()
                if priority_str == '' or priority_str is None:
                    priority = 4  # Default to lowest (P4)
                else:
                    try:
                        priority = int(priority_str)
                    except:
                        priority = 4

                task = {
                    'id': last_task_id,
                    'content': content,
                    'description': row.get('DESCRIPTION', '').strip(),
                    'priority': priority,
                    'indent': int(row.get('INDENT', 1)),
                    'section': current_section['name'] if current_section else 'No Section',
                    'author': row.get('AUTHOR', '').strip(),
                    'responsible': row.get('RESPONSIBLE', '').strip(),
                    'date': parse_date(row.get('DATE', '')),
                    'deadline': parse_date(row.get('DEADLINE', '')),
                    'deadline_lang': row.get('DEADLINE_LANG', '').strip(),
                    'notes': [],
                    'children': []
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
    task_stack = []

    for task in tasks:
        task['children'] = []
        indent = task['indent']

        while len(task_stack) >= indent:
            task_stack.pop()

        if indent == 1:
            root_tasks.append(task)
            task_stack = [task]
        else:
            if task_stack:
                parent = task_stack[-1]
                parent['children'].append(task)
            task_stack.append(task)

    return root_tasks

def generate_html(sections, tasks):
    """Generate enhanced HTML portal"""

    section_names = sorted(set(task['section'] for task in tasks))
    priorities = sorted(set(task['priority'] for task in tasks), reverse=True)

    # Extract unique responsible persons (clean up names)
    persons = set()
    for task in tasks:
        resp = task.get('responsible', '').strip()
        if resp:
            # Extract name without ID (e.g., "Arvydas (43613934)" -> "Arvydas")
            person_name = resp.split('(')[0].strip() if '(' in resp else resp
            persons.add(person_name)
    persons = sorted(persons)

    priority_labels = {
        1: 'P1 (Highest)',
        2: 'P2 (High)',
        3: 'P3 (Medium)',
        4: 'P4 (Low)'
    }

    priority_colors = {
        1: '#d1453b',
        2: '#eb8909',
        3: '#246fe0',
        4: '#808080'
    }

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Management Portal v2</title>
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
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .view-switcher {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}

        .view-btn {{
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .view-btn:hover {{
            background: #f0f4ff;
        }}

        .view-btn.active {{
            background: #667eea;
            color: white;
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

        .filter-group select, .filter-group input {{
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            background: white;
            transition: all 0.2s;
        }}

        .filter-group select:hover, .filter-group input:hover {{
            border-color: #667eea;
        }}

        .filter-group select:focus, .filter-group input:focus {{
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
            flex-wrap: wrap;
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

        /* List View Styles */
        .list-view {{
            display: block;
        }}

        .timeline-view {{
            display: none;
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
            cursor: pointer;
            user-select: none;
        }}

        .section-header:hover {{
            opacity: 0.95;
        }}

        .section-toggle {{
            font-size: 14px;
            transition: transform 0.3s;
        }}

        .section-toggle.collapsed {{
            transform: rotate(-90deg);
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
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}

        .tasks-container.collapsed {{
            max-height: 0 !important;
            border: none;
            box-shadow: none;
        }}

        .task-card {{
            border-bottom: 1px solid #f0f0f0;
            padding: 16px 20px;
            transition: all 0.2s;
        }}

        .task-card:last-child {{
            border-bottom: none;
        }}

        .task-card:hover {{
            background: #f8f9ff;
        }}

        .task-header {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 8px;
            cursor: pointer;
        }}

        .task-expand-btn {{
            font-size: 14px;
            color: #667eea;
            font-weight: bold;
            user-select: none;
            transition: transform 0.2s;
            min-width: 20px;
        }}

        .task-expand-btn.collapsed {{
            transform: rotate(-90deg);
        }}

        .task-expand-btn.no-children {{
            opacity: 0;
            cursor: default;
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
            margin-left: 32px;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .description-toggle {{
            color: #667eea;
            font-size: 13px;
            font-weight: 600;
            margin-top: 8px;
            margin-left: 32px;
            display: inline-block;
            cursor: pointer;
        }}

        .description-toggle:hover {{
            text-decoration: underline;
        }}

        .task-description, .task-notes {{
            display: none;
            margin-top: 12px;
            margin-left: 32px;
            padding: 12px;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            font-size: 14px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .task-description {{
            background: #f8f9fa;
        }}

        .task-notes {{
            background: #fff9e6;
            border-left-color: #eb8909;
        }}

        .task-description.expanded, .task-notes.expanded {{
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
            margin-bottom: 5px;
        }}

        .note-meta {{
            font-size: 11px;
            color: #888;
        }}

        .subtasks-container {{
            margin-left: 40px;
            margin-top: 8px;
            border-left: 3px solid #e0e0e0;
            padding-left: 10px;
            display: none;
        }}

        .subtasks-container.expanded {{
            display: block;
        }}

        .deadline {{
            color: #d1453b;
            font-weight: 600;
        }}

        /* Timeline/Gantt View Styles */
        .gantt-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            padding: 20px;
            overflow-x: auto;
        }}

        .gantt-header {{
            margin-bottom: 20px;
        }}

        .gantt-chart {{
            position: relative;
            min-width: 100%;
        }}

        .gantt-timeline {{
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 10px;
            padding-bottom: 10px;
        }}

        .gantt-month {{
            flex: 1;
            text-align: center;
            font-weight: 600;
            color: #667eea;
            font-size: 14px;
            padding: 5px;
            border-right: 1px solid #f0f0f0;
        }}

        .gantt-month:last-child {{
            border-right: none;
        }}

        .gantt-row {{
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f5f5f5;
            position: relative;
        }}

        .gantt-task-label {{
            width: 300px;
            padding-right: 20px;
            font-size: 14px;
            flex-shrink: 0;
        }}

        .gantt-task-bar {{
            position: absolute;
            left: 300px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            color: white;
            font-size: 11px;
            display: flex;
            align-items: center;
            padding: 0 8px;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

            .subtasks-container {{
                margin-left: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Portfolio Management Portal v2</h1>
            <p>Smart task management with timeline visualization</p>
        </div>
    </div>

    <div class="container">
        <div class="view-switcher">
            <button class="view-btn active" onclick="switchView('list')">List View</button>
            <button class="view-btn" onclick="switchView('timeline')">Timeline View</button>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label for="filter-status">Status</label>
                <select id="filter-status">
                    <option value="all">All Tasks</option>
                    <option value="with-dates" selected>Active (With Dates)</option>
                    <option value="no-dates">Backlog (No Dates)</option>
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-section">Section</label>
                <select id="filter-section">
                    <option value="all">All Sections</option>
                    {generate_section_options(section_names)}
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-priority">Priority</label>
                <select id="filter-priority">
                    <option value="all">All Priorities</option>
                    {generate_priority_options(priorities, priority_labels)}
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-person">Person</label>
                <select id="filter-person">
                    <option value="all">All People</option>
                    {generate_person_options(persons)}
                </select>
            </div>

            <div class="filter-group">
                <label for="filter-search">Search</label>
                <input type="text" id="filter-search" placeholder="Search tasks...">
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
            <div class="stat-item">
                <span class="stat-label">With Deadlines:</span>
                <span class="stat-value">{sum(1 for t in tasks if t.get('deadline'))}</span>
            </div>
        </div>

        <div id="list-view" class="list-view"></div>
        <div id="timeline-view" class="timeline-view"></div>
    </div>

    <script>
        const allTasks = {json.dumps(tasks, ensure_ascii=False, indent=2)};
        const priorityColors = {json.dumps(priority_colors)};
        const priorityLabels = {json.dumps(priority_labels)};
        let currentView = 'list';

        function buildHierarchy(tasks) {{
            const taskMap = {{}};
            tasks.forEach(t => {{
                taskMap[t.id] = {{ ...t, children: [] }};
            }});

            const roots = [];
            const sortedTasks = [...tasks].sort((a, b) => a.id - b.id);

            let lastAtLevel = {{}};
            sortedTasks.forEach(task => {{
                const t = taskMap[task.id];
                if (task.indent === 1) {{
                    roots.push(t);
                    lastAtLevel[1] = t;
                }} else {{
                    const parent = lastAtLevel[task.indent - 1];
                    if (parent) {{
                        parent.children.push(t);
                    }} else {{
                        roots.push(t);
                    }}
                    lastAtLevel[task.indent] = t;
                }}
            }});

            return roots;
        }}

        function switchView(view) {{
            currentView = view;
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            if (view === 'list') {{
                document.getElementById('list-view').style.display = 'block';
                document.getElementById('timeline-view').style.display = 'none';
            }} else {{
                document.getElementById('list-view').style.display = 'none';
                document.getElementById('timeline-view').style.display = 'block';
                renderTimeline(getFilteredTasks());
            }}
        }}

        function renderListView(tasks) {{
            const container = document.getElementById('list-view');

            if (tasks.length === 0) {{
                container.innerHTML = '<div class="no-results">No tasks match the current filters</div>';
                return;
            }}

            const tasksBySection = {{}};
            tasks.forEach(task => {{
                if (!tasksBySection[task.section]) {{
                    tasksBySection[task.section] = [];
                }}
                tasksBySection[task.section].push(task);
            }});

            let html = '';
            Object.keys(tasksBySection).sort().forEach(section => {{
                const sectionTasks = tasksBySection[section];
                const hierarchy = buildHierarchy(sectionTasks);

                // Sort root tasks by priority (1=highest first)
                hierarchy.sort((a, b) => a.priority - b.priority);

                html += `
                    <div class="section-group">
                        <div class="section-header" onclick="toggleSection(this)">
                            <span class="section-toggle">▼</span>
                            <span>${{section}}</span>
                            <span class="section-count">${{sectionTasks.length}}</span>
                        </div>
                        <div class="tasks-container" style="max-height: 10000px;">
                            ${{hierarchy.map(task => renderTaskHierarchy(task)).join('')}}
                        </div>
                    </div>
                `;
            }});

            container.innerHTML = html;
            document.getElementById('visible-tasks').textContent = tasks.length;
        }}

        function renderTaskHierarchy(task, level = 0) {{
            const priorityColor = priorityColors[task.priority] || '#808080';
            const priorityLabel = priorityLabels[task.priority] || `P${{task.priority}}`;
            const hasChildren = task.children && task.children.length > 0;
            const hasDescription = task.description && task.description.trim().length > 0;
            const hasNotes = task.notes && task.notes.length > 0;

            let metaItems = [];
            if (task.deadline) {{
                metaItems.push(`<span class="meta-item deadline">⏰ ${{task.deadline}}</span>`);
            }}
            if (task.date && task.date !== task.deadline) {{
                metaItems.push(`<span class="meta-item">📅 ${{task.date}}</span>`);
            }}
            if (task.responsible) {{
                metaItems.push(`<span class="meta-item">👤 ${{task.responsible.split('(')[0].trim()}}</span>`);
            }}
            if (hasNotes) {{
                metaItems.push(`<span class="meta-item">💬 ${{task.notes.length}} note(s)</span>`);
            }}

            let html = `
                <div class="task-card" data-task-id="${{task.id}}">
                    <div class="task-header" onclick="toggleTaskChildren(${{task.id}})">
                        <span class="task-expand-btn ${{!hasChildren ? 'no-children' : ''}}" id="expand-${{task.id}}">▼</span>
                        <span class="priority-badge" style="background: ${{priorityColor}}">${{priorityLabel}}</span>
                        <div class="task-content">${{task.content}}</div>
                    </div>
                    ${{metaItems.length > 0 ? `<div class="task-meta">${{metaItems.join('')}}</div>` : ''}}
                    ${{hasDescription ? `
                        <span class="description-toggle" onclick="event.stopPropagation(); toggleDescription(${{task.id}})">
                            📝 Show Description
                        </span>
                        <div class="task-description" id="desc-${{task.id}}">${{task.description}}</div>
                    ` : ''}}
                    ${{hasNotes ? `
                        <span class="description-toggle" onclick="event.stopPropagation(); toggleNotes(${{task.id}})" style="margin-left: 15px;">
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
                    ${{hasChildren ? `
                        <div class="subtasks-container" id="subtasks-${{task.id}}">
                            ${{task.children.map(child => renderTaskHierarchy(child, level + 1)).join('')}}
                        </div>
                    ` : ''}}
                </div>
            `;

            return html;
        }}

        function toggleSection(header) {{
            const container = header.nextElementSibling;
            const toggle = header.querySelector('.section-toggle');

            if (container.classList.contains('collapsed')) {{
                container.classList.remove('collapsed');
                container.style.maxHeight = '10000px';
                toggle.classList.remove('collapsed');
            }} else {{
                container.classList.add('collapsed');
                container.style.maxHeight = '0';
                toggle.classList.add('collapsed');
            }}
        }}

        function toggleTaskChildren(taskId) {{
            const subtasks = document.getElementById(`subtasks-${{taskId}}`);
            const expandBtn = document.getElementById(`expand-${{taskId}}`);

            if (!subtasks) return;

            if (subtasks.classList.contains('expanded')) {{
                subtasks.classList.remove('expanded');
                expandBtn.classList.add('collapsed');
            }} else {{
                subtasks.classList.add('expanded');
                expandBtn.classList.remove('collapsed');
            }}
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

        let timelineViewMode = 'months'; // 'months' or 'quarters'

        function renderTimeline(tasks) {{
            const container = document.getElementById('timeline-view');

            if (tasks.length === 0) {{
                container.innerHTML = '<div class="no-results">No tasks match the current filters</div>';
                return;
            }}

            // Build hierarchy for all tasks
            const tasksBySection = {{}};
            tasks.forEach(task => {{
                if (!tasksBySection[task.section]) {{
                    tasksBySection[task.section] = [];
                }}
                tasksBySection[task.section].push(task);
            }});

            // Find date range from tasks with dates
            const tasksWithDates = tasks.filter(t => t.date || t.deadline);
            let minDate, maxDate, totalDays, timePeriods = [];

            if (tasksWithDates.length > 0) {{
                const dates = tasksWithDates.flatMap(t => [t.date, t.deadline]).filter(Boolean);
                minDate = new Date(Math.min(...dates.map(d => new Date(d))));
                maxDate = new Date(Math.max(...dates.map(d => new Date(d))));

                // Round to start/end of month
                minDate = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
                maxDate = new Date(maxDate.getFullYear(), maxDate.getMonth() + 1, 0);
                totalDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);

                // Generate time periods based on view mode
                if (timelineViewMode === 'quarters') {{
                    let current = new Date(minDate);
                    while (current <= maxDate) {{
                        const quarter = Math.floor(current.getMonth() / 3) + 1;
                        const year = current.getFullYear();
                        const qStart = new Date(year, (quarter - 1) * 3, 1);
                        const qEnd = new Date(year, quarter * 3, 0);
                        const daysInPeriod = Math.min((qEnd - current) / (1000 * 60 * 60 * 24), (maxDate - current) / (1000 * 60 * 60 * 24));
                        const widthPercent = (daysInPeriod / totalDays) * 100;

                        timePeriods.push({{
                            label: `Q${{quarter}} ${{year}}`,
                            width: widthPercent
                        }});

                        current = new Date(year, quarter * 3, 1);
                    }}
                }} else {{
                    let current = new Date(minDate);
                    while (current <= maxDate) {{
                        const nextMonth = new Date(current.getFullYear(), current.getMonth() + 1, 1);
                        const monthEnd = new Date(nextMonth - 1);
                        const daysInMonth = (Math.min(monthEnd, maxDate) - current) / (1000 * 60 * 60 * 24) + 1;
                        const widthPercent = (daysInMonth / totalDays) * 100;

                        timePeriods.push({{
                            label: current.toLocaleString('default', {{ month: 'short', year: 'numeric' }}),
                            width: widthPercent
                        }});

                        current = nextMonth;
                    }}
                }}
            }}

            let html = '<div class="gantt-container">';

            if (tasksWithDates.length > 0) {{
                // Calculate today's position
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const todayOffset = today >= minDate && today <= maxDate
                    ? ((today - minDate) / (1000 * 60 * 60 * 24)) / totalDays * 100
                    : -1;

                html += `
                    <div class="gantt-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h3>Project Timeline (${{tasks.length}} tasks, ${{tasksWithDates.length}} with dates)</h3>
                        <div style="display: flex; gap: 10px;">
                            <button onclick="toggleTimelineView('months')" style="padding: 8px 16px; background: ${{timelineViewMode === 'months' ? '#667eea' : '#e0e0e0'}}; color: ${{timelineViewMode === 'months' ? 'white' : '#333'}}; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">Months</button>
                            <button onclick="toggleTimelineView('quarters')" style="padding: 8px 16px; background: ${{timelineViewMode === 'quarters' ? '#667eea' : '#e0e0e0'}}; color: ${{timelineViewMode === 'quarters' ? 'white' : '#333'}}; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">Quarters</button>
                        </div>
                    </div>
                    <div class="gantt-chart" style="position: relative;">
                        <div style="display: flex;">
                            <div style="width: 50px; flex-shrink: 0;"></div>
                            <div class="gantt-timeline" style="display: flex; flex: 1; border-bottom: 2px solid #667eea; margin-bottom: 10px; position: relative;">
                                ${{timePeriods.map(p => `<div class="gantt-period" style="width: ${{p.width}}%; text-align: center; font-weight: 600; color: #667eea; font-size: 14px; padding: 5px; border-right: 1px solid #e0e0e0;">${{p.label}}</div>`).join('')}}
                            </div>
                        </div>
                        ${{todayOffset >= 0 ? `
                        <div style="position: absolute; left: calc(50px + ${{todayOffset}}%); top: 0; bottom: 0; width: 2px; background: #ff4444; z-index: 100; pointer-events: none;">
                            <div style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); background: #ff4444; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; white-space: nowrap;">TODAY</div>
                        </div>
                        ` : ''}}
                `;
            }} else {{
                html += `
                    <div class="gantt-header">
                        <h3>Project Structure (${{tasks.length}} tasks - no dates available)</h3>
                    </div>
                    <div class="gantt-chart">
                `;
            }}

            // Render each section with hierarchy
            Object.keys(tasksBySection).sort().forEach(section => {{
                const sectionTasks = tasksBySection[section];
                const hierarchy = buildHierarchy(sectionTasks);

                // Sort root tasks by priority (1=highest first)
                hierarchy.sort((a, b) => a.priority - b.priority);

                html += `
                    <div style="margin-top: 20px;">
                        <div style="font-weight: 600; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 4px; margin-bottom: 10px;">
                            ${{section}} (${{sectionTasks.length}})
                        </div>
                        ${{hierarchy.map(task => renderTimelineTask(task, 0, minDate, totalDays, tasksWithDates.length > 0)).join('')}}
                    </div>
                `;
            }});

            html += '</div></div>';
            container.innerHTML = html;
        }}

        function toggleTimelineView(mode) {{
            timelineViewMode = mode;
            applyFilters();
        }}

        function renderTimelineTask(task, level, minDate, totalDays, showBars) {{
            const indent = level * 15;
            const priorityColor = priorityColors[task.priority] || '#808080';
            const priorityLabel = priorityLabels[task.priority] || `P${{task.priority}}`;
            const hasChildren = task.children && task.children.length > 0;
            const hasDate = task.date || task.deadline;
            const isMainTask = level === 0;

            let barHtml = '';
            let dateTooltip = '';

            // Extract person info (available for all rendering modes)
            const personName = task.responsible ? task.responsible.split('(')[0].trim() : '';
            const personDisplay = personName ? `👤 ${{personName}}` : '';

            if (showBars && hasDate) {{
                const start = task.date ? new Date(task.date) : new Date(task.deadline);
                const end = task.deadline ? new Date(task.deadline) : new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
                const startOffset = ((start - minDate) / (1000 * 60 * 60 * 24)) / totalDays * 100;
                const duration = ((end - start) / (1000 * 60 * 60 * 24)) / totalDays * 100;

                const startStr = task.date || '';
                const endStr = task.deadline || '';
                dateTooltip = startStr && endStr && startStr !== endStr
                    ? `${{startStr}} → ${{endStr}}`
                    : (startStr || endStr);

                // For master tasks with long enough bars, put text inside the bar
                const isLongBar = duration >= 15; // Bar is at least 15% of timeline
                const putTextInside = isMainTask && isLongBar;

                if (putTextInside) {{
                    barHtml = `
                        <div style="position: absolute; left: ${{startOffset}}%; width: ${{Math.max(duration, 0.5)}}%; height: 28px; background: ${{priorityColor}}; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; align-items: center; padding: 0 10px; overflow: hidden;" title="${{dateTooltip}}">
                            <span style="color: white; font-size: 12px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${{task.content}}</span>
                            ${{personDisplay ? `<span style="color: rgba(255,255,255,0.85); font-size: 10px; margin-left: 10px; white-space: nowrap;">${{personDisplay}}</span>` : ''}}
                            <span style="color: rgba(255,255,255,0.9); font-size: 10px; margin-left: 8px; white-space: nowrap;">(${{dateTooltip}})</span>
                        </div>
                    `;
                }} else {{
                    barHtml = `
                        <div style="position: absolute; left: ${{startOffset}}%; width: ${{Math.max(duration, 0.5)}}%; height: 28px; background: ${{priorityColor}}; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" title="${{dateTooltip}}"></div>
                        <div style="position: absolute; left: ${{startOffset + Math.max(duration, 0.5) + 0.5}}%; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
                            <span style="background: ${{priorityColor}}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">${{priorityLabel}}</span>
                            <span style="font-size: 12px; font-weight: ${{isMainTask ? '700' : '500'}}; color: #333;">${{task.content}}</span>
                            ${{personDisplay ? `<span style="font-size: 10px; color: #666; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">${{personDisplay}}</span>` : ''}}
                            <span style="font-size: 11px; color: #666;">(${{dateTooltip}})</span>
                        </div>
                    `;
                }}
            }} else if (!showBars) {{
                barHtml = `
                    <div style="width: 100%; display: flex; align-items: center; gap: 8px; padding: 4px 8px;">
                        <span style="background: ${{priorityColor}}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600;">${{priorityLabel}}</span>
                        <span style="font-weight: ${{isMainTask ? '700' : '400'}};">${{task.content}}</span>
                        ${{personDisplay ? `<span style="font-size: 10px; color: #666; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">${{personDisplay}}</span>` : ''}}
                        <span style="color: #999; font-size: 12px; margin-left: 10px;">(no date)</span>
                    </div>
                `;
            }} else {{
                // Has showBars but no date for this task
                barHtml = `
                    <div style="display: flex; align-items: center; gap: 8px; padding: 4px 8px;">
                        <span style="background: ${{priorityColor}}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600;">${{priorityLabel}}</span>
                        <span style="font-weight: ${{isMainTask ? '700' : '400'}}; color: #666;">${{task.content}}</span>
                        ${{personDisplay ? `<span style="font-size: 10px; color: #666; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">${{personDisplay}}</span>` : ''}}
                        <span style="color: #999; font-size: 11px;">(no date)</span>
                    </div>
                `;
            }}

            const hasDescription = task.description && task.description.trim().length > 0;

            const rowStyle = `
                display: flex;
                align-items: center;
                padding: 6px 0;
                border-bottom: 1px solid #f5f5f5;
                position: relative;
                background: ${{isMainTask ? '#d8d8d8' : 'transparent'}};
            `;

            let html = `
                <div style="${{rowStyle}}">
                    <div style="width: 50px; flex-shrink: 0; display: flex; align-items: center; padding-left: ${{indent}}px;">
                        ${{hasChildren ? `<span class="task-expand-btn" onclick="toggleTimelineChildren(${{task.id}})" id="tl-expand-${{task.id}}" style="cursor: pointer; user-select: none; font-size: 14px;">▼</span>` : ''}}
                    </div>
                    <div style="flex: 1; position: relative; height: 36px; display: flex; align-items: center;">
                        ${{barHtml}}
                    </div>
                    ${{hasDescription ? `
                    <div style="width: 30px; display: flex; align-items: center; justify-content: center;">
                        <button onclick="toggleTimelineDescription(${{task.id}})" style="background: #667eea; color: white; border: none; border-radius: 3px; padding: 4px 8px; cursor: pointer; font-size: 11px;">📝</button>
                    </div>
                    ` : ''}}
                </div>
                ${{hasDescription ? `
                <div id="tl-desc-${{task.id}}" class="task-description" style="display: none; padding: 10px 20px 10px ${{50 + indent}}px; background: #f9f9f9; border-left: 3px solid ${{priorityColor}}; margin: 5px 0; font-size: 13px; color: #555; white-space: pre-wrap;">
                    ${{task.description}}
                </div>
                ` : ''}}
            `;

            if (hasChildren) {{
                // Sort children by deadline/date
                const sortedChildren = [...task.children].sort((a, b) => {{
                    const aDate = a.deadline || a.date;
                    const bDate = b.deadline || b.date;

                    // Tasks with dates come first
                    if (aDate && !bDate) return -1;
                    if (!aDate && bDate) return 1;
                    if (!aDate && !bDate) return 0;

                    // Sort by date
                    return new Date(aDate) - new Date(bDate);
                }});

                html += `
                    <div class="timeline-subtasks" id="tl-subtasks-${{task.id}}">
                        ${{sortedChildren.map(child => renderTimelineTask(child, level + 1, minDate, totalDays, showBars)).join('')}}
                    </div>
                `;
            }}

            return html;
        }}

        function toggleTimelineChildren(taskId) {{
            const subtasks = document.getElementById(`tl-subtasks-${{taskId}}`);
            const expandBtn = document.getElementById(`tl-expand-${{taskId}}`);

            if (!subtasks) return;

            if (subtasks.style.display === 'none') {{
                subtasks.style.display = 'block';
                expandBtn.textContent = '▼';
            }} else {{
                subtasks.style.display = 'none';
                expandBtn.textContent = '▶';
            }}
        }}

        function toggleTimelineDescription(taskId) {{
            const desc = document.getElementById(`tl-desc-${{taskId}}`);
            if (!desc) return;

            if (desc.style.display === 'none') {{
                desc.style.display = 'block';
            }} else {{
                desc.style.display = 'none';
            }}
        }}

        function getFilteredTasks() {{
            const statusFilter = document.getElementById('filter-status').value;
            const sectionFilter = document.getElementById('filter-section').value;
            const priorityFilter = document.getElementById('filter-priority').value;
            const personFilter = document.getElementById('filter-person').value;
            const searchQuery = document.getElementById('filter-search').value.toLowerCase();

            return allTasks.filter(task => {{
                // Status filter
                if (statusFilter === 'with-dates' && !task.date && !task.deadline) return false;
                if (statusFilter === 'no-dates' && (task.date || task.deadline)) return false;

                if (sectionFilter !== 'all' && task.section !== sectionFilter) return false;
                if (priorityFilter !== 'all' && task.priority !== parseInt(priorityFilter)) return false;

                // Person filter
                if (personFilter !== 'all') {{
                    const taskPerson = task.responsible ? task.responsible.split('(')[0].trim() : '';
                    if (taskPerson !== personFilter) return false;
                }}

                if (searchQuery && !task.content.toLowerCase().includes(searchQuery) &&
                    !task.description.toLowerCase().includes(searchQuery)) return false;
                return true;
            }});
        }}

        function applyFilters() {{
            const filtered = getFilteredTasks();
            if (currentView === 'list') {{
                renderListView(filtered);
            }} else {{
                renderTimeline(filtered);
            }}
        }}

        // Event listeners
        document.getElementById('filter-status').addEventListener('change', applyFilters);
        document.getElementById('filter-section').addEventListener('change', applyFilters);
        document.getElementById('filter-priority').addEventListener('change', applyFilters);
        document.getElementById('filter-person').addEventListener('change', applyFilters);
        document.getElementById('filter-search').addEventListener('input', applyFilters);

        // Initial render with filters applied (default: with-dates)
        renderListView(getFilteredTasks());
    </script>
</body>
</html>'''

    return html

def generate_section_options(sections):
    return '\n'.join(f'<option value="{section}">{section}</option>' for section in sections)

def generate_priority_options(priorities, priority_labels):
    return '\n'.join(f'<option value="{p}">{priority_labels.get(p, f"P{p}")}</option>' for p in priorities)

def generate_person_options(persons):
    return '\n'.join(f'<option value="{person}">{person}</option>' for person in persons)

if __name__ == '__main__':
    print("=" * 60)
    print("Portfolio Management Portal Generator v2")
    print("=" * 60)
    print()

    print("Parsing PORTFOLIO.csv...")
    sections, tasks = parse_csv('PORTFOLIO.csv')
    print(f"Found {len(sections)} sections")
    print(f"Found {len(tasks)} tasks")

    tasks_with_dates = sum(1 for t in tasks if t.get('date') or t.get('deadline'))
    print(f"Tasks with dates: {tasks_with_dates}")
    print()

    print("Generating enhanced HTML portal...")
    html = generate_html(sections, tasks)

    output_file = 'portfolio_portal.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Portal created: {output_file}")
    print()
    print("=" * 60)
    print("DONE! Features:")
    print("- Expandable sections and hierarchical tasks")
    print("- Timeline/Gantt view")
    print("- Enhanced filtering and search")
    print("=" * 60)
