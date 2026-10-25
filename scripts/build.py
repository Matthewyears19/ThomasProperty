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
        image = ''
        if image_id:
            record = content_data.images[image_id]
            photo_class = 'card-photo comparison' if record.get('presentation') == 'comparison' else 'card-photo'
            label = 'Illustrative stock photograph' if record['kind'] == 'stock' else ('My work — before and after' if record.get('presentation') == 'comparison' else 'My work')
            image = f'<div class="{photo_class}">' + content_data.picture(image_id, sizes='(max-width: 640px) 100vw, (max-width: 1100px) 50vw, 33vw') + f'<span>{label}</span></div>'
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
    values['pageScripts'] = '<script type="module" src="/assets/js/enquiry.js"></script>' if route in ('/request-quote/', '/contact/') else ''
    if route == '/our-work/' and content_data.filter_enabled:
        values['pageScripts'] += '<script src="/assets/js/gallery.js" defer></script>'
    values['trustNav'] = ''
    values['trustFooter'] = ''
    for path, label, available in [('/our-work/', 'My Work', content_data.projects), ('/reviews/', 'Reviews', content_data.reviews)]:
        if available:
            current = ' aria-current="page"' if route == path else ''
            values['trustNav'] += f'<li><a href="{path}"{current}>{label}</a></li>'
            values['trustFooter'] += f'<a href="{path}">{label}</a>'
    values['serviceLinks'] = ''.join(f'<li><a href="/services/{e(s["slug"])}/"' + (' aria-current="page"' if route == f'/services/{s["slug"]}/' else '') + f'>{e(s["name"])}</a></li>' for s in services)
    dest = OUT / route.strip('/') / 'index.html' if route != '/404.html' else OUT / '404.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(template.substitute(values), encoding='utf-8')
    routes.append(route)

home = '''<section class="hero dark"><div class="container hero-grid"><div><span class="eyebrow">Property care, thoughtfully done</span><h1>Quality Property Services.<br>Reliable Workmanship.<br><em>Exceptional Care.</em></h1><p>I provide professional painting, decorating and property improvements across Cheshire and surrounding areas. From refreshing a single room to maintaining an entire property, I focus on quality finishes, reliable service and attention to detail.</p>''' + actions() + '<span class="area">Serving Cheshire and surrounding areas</span></div>' + placeholder('Care in every finish.', 'hero') + '''</div></section>
<div class="principles"><div class="container"><span>Free, no-obligation quotations</span><span>Care for your property</span><span>Attention to detail</span></div></div>
<section class="section"><div class="container"><div class="section-heading"><div><span class="eyebrow">What I do</span><h2>A little refresh.<br>A bigger improvement.</h2></div><a class="text-link" href="/services/">Discover my services ↗</a></div>''' + cards(services) + '''</div></section>
<section class="section section-white"><div class="container split"><div><span class="eyebrow">The way I work</span><h2>Why choose me?</h2><p>Thoughtful preparation, careful workmanship and an approachable service. Your property deserves attention at every stage.</p><ul class="values"><li>Attention to detail</li><li>Reliable, hardworking service</li><li>Respect and care for your property</li><li>Quality finishing</li><li>Free, no-obligation quotations</li></ul></div><div class="quote-panel"><span class="eyebrow">My approach</span><p>From the first conversation to the finishing touches, the details matter.</p><small>Tell me what you have in mind. I’ll discuss the work and agree the scope of your quotation.</small>''' + actions() + '''</div></div></section>
<section class="section" id="about"><div class="container split"><div><span class="eyebrow">A little about me</span><h2>Practical experience.<br>A personal approach.</h2></div><div><p>I run Thomas Property Services, a recently established business helping homeowners, landlords, letting agents, commercial businesses, property developers and housing associations.</p><p>I began learning painting and decorating alongside my father at around age 15. My father has over 25 years of experience, and learning from him helped shape my approach to careful preparation and finishing. Thomas Property Services is my recently established business.</p><p>I have also worked with other companies on exterior work, including landscaping, roofing and bricklaying. I do not currently offer roofing or bricklaying through Thomas Property Services.</p><a class="text-link" href="/contact/">Let’s discuss your property ↗</a></div></div></section>
<section class="section area-section dark"><div class="container split"><div><span class="eyebrow">Local property care</span><h2>Across Cheshire.<br>And a little beyond.</h2></div><div><p>I serve Cheshire and surrounding areas. Get in touch with your postcode and a short description of the work to discuss whether I can help in your location.</p><a href="/contact/">Ask about your area ↗</a></div></div></section>''' + cta()
home = home.replace('Practical experience.<br>A personal approach.</h2></div>', 'Practical experience.<br>A personal approach.</h2>' + content_data.service_figure(content_data.placements['intro']) + '</div>') if content_data.placements.get('intro') else home
trust_sections = ''
if content_data.projects:
    featured_projects = [p for p in content_data.projects if p.get('featured') is True][:3] or content_data.projects[:3]
    trust_sections += '<section class="section"><div class="container"><div class="section-heading"><div><span class="eyebrow">My work</span><h2>Care you can see.</h2></div><a class="text-link" href="/our-work/">Explore my completed work ↗</a></div>' + content_data.project_cards(featured_projects, heading=3) + '</div></section>'
