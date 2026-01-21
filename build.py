#!/usr/bin/env python3
"""
PlatGovNet HTML Builder

Run this script whenever you update summary.md or conference_data.csv
It will regenerate platgovnet_conference.html with the latest content.

Usage: python3 build.py
"""

import re
import sys
import os
import csv
import json

def build_html():
    # Check if files exist
    if not os.path.exists('summary.md'):
        print("ERROR: summary.md not found in current directory")
        sys.exit(1)
    if not os.path.exists('conference_data.csv'):
        print("ERROR: conference_data.csv not found in current directory")
        sys.exit(1)
    
    print("Loading files...")
    
    # Read markdown
    with open('summary.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Read and parse CSV with auto-detection
    print("Parsing CSV...")
    with open('conference_data.csv', 'r', encoding='utf-8') as f:
        # Read sample to detect delimiter
        sample = f.read(2048)
        f.seek(0)
        
        # Auto-detect delimiter
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            print(f"Detected CSV delimiter: '{delimiter}'")
        except:
            delimiter = ','
            print("Using default delimiter: ','")
        
        # Parse CSV
        reader = csv.DictReader(f, delimiter=delimiter)
        csv_data = list(reader)
    
    print(f"Loaded {len(csv_data)} presentations from CSV")
    
    # Organize data by year and panel
    data_by_year = {}
    all_themes = set()
    
    for row in csv_data:
        year = row.get('Year', '').strip()
        panel = row.get('Panel', '').strip()
        theme = row.get('theme', '').strip()
        person = row.get('Person', '').strip()
        presentation = row.get('Presentation', '').strip()
        
        if not year or not panel:
            continue
            
        if year not in data_by_year:
            data_by_year[year] = {}
        
        if panel not in data_by_year[year]:
            data_by_year[year][panel] = {
                'theme': theme,
                'presentations': []
            }
        
        data_by_year[year][panel]['presentations'].append({
            'person': person,
            'presentation': presentation
        })
        
        if theme:
            all_themes.add(theme)
    
    print(f"Organized into {len(data_by_year)} years")
    print(f"Found {len(all_themes)} unique themes: {', '.join(sorted(all_themes))}")
    
    # Count panels
    total_panels = sum(len(panels) for panels in data_by_year.values())
    print(f"Total panels: {total_panels}")
    
    # Convert to JSON for embedding
    data_json = json.dumps(data_by_year)
    
    print("Processing markdown...")
    
    # Split markdown
    parts = md_content.split('# PlatGovNet2025 Summary')
    menu_section = parts[0]
    summary_section = '# PlatGovNet2025 Summary' + parts[1]
    
    # Extract menu
    menu_data = {'2021': '', '2023': '', '2025': ''}
    current_year = None
    for line in menu_section.split('\n'):
        if line.startswith('## '):
            current_year = line.replace('## ', '').strip()
        elif line.strip() and current_year and current_year in menu_data:
            if menu_data[current_year]:
                menu_data[current_year] += ' '
            menu_data[current_year] += line.strip()
    
    # REPLACE PANEL MARKERS BEFORE PROCESSING MARKDOWN
    # Create mapping of lowercase panel names to actual CSV panel names for 2025
    panel_name_map = {}
    if '2025' in data_by_year:
        for panel_name in data_by_year['2025'].keys():
            panel_name_map[panel_name.lower().strip()] = panel_name
    
    # Find and replace panel markers
    panel_markers = re.findall(r'\*\*\*([^\*]+)\*\*\*', summary_section)
    for panel in panel_markers:
        panel_normalized = panel.lower().strip()
        # Check if this panel exists in 2025 data
        if panel_normalized in panel_name_map:
            csv_panel_name = panel_name_map[panel_normalized]
            # Replace with a PLACEHOLDER that won't be affected by markdown processing
            placeholder = f'|||PANELLINK:{csv_panel_name.lower()}:{panel}|||'
            summary_section = summary_section.replace(f'***{panel}***', placeholder)
        else:
            # Just remove the asterisks if no matching panel
            summary_section = summary_section.replace(f'***{panel}***', panel)
    
    print(f"Found {len([p for p in panel_markers if p.lower().strip() in panel_name_map])} panel markers matching CSV panels")
    
    # Process summary to HTML
    def process_line(line):
        line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', line)
        line = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', line)
        line = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', line)
        return line
    
    html_lines = []
    for line in summary_section.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            html_lines.append(f'<h2>{process_line(line[2:])}</h2>')
        elif line.startswith('## '):
            html_lines.append(f'<h3>{process_line(line[3:])}</h3>')
        elif line.startswith('### '):
            html_lines.append(f'<h4>{process_line(line[4:])}</h4>')
        else:
            html_lines.append(f'<p>{process_line(line)}</p>')
    
    summary_html = '\n'.join(html_lines)
    
    # NOW convert placeholders to actual panel links
    placeholder_pattern = r'\|\|\|PANELLINK:([^:]+):([^|]+)\|\|\|'
    def replace_placeholder(match):
        panel_key = match.group(1)
        panel_display = match.group(2)
        return f'<span class="panel-link" data-panel="{panel_key}">{panel_display}</span>'
    
    summary_html = re.sub(placeholder_pattern, replace_placeholder, summary_html)
    
    # Escape for JavaScript embedding
    summary_escaped = summary_html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    themes_json = json.dumps(sorted(all_themes))
    
    print("Building HTML...")
    
    # Build complete HTML
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>PlatGovNet</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Crimson Text',serif;line-height:1.6;color:#333;background:#fff;padding:20px 20px 20px 260px;max-width:1600px;margin:0 auto;position:relative}}
h1{{font-size:2em;margin-bottom:40px;font-weight:600}}
.filter-section{{margin-bottom:40px;padding-bottom:30px;border-bottom:1px solid #ddd}}
.filter-section strong{{display:block;margin-bottom:10px;font-size:1.1em}}
.theme-tag{{display:inline-block;padding:5px 12px;margin:3px;background:#f5f5f5;border-radius:3px;cursor:pointer;font-size:0.9em;transition:all 0.2s}}
.theme-tag:hover{{background:#e0e0e0}}
.theme-tag.active{{background:#333;color:white}}
.conference-map{{margin-bottom:60px}}
.year-section{{margin-bottom:50px;display:grid;grid-template-columns:400px 1fr;gap:40px;align-items:start}}
.year-left{{}}
.year-right{{}}
.year-header{{font-size:1.5em;font-weight:600;margin-bottom:15px}}
.year-summary{{font-size:0.95em;color:#555;line-height:1.5;margin:0;padding:0}}
.panels-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:20px;margin:calc(2.25em + 15px) 0 0 0;padding:0;align-items:start}}
.panel-item{{position:relative;transition:opacity 0.3s;margin:0;padding:0}}
.panel-item:first-child{{margin-top:0}}
.panel-item.greyed-out{{opacity:0.2}}
.panel-name{{font-weight:600;margin:0 0 8px 0;padding:0;display:block;font-size:0.95em;line-height:1.5}}
.panel-name.clickable{{cursor:pointer;color:#2c5aa0}}
.panel-name.clickable:hover{{text-decoration:underline}}
.presentation-dots{{display:flex;flex-wrap:wrap;gap:5px}}
.dot{{width:10px;height:10px;background:black;border-radius:50%;cursor:pointer;position:relative;transition:transform 0.2s}}
.dot:hover{{transform:scale(1.3)}}
.tooltip{{position:absolute;bottom:15px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.9);color:white;padding:10px 12px;border-radius:4px;font-size:0.85em;z-index:1000;pointer-events:none;opacity:0;transition:opacity 0.2s;line-height:1.5;min-width:300px;max-width:400px;white-space:normal}}
.tooltip .tooltip-name{{font-weight:600;display:block;margin-bottom:3px}}
.tooltip .tooltip-presentation{{display:block;font-size:0.95em;opacity:0.9}}
.dot:hover .tooltip{{opacity:1}}
.summary-container{{position:relative;margin-top:60px}}
.floating-sidebar{{position:fixed;left:30px;top:50vh;transform:translateY(-50%);width:200px;opacity:0;transition:opacity 0.3s;height:fit-content;max-height:80vh;overflow-y:auto}}
.floating-sidebar.visible{{opacity:1}}
.floating-sidebar .sidebar-panel{{padding:8px 0;cursor:pointer;color:#2c5aa0;font-size:0.9em;border-bottom:1px solid #f0f0f0;transition:all 0.2s}}
.floating-sidebar .sidebar-panel:hover{{padding-left:5px;background:#f5f5f5}}
.summary-main{{max-width:800px}}
.summary-section{{margin-top:0}}
.summary-section h2{{font-size:1.8em;margin-bottom:20px;font-weight:600}}
.summary-section h3{{font-size:1.3em;margin-top:30px;margin-bottom:15px;font-weight:600}}
.summary-section h4{{font-size:1.1em;margin-top:25px;margin-bottom:12px;font-weight:600;font-style:italic}}
.summary-section p{{margin-bottom:15px;line-height:1.7}}
.summary-section a{{color:#2c5aa0;text-decoration:none;border-bottom:1px solid #2c5aa0}}
.summary-section a:hover{{background:#f0f5ff}}
.summary-section em{{font-style:italic}}
.summary-section strong{{font-weight:600}}
.panel-link{{color:#2c5aa0;cursor:pointer;position:relative;border-bottom:1px dotted #2c5aa0}}
.panel-link:hover{{background:#f0f5ff}}
.panel-participants{{position:absolute;bottom:100%;left:0;background:rgba(0,0,0,0.9);color:white;padding:10px 12px;border-radius:4px;font-size:0.85em;opacity:0;pointer-events:none;transition:opacity 0.2s;z-index:1000;margin-bottom:5px;min-width:300px;max-width:400px;line-height:1.5}}
.panel-participants .participant-item{{margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.2)}}
.panel-participants .participant-item:last-child{{margin-bottom:0;padding-bottom:0;border-bottom:none}}
.panel-participants .participant-name{{font-weight:600;display:block;margin-bottom:2px}}
.panel-participants .participant-presentation{{display:block;font-size:0.95em;opacity:0.9}}
.panel-link:hover .panel-participants{{opacity:1}}
.keynote-section{{background:#f9f9f9;padding:20px 25px;margin:30px 0;border-left:4px solid #2c5aa0}}
.keynote-section p{{margin-bottom:12px}}
</style>
</head><body>
<h1>PlatGovNet, then and now</h1>
<div class="filter-section"><strong>Filter by theme (applies to all years):</strong><div id="global-themes"></div></div>
<div class="conference-map">
<div class="year-section"><div class="year-left"><div class="year-header">2021</div><div class="year-summary">{menu_data['2021']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2021"></div></div></div>
<div class="year-section"><div class="year-left"><div class="year-header">2023</div><div class="year-summary">{menu_data['2023']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2023"></div></div></div>
<div class="year-section"><div class="year-left"><div class="year-header">2025</div><div class="year-summary">{menu_data['2025']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2025"></div></div></div>
</div>
<div class="floating-sidebar" id="floating-sidebar"><div id="sidebar-panels"></div></div>
<div class="summary-container">
<div class="summary-main"><div class="summary-section" id="summary-2025">{summary_escaped}</div></div>
</div>
<script>
// Data is already parsed by Python and embedded as JSON
const dataByYear={data_json};
const allThemes={themes_json};

// Render theme filters
const globalThemesContainer=document.getElementById('global-themes');
allThemes.forEach(theme=>{{const tag=document.createElement('span');tag.className='theme-tag';tag.textContent=theme;tag.dataset.theme=theme;tag.addEventListener('click',()=>toggleGlobalTheme(theme,tag));globalThemesContainer.appendChild(tag)}});

// Render panels for each year
function renderYear(year){{const panels=dataByYear[year];if(!panels)return;const container=document.getElementById(`panels-${{year}}`);Object.keys(panels).forEach(panelName=>{{const panel=panels[panelName];const panelDiv=document.createElement('div');panelDiv.className='panel-item';panelDiv.dataset.theme=panel.theme;panelDiv.dataset.panel=panelName.toLowerCase();panelDiv.dataset.year=year;const nameDiv=document.createElement('div');nameDiv.className='panel-name';if(year==='2025'){{nameDiv.classList.add('clickable');nameDiv.onclick=()=>{{const links=document.querySelectorAll(`.panel-link[data-panel="${{panelName.toLowerCase()}}"]`);if(links[0]){{links[0].scrollIntoView({{behavior:'smooth',block:'center'}});links[0].style.background='#fff8dc';setTimeout(()=>links[0].style.background='',2000)}}}}}}nameDiv.textContent=panelName;const dotsDiv=document.createElement('div');dotsDiv.className='presentation-dots';panel.presentations.forEach(pres=>{{const dot=document.createElement('div');dot.className='dot';const tooltip=document.createElement('div');tooltip.className='tooltip';const nameSpan=document.createElement('span');nameSpan.className='tooltip-name';nameSpan.textContent=pres.person;const presSpan=document.createElement('span');presSpan.className='tooltip-presentation';presSpan.textContent=pres.presentation;tooltip.appendChild(nameSpan);tooltip.appendChild(presSpan);dot.appendChild(tooltip);dotsDiv.appendChild(dot)}});panelDiv.appendChild(nameDiv);panelDiv.appendChild(dotsDiv);container.appendChild(panelDiv)}})}}

function toggleGlobalTheme(theme,el){{const panels=document.querySelectorAll('.panel-item');const tags=document.querySelectorAll('.theme-tag');const wasActive=el.classList.contains('active');if(wasActive){{el.classList.remove('active');panels.forEach(p=>p.classList.remove('greyed-out'))}}else{{tags.forEach(t=>t.classList.remove('active'));el.classList.add('active');panels.forEach(p=>{{if(p.dataset.theme!==theme)p.classList.add('greyed-out');else p.classList.remove('greyed-out')}})}}}};

function setupPanelLinks(){{const links=document.querySelectorAll('.panel-link');links.forEach(link=>{{const panelName=link.dataset.panel;const panel2025=dataByYear['2025']?dataByYear['2025'][panelName]:null;if(panel2025){{const div=document.createElement('div');div.className='panel-participants';panel2025.presentations.forEach(pres=>{{const item=document.createElement('div');item.className='participant-item';const name=document.createElement('span');name.className='participant-name';name.textContent=pres.person;const pres2=document.createElement('span');pres2.className='participant-presentation';pres2.textContent=pres.presentation;item.appendChild(name);item.appendChild(pres2);div.appendChild(item)}});link.appendChild(div)}}link.onclick=(e)=>{{e.preventDefault();const el=document.querySelector(`[data-panel="${{panelName}}"][data-year="2025"]`);if(el){{el.scrollIntoView({{behavior:'smooth',block:'center'}});el.style.background='#fff8dc';setTimeout(()=>el.style.background='',2000)}}}}}})}}

function setupFloatingSidebar(){{const sidebar=document.getElementById('floating-sidebar');const sidebarPanels=document.getElementById('sidebar-panels');const summarySection=document.getElementById('summary-2025');const panels2025=dataByYear['2025'];if(!panels2025)return;Object.keys(panels2025).forEach(panelName=>{{const div=document.createElement('div');div.className='sidebar-panel';div.textContent=panelName;div.onclick=()=>{{const links=document.querySelectorAll(`.panel-link[data-panel="${{panelName.toLowerCase()}}"]`);if(links[0]){{links[0].scrollIntoView({{behavior:'smooth',block:'center'}});links[0].style.background='#fff8dc';setTimeout(()=>links[0].style.background='',2000)}}}};sidebarPanels.appendChild(div)}});const observer=new IntersectionObserver(entries=>{{entries.forEach(entry=>{{if(entry.isIntersecting)sidebar.classList.add('visible');else sidebar.classList.remove('visible')}})}},{{threshold:0.1}});observer.observe(summarySection)}}

renderYear('2021');renderYear('2023');renderYear('2025');setupPanelLinks();setupFloatingSidebar();
</script>
</body></html>'''
    
    # Write HTML
    with open('platgovnet_conference.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("\n✓ SUCCESS! platgovnet_conference.html has been regenerated")
    print(f"✓ Embedded data for {total_panels} panels")
    print(f"✓ Embedded {len(summary_html)} chars of summary HTML")
    print(f"✓ Found {len(panel_markers)} linked panels in text")
    print("\nYou can now open platgovnet_conference.html in your browser!")

if __name__ == '__main__':
    build_html()
