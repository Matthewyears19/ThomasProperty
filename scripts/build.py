"""Dependency-free static build. Run from any directory with Python 3.10+."""
from pathlib import Path
from string import Template
from html import escape
from urllib.parse import quote
import json
import shutil
from datetime import date
from content import Content
from seo import SEO
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
business = json.loads((ROOT / 'data/business.json').read_text(encoding='utf-8'))
services = json.loads((ROOT / 'data/services.json').read_text(encoding='utf-8'))
content_data = Content(ROOT, services, business)
seo = SEO(ROOT, business, services)
template = Template((ROOT / 'templates/page.html').read_text(encoding='utf-8'))
# Rebuild only the exact generated directory. Removing an approval must remove
# its previous pages and images as well; unapproved source images never get copied.
if OUT.is_symlink() or OUT.resolve() != ROOT.resolve() / 'dist':
    raise ValueError('Refusing to rebuild an output path outside this project/dist')
print(f'Verified generated output directory: {OUT.resolve()}')
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for folder in ('css', 'js'):
    shutil.copytree(ROOT / 'assets' / folder, OUT / 'assets' / folder)
(OUT / 'assets/images').mkdir(parents=True)
for image_path in {ROOT / business['logo'].lstrip('/'), ROOT / 'assets/images/favicon.svg', *content_data.public_images}:
    destination = OUT / image_path.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(image_path, destination)
shutil.copyfile(ROOT / 'lib/validation.mjs', OUT / 'assets/js/validation.mjs')

def e(value):
    return escape(str(value), quote=True)

def button(label='Request a Free Quote', href='/request-quote/', style='gold'):
    return f'<a class="button button-{style}" href="{e(href)}">{e(label)} <span aria-hidden="true">↗</span></a>'

def actions(service=None):
    target = '/request-quote/' + ('?service=' + quote(service) if service else '')
    return '<div class="actions">' + button(href=target) + button('Call ' + business['phone'], business['phoneHref'], 'outline') + '</div>'

def placeholder(label, placement=None):
    if placement in content_data.placements:
        return content_data.service_figure(content_data.placements[placement], hero=placement == 'hero')
    return f'<div class="placeholder"><span class="frame" aria-hidden="true"></span><strong>{e(label)}</strong><small>Approved service photography to be supplied.</small><span class="placeholder-label">Development image placeholder · not completed work</span></div>'

def cards(items):
    result = '<div class="service-grid">'
    for service in items:
        image_id = content_data.placements.get(service['slug'])
        image = '<div class="card-photo">' + content_data.picture(image_id, sizes='(max-width: 640px) 100vw, (max-width: 1100px) 50vw, 33vw') + '<span>Illustrative stock photograph</span></div>' if image_id else ''
        result += f'<article class="service-card">{image}<div class="service-card-copy"><span class="number" aria-hidden="true">{e(service["symbol"])}</span><h3>{e(service["name"])}</h3><p>{e(service["short"])}</p><a class="text-link" href="/services/{e(service["slug"])}/">Explore {e(service["name"])} <span aria-hidden="true">↗</span></a></div></article>'
    return result + '</div>'

def cta():
    return '<section class="cta-section dark"><div class="container"><div><span class="eyebrow">Let’s get started</span><h2>Ready to improve your property?</h2><p>Discuss your project and request a free, no-obligation quotation.</p></div>' + actions() + '</div></section>'

def intro(title, text, parent=None):
    crumb = '<a href="/">Home</a> / ' + ('<a href="/services/">Services</a> / ' if parent else '') + e(title)
    return f'<section class="page-intro dark"><div class="container"><div class="breadcrumb">{crumb}</div><span class="eyebrow">{e(business["area"])}</span><h1>{e(title)}</h1><p>{e(text)}</p></div></section>'