if content_data.reviews:
    featured_reviews = [r for r in content_data.reviews if r.get('featured') is True][:3] or content_data.reviews[:3]
    trust_sections += '<section class="section section-white"><div class="container"><div class="section-heading"><div><span class="eyebrow">Customer feedback</span><h2>In my customers’ words.</h2></div><a class="text-link" href="/reviews/">Read customer reviews ↗</a></div>' + content_data.review_cards(featured_reviews) + '</div></section>'
home = home.replace('<section class="section area-section', trust_sections + '<section class="section area-section', 1)
page('/', 'Property services in Cheshire', 'Painting, decorating, property improvements and maintenance across Cheshire and surrounding areas. Request a free quotation from Thomas Property Services.', home)
page('/services/', 'My services', 'Explore painting, decorating, wood finishing, property improvements, jet washing and landlord maintenance in Cheshire.', intro('Property care, inside and out.', 'Explore my services and tell me what your property needs. Work is discussed individually and quotations are free and no-obligation.') + '<section class="section"><div class="container"><h2>Explore my property services</h2>' + cards(services) + '</div></section>' + cta())

for s in services:
    scope = '<ul class="checklist">' + ''.join('<li>' + e(w) + '</li>' for w in s['work']) + '</ul>'
    extra = ''
    if s['slug'] == 'house-mot':
        extra = '<div class="actions">' + button('Enquire about a one-off House MOT', '/request-quote/?service=' + quote('One-off House MOT'), 'navy') + button('Discuss ongoing maintenance', '/request-quote/?service=' + quote('Ongoing Property Maintenance'), 'outline') + '</div>'
    content = intro(s['name'], s['intro'], True) + '<section class="section section-white"><div class="container split service-detail"><div><span class="eyebrow">The service</span><h2>How I can help</h2>' + scope + '<h2>Careful work, considered results</h2><p>' + e(s['benefit']) + '</p><div class="notice">' + e(s['note']) + '</div>' + actions(s['quote']) + extra + ('<div class="notice"><strong>Draft service scope — for review</strong><p>' + e(s['draftScope']['oneOff']) + '</p><p>' + e(s['draftScope']['ongoing']) + '</p><p>' + e(s['draftScope']['exclusions']) + '</p></div>' if s.get('draftScope') else '') + '</div><div>' + placeholder(s['name'], s['slug']) + ''.join(content_data.service_figure(image_id) for image_id in content_data.service_galleries.get(s['slug'], [])) + '<h2>What happens next?</h2><p>Tell me about the property and the work you have in mind. I’ll discuss suitability, scope and the next steps towards your free, no-obligation quotation.</p><p>Materials, timing and any preparation needed will be discussed for your individual job.</p></div></div></section><section class="section"><div class="container"><span class="eyebrow">More ways I can help</span><h2>Related services</h2>' + cards([other for other in services if other != s][:2]) + '</div></section>' + cta()
    service_faqs = [faq for faq in content_data.faqs if s['slug'] in faq['services']]
    if service_faqs:
        questions = '<section class="section section-white"><div class="container"><span class="eyebrow">Planning your enquiry</span><h2>Questions about this service</h2>' + content_data.faq_list(service_faqs) + '<p><a href="/faqs/">More frequently asked questions ↗</a></p></div></section>'
        content = content.replace(cta(), questions + cta(), 1)
    page('/services/' + s['slug'] + '/', s['name'] + ' in Cheshire', s['intro'], content)

if content_data.reviews:
    page('/reviews/', 'Customer reviews', 'Read genuine, permissioned customer feedback about Thomas Property Services.', intro('In my customers’ words.', 'Customer feedback published with permission. Read about their experience of working with Thomas Property Services.') + '<section class="section"><div class="container">' + content_data.review_cards(content_data.reviews) + '</div></section>' + cta())

