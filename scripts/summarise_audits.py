"""Save small reproducible Lighthouse results; raw reports stay ignored."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
results = []
for name in ('home-mobile', 'quote-mobile', 'contact-mobile', 'home-desktop'):
    path = ROOT / 'reports' / f'{name}.json'
    if not path.exists():
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    results.append({
        'name': name, 'url': report['requestedUrl'], 'time': report['fetchTime'],
        'lighthouseVersion': report['lighthouseVersion'],
        'userAgent': report['environment']['hostUserAgent'],
        'formFactor': report['configSettings']['formFactor'],
        'throttlingMethod': report['configSettings']['throttlingMethod'],
        'throttling': report['configSettings']['throttling'],
        'scores': {key: round(value['score'] * 100) for key, value in report['categories'].items()},
        'metrics': {key: {'value': report['audits'][key].get('numericValue'), 'display': report['audits'][key].get('displayValue')} for key in ('largest-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time')},
        'failedAudits': [key for key, value in report['audits'].items() if value.get('score') == 0 and value.get('scoreDisplayMode') not in ('informative', 'manual', 'notApplicable')]
    })
destination = ROOT / 'docs/lighthouse-results.json'
destination.write_text(json.dumps({'context': 'Local static preview; form/analytics disabled; preview intentionally blocked from indexing; synthetic tests are not field Core Web Vitals or live delivery verification.', 'results': results}, indent=2) + '\n', encoding='utf-8')
print(destination)