routes = []
def page(route, title, description, content):
    description = textwrap.shorten(description, width=160, placeholder='…')
    values = {key: e(value) for key, value in business.items()}
    values.update(title=e(title + ' | ' + business['name']), description=e(description), canonical=e(business['domain'] + route), year=date.today().year, content=content)
    values['robots'] = 'index, follow' if seo.indexable and route != '/404.html' else 'noindex, nofollow'
    values['structuredData'] = seo.structured_data(route, title, description)
    values['navigationBootstrap'] = seo.navigation_bootstrap()
    for name, path in [('home', '/'), ('services', '/services/'), ('faqs', '/faqs/'), ('contact', '/contact/')]:
        values[name + 'Current'] = 'aria-current="page"' if route == path else ''
    values['pageScripts'] = '<script type="module" src="/assets/js/enquiry.js"></script>' if route == '/request-quote/' else ''
    if route == '/our-work/' and content_data.filter_enabled:
        values['pageScripts'] += '<script src="/assets/js/gallery.js" defer></script>'
    values['trustNav'] = ''
    values['trustFooter'] = ''
    for path, label, available in [('/our-work/', 'Our Work', content_data.projects), ('/reviews/', 'Reviews', content_data.reviews)]:
        if available:
            current = ' aria-current="page"' if route == path else ''
            values['trustNav'] += f'<li><a href="{path}"{current}>{label}</a></li>'
            values['trustFooter'] += f'<a href="{path}">{label}</a>'
    values['serviceLinks'] = ''.join(f'<li><a href="/services/{e(s["slug"])}/"' + (' aria-current="page"' if route == f'/services/{s["slug"]}/' else '') + f'>{e(s["name"])}</a></li>' for s in services)
    dest = OUT / route.strip('/') / 'index.html' if route != '/404.html' else OUT / '404.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(template.substitute(values), encoding='utf-8')
    routes.append(route)

home = '''<section class="hero dark"><div class="container hero-grid"><div><span class="eyebrow">Property care, thoughtfully done</span><h1>Quality Property Services.<br>Reliable Workmanship.<br><em>Exceptional Care.</em></h1><p>Professional painting, decorating and property improvements across Cheshire and surrounding areas. From refreshing a single room to maintaining an entire property, Thomas Property Services focuses on quality finishes, reliable service and attention to detail.</p>''' + actions() + '<span class="area">Serving Cheshire and surrounding areas</span></div>' + placeholder('Care in every finish.', 'hero') + '''</div></section>
<div class="principles"><div class="container"><span>Free, no-obligation quotations</span><span>Care for your property</span><span>Attention to detail</span></div></div>
<section class="section"><div class="container"><div class="section-heading"><div><span class="eyebrow">What we do</span><h2>A little refresh.<br>A bigger improvement.</h2></div><a class="text-link" href="/services/">Discover our services ↗</a></div>''' + cards(services) + '''</div></section>
<section class="section section-white"><div class="container split"><div><span class="eyebrow">The way we work</span><h2>Why choose Thomas Property Services?</h2><p>Thoughtful preparation, careful workmanship and an approachable service. Your property deserves attention at every stage.</p><ul class="values"><li>Attention to detail</li><li>Reliable, hardworking service</li><li>Respect and care for your property</li><li>Quality finishing</li><li>Free, no-obligation quotations</li></ul></div><div class="quote-panel"><span class="eyebrow">Our approach</span><p>From the first conversation to the finishing touches, the details matter.</p><small>Tell us what you have in mind. We’ll discuss the work and agree the scope of your quotation.</small>''' + actions() + '''</div></div></section>
<section class="section" id="about"><div class="container split"><div><span class="eyebrow">Meet Thomas Property Services</span><h2>Practical experience.<br>A personal approach.</h2></div><div><p>Thomas Property Services is a recently established business serving homeowners, landlords, letting agents, commercial businesses, property developers and housing associations.</p><p>The owner began learning painting and decorating alongside their father at around age 15. Their father brings over 25 years of experience; that is his experience, rather than the trading history of this business.</p><p>The owner has also worked with other companies on exterior work, including landscaping, roofing and bricklaying. Roofing and bricklaying are not currently advertised services.</p><a class="text-link" href="/contact/">Let’s discuss your property ↗</a></div></div></section>
<section class="section area-section dark"><div class="container split"><div><span class="eyebrow">Local property care</span><h2>Across Cheshire.<br>And a little beyond.</h2></div><div><p>We serve Cheshire and surrounding areas. Get in touch with your postcode and a short description of the work to discuss whether we can help in your location.</p><a href="/contact/">Ask about your area ↗</a></div></div></section>''' + cta()
home = home.replace('Practical experience.<br>A personal approach.</h2></div>', 'Practical experience.<br>A personal approach.</h2>' + content_data.service_figure('stock-maintenance') + '</div>') if 'stock-maintenance' in content_data.images else home
trust_sections = ''
if content_data.projects:
    featured_projects = [p for p in content_data.projects if p.get('featured') is True][:3] or content_data.projects[:3]
    trust_sections += '<section class="section"><div class="container"><div class="section-heading"><div><span class="eyebrow">Our work</span><h2>Care you can see.</h2></div><a class="text-link" href="/our-work/">Explore our completed work ↗</a></div>' + content_data.project_cards(featured_projects, heading=3) + '</div></section>'
