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
                task = {
                    'id': last_task_id,
                    'content': row.get('CONTENT', '').strip(),
                    'description': row.get('DESCRIPTION', '').strip(),
                    'priority': int(row.get('PRIORITY', 1)),
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

    priority_labels = {
        4: 'P1 (Highest)',
        3: 'P2 (High)',
        2: 'P3 (Medium)',
        1: 'P4 (Low)'
    }

    priority_colors = {
        4: '#d1453b',
        3: '#eb8909',
        2: '#246fe0',
        1: '#808080'
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

        function renderTimeline(tasks) {{
            const container = document.getElementById('timeline-view');

            // Filter tasks with dates
            const tasksWithDates = tasks.filter(t => t.date || t.deadline);

            if (tasksWithDates.length === 0) {{
                container.innerHTML = '<div class="no-results">No tasks with dates to display in timeline view</div>';
                return;
            }}

            // Find date range
            const dates = tasksWithDates.flatMap(t => [t.date, t.deadline]).filter(Boolean);
            const minDate = new Date(Math.min(...dates.map(d => new Date(d))));
            const maxDate = new Date(Math.max(...dates.map(d => new Date(d))));

            // Add padding
            minDate.setMonth(minDate.getMonth() - 1);
            maxDate.setMonth(maxDate.getMonth() + 1);

            const totalDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);

            // Generate timeline header
            const months = [];
            let current = new Date(minDate);
            while (current <= maxDate) {{
                months.push(current.toLocaleString('default', {{ month: 'short', year: 'numeric' }}));
                current.setMonth(current.getMonth() + 1);
            }}

            let html = `
                <div class="gantt-container">
                    <div class="gantt-header">
                        <h3>Project Timeline (${{tasksWithDates.length}} tasks)</h3>
                    </div>
                    <div class="gantt-chart">
                        <div class="gantt-timeline">
                            ${{months.map(m => `<div class="gantt-month">${{m}}</div>`).join('')}}
                        </div>
                        ${{tasksWithDates.map(task => {{
                            const start = task.date ? new Date(task.date) : new Date(task.deadline);
                            const end = task.deadline ? new Date(task.deadline) : new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);

                            const startOffset = ((start - minDate) / (1000 * 60 * 60 * 24)) / totalDays * 100;
                            const duration = ((end - start) / (1000 * 60 * 60 * 24)) / totalDays * 100;

                            return `
                                <div class="gantt-row">
                                    <div class="gantt-task-label">${{task.content}}</div>
                                    <div class="gantt-task-bar" style="left: calc(300px + ${{startOffset}}%); width: ${{Math.max(duration, 2)}}%);">
                                        ${{task.deadline ? '⏰ ' + task.deadline : ''}}
                                    </div>
                                </div>
                            `;
                        }}).join('')}}
                    </div>
                </div>
            `;

            container.innerHTML = html;
        }}

        function getFilteredTasks() {{
            const sectionFilter = document.getElementById('filter-section').value;
            const priorityFilter = document.getElementById('filter-priority').value;
            const searchQuery = document.getElementById('filter-search').value.toLowerCase();

            return allTasks.filter(task => {{
                if (sectionFilter !== 'all' && task.section !== sectionFilter) return false;
                if (priorityFilter !== 'all' && task.priority !== parseInt(priorityFilter)) return false;
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
        document.getElementById('filter-section').addEventListener('change', applyFilters);
        document.getElementById('filter-priority').addEventListener('change', applyFilters);
        document.getElementById('filter-search').addEventListener('input', applyFilters);

        // Initial render
        renderListView(allTasks);
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
