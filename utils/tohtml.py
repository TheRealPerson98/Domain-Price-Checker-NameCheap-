import os
import datetime
import shutil
from utils.html.final.macros import render_template, get_status_info, count_statuses

def generate_html_output(results, save_screenshots=False):
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d %H:%M:%S")
    
    available_count, unavailable_count, error_count = count_statuses(results)
    
    report_dir = os.path.join("data")
    assets_dir = os.path.join(report_dir, "assets")
    
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(script_dir, "html", "final")
    
    css_src = os.path.join(template_dir, "styles.css")
    js_src = os.path.join(template_dir, "script.js")
    
    css_dest = os.path.join(assets_dir, "styles.css")
    js_dest = os.path.join(assets_dir, "script.js")
    
    shutil.copy2(css_src, css_dest)
    shutil.copy2(js_src, js_dest)
    
    with open(os.path.join(template_dir, "template.html"), 'r', encoding='utf-8') as f:
        template = f.read()
    
    with open(os.path.join(template_dir, "row_template.html"), 'r', encoding='utf-8') as f:
        row_template = f.read()
    
    table_rows = ""
    for domain, price in sorted(results.items()):
        status_class, status_text = get_status_info(price)
        
        screenshot_path = f"images/{domain.replace('.', '_')}.png"
        screenshot_full_path = os.path.join("data", screenshot_path)
        screenshot_exists = save_screenshots and os.path.exists(screenshot_full_path)
        
        screenshot_cell = ""
        if save_screenshots:
            if screenshot_exists:
                screenshot_cell = f'<td><img src="{screenshot_path}" class="screenshot" onclick="openModal(\'{screenshot_path}\')" alt="{domain} screenshot"></td>'
            else:
                screenshot_cell = '<td>No screenshot</td>'
        
        row_context = {
            "domain": domain,
            "status_class": status_class,
            "status_text": status_text,
            "price": price,
            "screenshot_cell": screenshot_cell
        }
        
        row = render_template(row_template, row_context)
        table_rows += row
    
    template_context = {
        "date": date_string,
        "total_count": len(results),
        "available_count": available_count,
        "unavailable_count": unavailable_count,
        "error_count": error_count,
        "screenshot_header": '<th>Screenshot</th>' if save_screenshots else '',
        "table_rows": table_rows
    }
    
    html = render_template(template, template_context)
    
    html = html.replace('href="styles.css"', 'href="assets/styles.css"')
    html = html.replace('src="script.js"', 'src="assets/script.js"')
    
    html_path = os.path.join("data", "domain_report.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return html_path 