if content_data.reviews:
    featured_reviews = [r for r in content_data.reviews if r.get('featured') is True][:3] or content_data.reviews[:3]
    trust_sections += '<section class="section section-white"><div class="container"><div class="section-heading"><div><span class="eyebrow">Customer feedback</span><h2>In our customers’ words.</h2></div><a class="text-link" href="/reviews/">Read customer reviews ↗</a></div>' + content_data.review_cards(featured_reviews) + '</div></section>'
home = home.replace('<section class="section area-section', trust_sections + '<section class="section area-section', 1)
page('/', 'Property services in Cheshire', 'Painting, decorating, property improvements and maintenance across Cheshire and surrounding areas. Request a free quotation from Thomas Property Services.', home)
page('/services/', 'Our services', 'Explore painting, decorating, wood finishing, property improvements, jet washing and landlord maintenance in Cheshire.', intro('Property care, inside and out.', 'Explore our services and tell us what your property needs. Work is discussed individually and quotations are free and no-obligation.') + '<section class="section"><div class="container"><h2>Explore our property services</h2>' + cards(services) + '</div></section>' + cta())

for s in services:
    scope = '<ul class="checklist">' + ''.join('<li>' + e(w) + '</li>' for w in s['work']) + '</ul>'
    extra = ''
    if s['slug'] == 'house-mot':
        extra = '<div class="actions">' + button('Enquire about a one-off House MOT', '/request-quote/?service=' + quote('One-off House MOT'), 'navy') + button('Discuss ongoing maintenance', '/request-quote/?service=' + quote('Ongoing Property Maintenance'), 'outline') + '</div>'
    content = intro(s['name'], s['intro'], True) + '<section class="section section-white"><div class="container split service-detail"><div><span class="eyebrow">The service</span><h2>How we can help</h2>' + scope + '<h2>Careful work, considered results</h2><p>' + e(s['benefit']) + '</p><div class="notice">' + e(s['note']) + '</div>' + actions(s['quote']) + extra + ('<div class="notice"><strong>Draft service scope — for review</strong><p>' + e(s['draftScope']['oneOff']) + '</p><p>' + e(s['draftScope']['ongoing']) + '</p><p>' + e(s['draftScope']['exclusions']) + '</p></div>' if s.get('draftScope') else '') + '</div><div>' + placeholder(s['name'], s['slug']) + '<h2>What happens next?</h2><p>Tell us about the property and the work you have in mind. We’ll discuss suitability, scope and the next steps towards your free, no-obligation quotation.</p><p>Materials, timing and any preparation needed will be discussed for your individual job.</p></div></div></section><section class="section"><div class="container"><span class="eyebrow">More ways we can help</span><h2>Related services</h2>' + cards([other for other in services if other != s][:2]) + '</div></section>' + cta()
    service_faqs = [faq for faq in content_data.faqs if s['slug'] in faq['services']]
    if service_faqs:
        questions = '<section class="section section-white"><div class="container"><span class="eyebrow">Planning your enquiry</span><h2>Questions about this service</h2>' + content_data.faq_list(service_faqs) + '<p><a href="/faqs/">More frequently asked questions ↗</a></p></div></section>'
        content = content.replace(cta(), questions + cta(), 1)
    page('/services/' + s['slug'] + '/', s['name'] + ' in Cheshire', s['intro'], content)

if content_data.reviews:
    page('/reviews/', 'Customer reviews', 'Read genuine, permissioned customer feedback about Thomas Property Services.', intro('In our customers’ words.', 'Customer feedback published with permission. Read about their experience of working with Thomas Property Services.') + '<section class="section"><div class="container">' + content_data.review_cards(content_data.reviews) + '</div></section>' + cta())

if content_data.projects:
    page('/our-work/', 'Our completed work', 'Explore genuine Thomas Property Services projects, organised by service.', intro('Thoughtful work. Real results.', 'A selection of genuine completed work, shared with permission.') + '<section class="section"><div class="container">' + content_data.filters() + content_data.project_cards(content_data.projects) + '</div></section>' + cta())
    for project in content_data.projects:
        images = ''
        paired = set()
        if project.get('beforeAfter'):
            images += '<section aria-label="Before and after photographs" class="before-after">'
            for key, label in [('before', 'Before'), ('after', 'After')]:
                image_id = project['beforeAfter'][key]
                image_record = content_data.images[image_id]
                paired.add(image_id)
                images += '<figure class="project-photo">' + content_data.picture(image_id) + f'<figcaption><strong>{label}</strong>{e(image_record["alt"])} {e(image_record.get("credit", ""))}</figcaption></figure>'
            images += '</section>'
        images += '<div class="photo-grid">'
        for image_id in project['images']:
            if image_id not in paired:
                image_record = content_data.images[image_id]
                images += '<figure class="project-photo">' + content_data.picture(image_id) + f'<figcaption>{e(image_record["alt"])} {e(image_record.get("credit", ""))}</figcaption></figure>'
        images += '</div>'
        location = f'<p>{e(project["location"])}</p>' if project.get('location') else ''
        details = '<section class="section"><div class="container"><p><a href="/our-work/">← Back to our work</a></p>' + location + images + f'<p>Service: <a href="/services/{e(project["category"])}/">{e(content_data.services[project["category"]]["name"])}</a></p></div></section>'
        page('/our-work/' + project['slug'] + '/', project['title'], project['description'], intro(project['title'], project['description']) + details + cta())