if content_data.projects:
    page('/our-work/', 'My completed work', 'Explore genuine Thomas Property Services projects, organised by service.', intro('Thoughtful work. Real results.', 'A selection of genuine completed work, shared with permission.') + '<section class="section"><div class="container">' + content_data.filters() + content_data.project_cards(content_data.projects) + '</div></section>' + cta())
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
        details = '<section class="section"><div class="container"><p><a href="/our-work/">← Back to my work</a></p>' + location + images + f'<p>Service: <a href="/services/{e(project["category"])}/">{e(content_data.services[project["category"]]["name"])}</a></p></div></section>'
        page('/our-work/' + project['slug'] + '/', project['title'], project['description'], intro(project['title'], project['description']) + details + cta())

def contact_details():
    return f'''<div class="contact-card"><h3>Give me a call</h3><a class="contact-phone" href="{e(business['phoneHref'])}">{e(business['phone'])}</a></div><div class="contact-card"><h3>Send an email</h3><a href="mailto:{e(business['email'])}">{e(business['email'])}</a></div><div class="contact-card"><h3>Where I work</h3><p>{e(business['area'])}. Share your postcode to discuss coverage.</p></div><div class="contact-card"><h3>Stay in touch</h3><a href="{e(business['facebook'])}">Thomas Property Services on Facebook ↗</a></div>'''


options = ['General enquiry', 'Painting and Decorating', 'Gloss Work and Wood Finishing', 'Property Improvements', 'Jet Washing', 'Mould Removal', 'One-off House MOT', 'Ongoing Property Maintenance', 'Other / Not Sure']
form = Template((ROOT / 'templates/quote-form.html').read_text(encoding='utf-8')).substitute(options=''.join(f'<option value="{e(o)}">{e(o)}</option>' for o in options))

contact_form = form.replace('value="General enquiry"', 'value="General enquiry" selected', 1)
page('/contact/', 'Contact me and general enquiries', 'Ask Thomas Property Services a question or discuss property work in Cheshire. Send an enquiry, call or email me.', intro('How can I help?', 'Ask a question, discuss property maintenance or request a free quotation. You do not need to have a specific project in mind.') + '<section class="section"><div class="container split service-detail"><div><h2>A conversation is a good place to start.</h2><p>Use this form for a general enquiry or choose a service to discuss work. I aim to respond within 48 hours. For a more urgent enquiry, please telephone.</p>' + contact_details() + '</div>' + contact_form + '</div></section>')

page('/request-quote/', 'Enquiries and free quotations', 'Send a general enquiry or request a free, no-obligation quotation for property services in Cheshire. Contact Thomas Property Services.', intro('An enquiry or a project in mind?', 'Ask a general question or tell me about work you would like completed. Quotations are free and no-obligation. You can also contact me by telephone or email.') + '<section class="section"><div class="container split service-detail"><div><span class="eyebrow">No obligation, just a conversation</span><h2>Tell me what you have in mind.</h2><p>A short message and a way to get in touch are all you need to start. For work enquiries, please include the area or postcode where the work is to be completed. The scope, materials and timing will be discussed for your project.</p>' + contact_details() + '</div>' + form + '</div></section>')

faqs = content_data.faqs

page('/faqs/', 'Frequently asked questions', 'Find answers about service areas, free quotations, materials and landlord maintenance from Thomas Property Services.', intro('A few useful answers.', 'Practical information to help you plan your enquiry.') + '<section class="section"><div class="container">' + content_data.faq_list(faqs) + '</div></section>' + cta())

privacy = (ROOT / 'templates/privacy-content.html').read_text(encoding='utf-8')

page('/privacy-policy/', 'Privacy policy — development draft', 'Development privacy notice describing the current local website and outstanding privacy information before launch.', intro('Privacy policy', 'Privacy information for enquiries and website use. Retention details remain subject to the operator’s final notice.') + privacy)
page('/404.html', 'Page not found', 'This page could not be found. Return to Thomas Property Services or contact me about your property.', intro('This page could not be found.', 'The page may have moved, or the address may be incorrect.') + '<section class="section"><div class="container">' + button('Return to the homepage', '/', 'navy') + '</div></section>')

seo.write_files(OUT, routes)
(OUT / '_routes.json').write_text(json.dumps({'version': 1, 'include': ['/api/*'], 'exclude': []}), encoding='utf-8')
print(f'Built {len(routes)} pages in {OUT}')
