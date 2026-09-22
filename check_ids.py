import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

js_ids = set(re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]", js))
html_ids = set(re.findall(r"id=['\"]([^'\"]+)['\"]", html))

missing_ids = [i for i in js_ids if i not in html_ids]
print('JS IDs referenced count:', len(js_ids))
print('Missing IDs in HTML count:', len(missing_ids))
for m in sorted(missing_ids):
    print('  - Missing ID:', m)
