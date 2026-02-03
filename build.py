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

    # Hardcoded year summaries (these don't change frequently)
    menu_data = {
        '2021': '',
        '2023': 'Since the onset of the COVID-19 pandemic, the global reliance on the services provided by a range of major online platform companies has skyrocketed. Online marketplaces, social networks, cloud providers, streaming services, and service delivery platforms all rake in record and increasing profits as they continue to embed themselves ever more deeply into public and private life. At the same time, dissatisfaction with the platform economy status quo is growing internationally. Across policy areas like content moderation, competition, labor law, and data protection, governments around the world are developing new rules to tackle troubling forms of outsized political, cultural, and infrastructural platform power.',
        '2025': 'A changing mix of competing platform companies faced with various efforts to regulate, influence, or control them and their offers has become an ever more central feature of many societies. Monolithic services begin to fracture and decentralized platform infrastructures emerge. Some governments assert their power and authority through the agenda of "digital sovereignty". New constellations of actors emerge and tensions manifest across state, market, and civil society. We witness realignments in the political economy of platforms and societies.'
    }
    
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
        # Process bold (**text**) first, before single asterisks
        line = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', line)
        # Single asterisks (*text*) should also be bold (per user request)
        line = re.sub(r'\*([^\*]+)\*', r'<strong>\1</strong>', line)
        return line
    
    # Extract headings for sidebar navigation
    headings = []
    heading_counter = 0

    html_lines = []
    for line in summary_section.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            heading_counter += 1
            heading_id = f'heading-{heading_counter}'
            heading_text = process_line(line[2:])
            # Remove any HTML tags for the plain text version
            plain_text = re.sub(r'<[^>]+>', '', heading_text)
            headings.append({'id': heading_id, 'text': plain_text, 'level': 1})
            html_lines.append(f'<h2 id="{heading_id}">{heading_text}</h2>')
        elif line.startswith('## '):
            heading_counter += 1
            heading_id = f'heading-{heading_counter}'
            heading_text = process_line(line[3:])
            plain_text = re.sub(r'<[^>]+>', '', heading_text)
            headings.append({'id': heading_id, 'text': plain_text, 'level': 2})
            html_lines.append(f'<h3 id="{heading_id}">{heading_text}</h3>')
        elif line.startswith('### '):
            heading_counter += 1
            heading_id = f'heading-{heading_counter}'
            heading_text = process_line(line[4:])
            plain_text = re.sub(r'<[^>]+>', '', heading_text)
            headings.append({'id': heading_id, 'text': plain_text, 'level': 3})
            html_lines.append(f'<h4 id="{heading_id}">{heading_text}</h4>')
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
    headings_json = json.dumps(headings)

    print(f"Extracted {len(headings)} headings for sidebar navigation")
    
    print("Building HTML...")
    
    # Build complete HTML
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>PlatGovNet</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Crimson Text',serif;line-height:1.6;color:#333;background:#fff;padding:20px 20px 20px 260px;max-width:1600px;margin:0 auto;position:relative}}
h1{{font-size:2em;margin-bottom:40px;font-weight:600}}
/* Left sidebar for filter */
.left-sidebar{{position:fixed;left:15px;top:20px;width:230px;max-height:calc(100vh - 40px);overflow-y:auto;z-index:9998}}
.filter-sidebar{{margin-bottom:20px}}
.filter-sidebar strong{{display:block;margin-bottom:10px;font-size:1.1em;font-weight:600}}
.filter-sidebar .theme-tag{{display:block;padding:6px 10px;margin:4px 0;background:#f5f5f5;border-radius:3px;cursor:pointer;font-size:0.9em;transition:all 0.2s}}
.filter-sidebar .theme-tag:hover{{background:#e0e0e0;padding-left:14px}}
.filter-sidebar .theme-tag.active{{background:#333;color:white}}
.filter-count{{display:inline-block;margin-left:8px;padding:2px 6px;background:#2c5aa0;color:white;border-radius:10px;font-size:0.75em;font-weight:600}}
/* TOC sidebar - no box */
.toc-sidebar{{margin-top:20px;padding-top:20px;border-top:1px solid #ddd}}
.toc-sidebar .sidebar-title{{font-weight:600;font-size:1em;margin-bottom:10px;color:#333}}
.toc-sidebar .sidebar-item{{padding:6px 4px;cursor:pointer;color:#2c5aa0;font-size:0.85em;transition:all 0.2s;line-height:1.4}}
.toc-sidebar .sidebar-item:hover{{padding-left:8px;color:#1a3d6e}}
.toc-sidebar .sidebar-item.level-1{{font-weight:600;font-size:0.95em}}
.toc-sidebar .sidebar-item.level-2{{padding-left:10px;font-size:0.85em}}
.toc-sidebar .sidebar-item.level-3{{padding-left:20px;font-size:0.8em;font-style:italic}}
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
.panel-item.highlighted{{background:#fff8dc;border-radius:4px;padding:5px}}
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
.panel-link{{color:#2c5aa0;cursor:pointer;border-bottom:1px dotted #2c5aa0}}
.panel-link:hover{{background:#f0f5ff}}
.keynote-section{{background:#f9f9f9;padding:20px 25px;margin:30px 0;border-left:4px solid #2c5aa0}}
.keynote-section p{{margin-bottom:12px}}
/* Panel preview - centered on right side of content */
.panel-preview{{position:fixed;right:50%;margin-right:-580px;top:50%;transform:translateY(-50%);width:350px;max-height:70vh;background:#fff;border:1px solid #ddd;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.15);padding:15px;z-index:10000;opacity:0;visibility:hidden;transition:opacity 0.3s,visibility 0.3s;overflow-y:auto}}
.panel-preview.visible{{opacity:1;visibility:visible}}
.panel-preview-title{{font-weight:600;font-size:1.1em;margin-bottom:12px;color:#333;border-bottom:1px solid #eee;padding-bottom:8px}}
.panel-preview .participant-item{{margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #f0f0f0}}
.panel-preview .participant-item:last-child{{margin-bottom:0;padding-bottom:0;border-bottom:none}}
.panel-preview .participant-name{{font-weight:600;display:block;margin-bottom:3px;color:#2c5aa0;font-size:0.95em}}
.panel-preview .participant-presentation{{display:block;font-size:0.9em;color:#555;line-height:1.4}}
/* External link preview - centered on right side of content */
.link-preview{{position:fixed;right:50%;margin-right:-580px;top:50%;transform:translateY(-50%);width:300px;background:#fff;border:1px solid #ddd;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.15);padding:15px;z-index:10000;opacity:0;visibility:hidden;transition:opacity 0.3s,visibility 0.3s}}
.link-preview.visible{{opacity:1;visibility:visible}}
.link-preview-title{{font-weight:600;font-size:1em;margin-bottom:8px;color:#333;line-height:1.3}}
.link-preview-url{{font-size:0.85em;color:#666;word-break:break-all}}
</style>
</head><body>
<div class="left-sidebar" id="left-sidebar">
<div class="filter-sidebar">
<strong>Filter by theme:</strong>
<div id="global-themes"></div>
<div id="filter-count-display" style="margin-top:10px;font-size:0.9em;color:#666;display:none;"></div>
</div>
<div class="toc-sidebar" id="toc-sidebar">
<div class="sidebar-title">Table of Contents</div>
<div id="sidebar-panels"></div>
</div>
</div>
<h1>PlatGovNet, then and now</h1>
<div class="conference-map">
<div class="year-section"><div class="year-left"><div class="year-header">2021</div><div class="year-summary">{menu_data['2021']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2021"></div></div></div>
<div class="year-section"><div class="year-left"><div class="year-header">2023</div><div class="year-summary">{menu_data['2023']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2023"></div></div></div>
<div class="year-section"><div class="year-left"><div class="year-header">2025</div><div class="year-summary">{menu_data['2025']}</div></div><div class="year-right"><div class="panels-grid" id="panels-2025"></div></div></div>
</div>
<div class="summary-container">
<div class="summary-main"><div class="summary-section" id="summary-2025">{summary_escaped}</div></div>
</div>
<div class="panel-preview" id="panel-preview">
<div class="panel-preview-title" id="panel-preview-title"></div>
<div id="panel-preview-content"></div>
</div>
<div class="link-preview" id="link-preview">
<div class="link-preview-title" id="preview-title"></div>
<div class="link-preview-url" id="preview-url"></div>
</div>
<script>
// Data is already parsed by Python and embedded as JSON
const dataByYear={data_json};
const allThemes={themes_json};
const sidebarHeadings={headings_json};

// Render theme filters in left sidebar
const globalThemesContainer=document.getElementById('global-themes');
const filterCountDisplay=document.getElementById('filter-count-display');
allThemes.forEach(theme=>{{
  const tag=document.createElement('span');
  tag.className='theme-tag';
  tag.textContent=theme;
  tag.dataset.theme=theme;
  tag.addEventListener('click',()=>toggleGlobalTheme(theme,tag));
  globalThemesContainer.appendChild(tag);
}});

// Render panels for each year
function renderYear(year){{
  const panels=dataByYear[year];
  if(!panels)return;
  const container=document.getElementById(`panels-${{year}}`);
  Object.keys(panels).forEach(panelName=>{{
    const panel=panels[panelName];
    const panelDiv=document.createElement('div');
    panelDiv.className='panel-item';
    panelDiv.dataset.theme=panel.theme;
    panelDiv.dataset.panel=panelName.toLowerCase();
    panelDiv.dataset.year=year;
    const nameDiv=document.createElement('div');
    nameDiv.className='panel-name';
    if(year==='2025'){{
      nameDiv.classList.add('clickable');
      nameDiv.onclick=()=>{{
        const links=document.querySelectorAll(`.panel-link[data-panel="${{panelName.toLowerCase()}}"]`);
        if(links[0]){{
          links[0].scrollIntoView({{behavior:'smooth',block:'center'}});
          links[0].style.background='#fff8dc';
          setTimeout(()=>links[0].style.background='',2000);
        }}
      }}
    }}
    nameDiv.textContent=panelName;
    const dotsDiv=document.createElement('div');
    dotsDiv.className='presentation-dots';
    panel.presentations.forEach(pres=>{{
      const dot=document.createElement('div');
      dot.className='dot';
      const tooltip=document.createElement('div');
      tooltip.className='tooltip';
      const nameSpan=document.createElement('span');
      nameSpan.className='tooltip-name';
      nameSpan.textContent=pres.person;
      const presSpan=document.createElement('span');
      presSpan.className='tooltip-presentation';
      presSpan.textContent=pres.presentation;
      tooltip.appendChild(nameSpan);
      tooltip.appendChild(presSpan);
      dot.appendChild(tooltip);
      dotsDiv.appendChild(dot);
    }});
    panelDiv.appendChild(nameDiv);
    panelDiv.appendChild(dotsDiv);
    container.appendChild(panelDiv);
  }});
}}

// Toggle theme filter with count indicator
function toggleGlobalTheme(theme,el){{
  const panels=document.querySelectorAll('.panel-item');
  const tags=document.querySelectorAll('.theme-tag');
  const wasActive=el.classList.contains('active');
  tags.forEach(t=>{{
    t.classList.remove('active');
    const existingCount=t.querySelector('.filter-count');
    if(existingCount)existingCount.remove();
  }});
  if(wasActive){{
    panels.forEach(p=>{{
      p.classList.remove('greyed-out');
      p.classList.remove('highlighted');
    }});
    filterCountDisplay.style.display='none';
  }}else{{
    el.classList.add('active');
    let highlightedCount=0;
    panels.forEach(p=>{{
      if(p.dataset.theme!==theme){{
        p.classList.add('greyed-out');
        p.classList.remove('highlighted');
      }}else{{
        p.classList.remove('greyed-out');
        p.classList.add('highlighted');
        highlightedCount++;
      }}
    }});
    const countBadge=document.createElement('span');
    countBadge.className='filter-count';
    countBadge.textContent=highlightedCount;
    el.appendChild(countBadge);
    filterCountDisplay.textContent=`${{highlightedCount}} panels highlighted`;
    filterCountDisplay.style.display='block';
  }}
}}

// Setup panel links with fixed right-side preview
function setupPanelLinks(){{
  const links=document.querySelectorAll('.panel-link');
  const panelPreview=document.getElementById('panel-preview');
  const panelPreviewTitle=document.getElementById('panel-preview-title');
  const panelPreviewContent=document.getElementById('panel-preview-content');
  let hideTimeout;

  // Helper function for case-insensitive panel lookup
  function findPanel(panelName){{
    if(!dataByYear['2025'])return null;
    const lowerName=panelName.toLowerCase();
    for(const key of Object.keys(dataByYear['2025'])){{
      if(key.toLowerCase()===lowerName)return{{name:key,data:dataByYear['2025'][key]}};
    }}
    return null;
  }}

  links.forEach(link=>{{
    const panelName=link.dataset.panel;
    const panelMatch=findPanel(panelName);
    const panel2025=panelMatch?panelMatch.data:null;
    const panelDisplayName=panelMatch?panelMatch.name:panelName;

    link.addEventListener('mouseenter',()=>{{
      clearTimeout(hideTimeout);
      if(panel2025){{
        panelPreviewTitle.textContent=panelDisplayName.split(' ').map(w=>w.charAt(0).toUpperCase()+w.slice(1)).join(' ');
        panelPreviewContent.innerHTML='';
        panel2025.presentations.forEach(pres=>{{
          const item=document.createElement('div');
          item.className='participant-item';
          const name=document.createElement('span');
          name.className='participant-name';
          name.textContent=pres.person;
          const presText=document.createElement('span');
          presText.className='participant-presentation';
          presText.textContent=pres.presentation;
          item.appendChild(name);
          item.appendChild(presText);
          panelPreviewContent.appendChild(item);
        }});
        panelPreview.classList.add('visible');
      }}
    }});

    link.addEventListener('mouseleave',()=>{{
      hideTimeout=setTimeout(()=>{{
        panelPreview.classList.remove('visible');
      }},200);
    }});

    link.onclick=(e)=>{{
      e.preventDefault();
      const el=document.querySelector(`[data-panel="${{panelName}}"][data-year="2025"]`);
      if(el){{
        el.scrollIntoView({{behavior:'smooth',block:'center'}});
        el.style.background='#fff8dc';
        setTimeout(()=>el.style.background='',2000);
      }}
    }};
  }});

  panelPreview.addEventListener('mouseenter',()=>{{
    clearTimeout(hideTimeout);
  }});
  panelPreview.addEventListener('mouseleave',()=>{{
    panelPreview.classList.remove('visible');
  }});
}}

// Setup TOC sidebar (no box, always visible)
function setupTocSidebar(){{
  const sidebarPanels=document.getElementById('sidebar-panels');
  if(!sidebarHeadings||sidebarHeadings.length===0)return;
  sidebarHeadings.forEach(heading=>{{
    const div=document.createElement('div');
    div.className=`sidebar-item level-${{heading.level}}`;
    const maxLen=heading.level===1?60:heading.level===2?50:40;
    let text=heading.text;
    if(text.length>maxLen)text=text.substring(0,maxLen)+'...';
    div.textContent=text;
    div.title=heading.text;
    div.onclick=()=>{{
      const el=document.getElementById(heading.id);
      if(el){{
        el.scrollIntoView({{behavior:'smooth',block:'start'}});
        el.style.background='#fff8dc';
        setTimeout(()=>el.style.background='',2000);
      }}
    }};
    sidebarPanels.appendChild(div);
  }});
}}

// Setup external link preview (title and URL only)
function setupLinkPreview(){{
  const preview=document.getElementById('link-preview');
  const previewTitle=document.getElementById('preview-title');
  const previewUrl=document.getElementById('preview-url');
  const summaryLinks=document.querySelectorAll('.summary-section a[href^="http"]');
  let hideTimeout;
  summaryLinks.forEach(link=>{{
    link.addEventListener('mouseenter',(e)=>{{
      clearTimeout(hideTimeout);
      const url=link.href;
      previewTitle.textContent=link.textContent||'External Link';
      previewUrl.textContent=url;
      preview.classList.add('visible');
    }});
    link.addEventListener('mouseleave',()=>{{
      hideTimeout=setTimeout(()=>{{
        preview.classList.remove('visible');
      }},200);
    }});
  }});
  preview.addEventListener('mouseenter',()=>{{
    clearTimeout(hideTimeout);
  }});
  preview.addEventListener('mouseleave',()=>{{
    preview.classList.remove('visible');
  }});
}}

// Initialize everything
renderYear('2021');
renderYear('2023');
renderYear('2025');
setupPanelLinks();
setupTocSidebar();
setupLinkPreview();
</script>
</body></html>'''
    
    # Write HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n✓ SUCCESS! index.html has been regenerated")
    print(f"✓ Embedded data for {total_panels} panels")
    print(f"✓ Embedded {len(summary_html)} chars of summary HTML")
    print(f"✓ Found {len(panel_markers)} linked panels in text")
    print("\nYou can now open platgovnet_conference.html in your browser!")

if __name__ == '__main__':
    build_html()