def contact_details():
    return f'''<div class="contact-card"><h3>Give us a call</h3><a class="contact-phone" href="{e(business['phoneHref'])}">{e(business['phone'])}</a></div><div class="contact-card"><h3>Send an email</h3><a href="mailto:{e(business['email'])}">{e(business['email'])}</a></div><div class="contact-card"><h3>Where we work</h3><p>{e(business['area'])}. Share your postcode to discuss coverage.</p></div><div class="contact-card"><h3>Stay in touch</h3><a href="{e(business['facebook'])}">Thomas Property Services on Facebook ↗</a></div>'''

page('/contact/', 'Contact us', 'Call 07410 928465 or email Thomas Property Services to discuss property care and free quotations across Cheshire and surrounding areas.', intro('Let’s talk about your property.', 'A room to refresh, outdoor surfaces to clean or a list of maintenance jobs? Tell us what you have in mind.') + '<section class="section"><div class="container split service-detail"><div><h2>A conversation is a good place to start.</h2><p>Contact us by telephone or email to discuss your project. We aim to respond to enquiries within 48 hours. For a more urgent enquiry, please call.</p>' + contact_details() + '</div><aside class="form-panel"><span class="eyebrow">Your next step</span><h2>Request a free quote</h2><p>Have a service in mind? The quotation page collects the details that help us understand the job.</p><ul class="checklist"><li>What work is needed?</li><li>Where is the property?</li><li>When would you like to get started?</li></ul>' + button() + '<div class="notice">Use the quotation page to send an enquiry when the online service is available. You can always telephone or email us directly.</div></aside></div></section>' + cta())

options = ['Painting and Decorating', 'Gloss Work and Wood Finishing', 'Property Improvements', 'Jet Washing', 'Mould Removal', 'One-off House MOT', 'Ongoing Property Maintenance', 'Other / Not Sure']
form = Template((ROOT / 'templates/quote-form.html').read_text(encoding='utf-8')).substitute(options=''.join(f'<option value="{e(o)}">{e(o)}</option>' for o in options))

page('/request-quote/', 'Request a free quote', 'Discuss your painting, decorating or property maintenance project. Free, no-obligation quotations from Thomas Property Services in Cheshire.', intro('Your property. Your next project.', 'Request a free, no-obligation quotation. Tell us about the work below, or contact us by telephone or email. Online submission is available once the secure enquiry service is configured.') + '<section class="section"><div class="container split service-detail"><div><span class="eyebrow">No obligation, just a conversation</span><h2>Tell us what you have in mind.</h2><p>A short description of the work and a way to get in touch are a good starting point. The scope, materials and timing will be discussed for your project.</p>' + contact_details() + '</div>' + form + '</div></section>')

faqs = content_data.faqs

page('/faqs/', 'Frequently asked questions', 'Find answers about service areas, free quotations, materials and landlord maintenance from Thomas Property Services.', intro('A few useful answers.', 'Practical information to help you plan your enquiry.') + '<section class="section"><div class="container">' + content_data.faq_list(faqs) + '</div></section>' + cta())

privacy = (ROOT / 'templates/privacy-content.html').read_text(encoding='utf-8')

page('/privacy-policy/', 'Privacy policy — development draft', 'Development privacy notice describing the current local website and outstanding privacy information before launch.', intro('Privacy policy', 'Privacy information for enquiries and website use. Retention details remain subject to the operator’s final notice.') + privacy)
page('/404.html', 'Page not found', 'This page could not be found. Return to Thomas Property Services or contact us about your property.', intro('This page could not be found.', 'The page may have moved, or the address may be incorrect.') + '<section class="section"><div class="container">' + button('Return to the homepage', '/', 'navy') + '</div></section>')

seo.write_files(OUT, routes)
(OUT / '_routes.json').write_text(json.dumps({'version': 1, 'include': ['/api/*'], 'exclude': []}), encoding='utf-8')
print(f'Built {len(routes)} pages in {OUT}')
