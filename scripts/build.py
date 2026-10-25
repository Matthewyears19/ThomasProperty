"""Dependency-free static build. Run from any directory with Python 3.10+."""
from pathlib import Path
from string import Template
from html import escape
from urllib.parse import quote
import json
import shutil
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)
business = json.loads((ROOT / 'data/business.json').read_text(encoding='utf-8'))
services = json.loads((ROOT / 'data/services.json').read_text(encoding='utf-8'))
template = Template((ROOT / 'templates/page.html').read_text(encoding='utf-8'))
shutil.copytree(ROOT / 'assets', OUT / 'assets', dirs_exist_ok=True)

def e(value):
    return escape(str(value), quote=True)

def button(label='Request a Free Quote', href='/request-quote/', style='gold'):
    return f'<a class="button button-{style}" href="{e(href)}">{e(label)} <span aria-hidden="true">↗</span></a>'

def actions(service=None):
    target = '/request-quote/' + ('?service=' + quote(service) if service else '')
    return '<div class="actions">' + button(href=target) + button('Call ' + business['phone'], business['phoneHref'], 'outline') + '</div>'

def placeholder(label):
    return f'<div class="placeholder"><span class="frame" aria-hidden="true"></span><strong>{e(label)}</strong><small>Approved service photography to be supplied.</small><span class="placeholder-label">Development image placeholder · not completed work</span></div>'

def cards(items):
    return '<div class="service-grid">' + ''.join(f'<article class="service-card"><span class="number" aria-hidden="true">{e(s["symbol"])}</span><h3>{e(s["name"])}</h3><p>{e(s["short"])}</p><a class="text-link" href="/services/{e(s["slug"])}/">Explore {e(s["name"])} <span aria-hidden="true">↗</span></a></article>' for s in items) + '</div>'

def cta():
    return '<section class="cta-section dark"><div class="container"><div><span class="eyebrow">Let’s get started</span><h2>Ready to improve your property?</h2><p>Discuss your project and request a free, no-obligation quotation.</p></div>' + actions() + '</div></section>'

def intro(title, text, parent=None):
    crumb = '<a href="/">Home</a> / ' + ('<a href="/services/">Services</a> / ' if parent else '') + e(title)
    return f'<section class="page-intro dark"><div class="container"><div class="breadcrumb">{crumb}</div><span class="eyebrow">{e(business["area"])}</span><h1>{e(title)}</h1><p>{e(text)}</p></div></section>'

routes = []
def page(route, title, description, content):
    values = {key: e(value) for key, value in business.items()}
    values.update(title=e(title + ' | ' + business['name']), description=e(description), canonical=e(business['domain'] + route), year=date.today().year, content=content)
    for name, path in [('home', '/'), ('services', '/services/'), ('faqs', '/faqs/'), ('contact', '/contact/')]:
        values[name + 'Current'] = 'aria-current="page"' if route == path else ''
    values['serviceLinks'] = ''.join(f'<li><a href="/services/{e(s["slug"])}/"' + (' aria-current="page"' if route == f'/services/{s["slug"]}/' else '') + f'>{e(s["name"])}</a></li>' for s in services)
    dest = OUT / route.strip('/') / 'index.html' if route != '/404.html' else OUT / '404.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(template.substitute(values), encoding='utf-8')
    routes.append(route)

home = '''<section class="hero dark"><div class="container hero-grid"><div><span class="eyebrow">Property care, thoughtfully done</span><h1>Quality Property Services.<br>Reliable Workmanship.<br><em>Exceptional Care.</em></h1><p>Professional painting, decorating and property improvements across Cheshire and surrounding areas. From refreshing a single room to maintaining an entire property, Thomas Property Services focuses on quality finishes, reliable service and attention to detail.</p>''' + actions() + '<span class="area">Serving Cheshire and surrounding areas</span></div>' + placeholder('Care in every finish.') + '''</div></section>
<div class="principles"><div class="container"><span>Free, no-obligation quotations</span><span>Care for your property</span><span>Attention to detail</span></div></div>
<section class="section"><div class="container"><div class="section-heading"><div><span class="eyebrow">What we do</span><h2>A little refresh.<br>A bigger improvement.</h2></div><a class="text-link" href="/services/">Discover our services ↗</a></div>''' + cards(services) + '''</div></section>
<section class="section section-white"><div class="container split"><div><span class="eyebrow">The way we work</span><h2>Why choose Thomas Property Services?</h2><p>Thoughtful preparation, careful workmanship and an approachable service. Your property deserves attention at every stage.</p><ul class="values"><li>Attention to detail</li><li>Reliable, hardworking service</li><li>Respect and care for your property</li><li>Quality finishing</li><li>Free, no-obligation quotations</li></ul></div><div class="quote-panel"><span class="eyebrow">Our approach</span><p>From the first conversation to the finishing touches, the details matter.</p><small>Tell us what you have in mind. We’ll discuss the work and agree the scope of your quotation.</small>''' + actions() + '''</div></div></section>
<section class="section" id="about"><div class="container split"><div><span class="eyebrow">Meet Thomas Property Services</span><h2>Practical experience.<br>A personal approach.</h2></div><div><p>Thomas Property Services is a recently established business serving homeowners, landlords, letting agents, commercial businesses, property developers and housing associations.</p><p>The owner began learning painting and decorating alongside their father at around age 15. Their father brings over 25 years of experience; that is his experience, rather than the trading history of this business.</p><p>The owner has also worked with other companies on exterior work, including landscaping, roofing and bricklaying. Roofing and bricklaying are not currently advertised services.</p><a class="text-link" href="/contact/">Let’s discuss your property ↗</a></div></div></section>
<section class="section area-section dark"><div class="container split"><div><span class="eyebrow">Local property care</span><h2>Across Cheshire.<br>And a little beyond.</h2></div><div><p>We serve Cheshire and surrounding areas. Get in touch with your postcode and a short description of the work to discuss whether we can help in your location.</p><a href="/contact/">Ask about your area ↗</a></div></div></section>''' + cta()
page('/', 'Property services in Cheshire', 'Painting, decorating, property improvements and maintenance across Cheshire and surrounding areas. Request a free quotation from Thomas Property Services.', home)
page('/services/', 'Our services', 'Explore painting, decorating, wood finishing, property improvements, jet washing and landlord maintenance in Cheshire.', intro('Property care, inside and out.', 'Explore our services and tell us what your property needs. Work is discussed individually and quotations are free and no-obligation.') + '<section class="section"><div class="container">' + cards(services) + '</div></section>' + cta())

for s in services:
    scope = '<ul class="checklist">' + ''.join('<li>' + e(w) + '</li>' for w in s['work']) + '</ul>'
    extra = ''
    if s['slug'] == 'house-mot':
        extra = '<div class="actions">' + button('Enquire about a one-off House MOT', '/request-quote/?service=' + quote('One-off House MOT'), 'navy') + button('Discuss ongoing maintenance', '/request-quote/?service=' + quote('Ongoing Property Maintenance'), 'outline') + '</div>'
    content = intro(s['name'], s['intro'], True) + '<section class="section section-white"><div class="container split service-detail"><div><span class="eyebrow">The service</span><h2>How we can help</h2>' + scope + '<h2>Careful work, considered results</h2><p>' + e(s['benefit']) + '</p><div class="notice">' + e(s['note']) + '</div>' + actions(s['quote']) + extra + '</div><div>' + placeholder(s['name']) + '<h2>What happens next?</h2><p>Tell us about the property and the work you have in mind. We’ll discuss suitability, scope and the next steps towards your free, no-obligation quotation.</p><p>Materials, timing and any preparation needed will be discussed for your individual job.</p></div></div></section><section class="section"><div class="container"><span class="eyebrow">More ways we can help</span><h2>Related services</h2>' + cards([other for other in services if other != s][:2]) + '</div></section>' + cta()
    page('/services/' + s['slug'] + '/', s['name'] + ' in Cheshire', s['intro'], content)

def contact_details():
    return f'''<div class="contact-card"><h3>Give us a call</h3><a class="contact-phone" href="{e(business['phoneHref'])}">{e(business['phone'])}</a></div><div class="contact-card"><h3>Send an email</h3><a href="mailto:{e(business['email'])}">{e(business['email'])}</a></div><div class="contact-card"><h3>Where we work</h3><p>{e(business['area'])}. Share your postcode to discuss coverage.</p></div><div class="contact-card"><h3>Stay in touch</h3><a href="{e(business['facebook'])}">Thomas Property Services on Facebook ↗</a></div>'''

page('/contact/', 'Contact us', 'Call 07410 928465 or email Thomas Property Services to discuss property care and free quotations across Cheshire and surrounding areas.', intro('Let’s talk about your property.', 'A room to refresh, outdoor surfaces to clean or a list of maintenance jobs? Tell us what you have in mind.') + '<section class="section"><div class="container split service-detail"><div><h2>A conversation is a good place to start.</h2><p>Contact us by telephone or email to discuss your project. We aim to respond to enquiries within 48 hours. For a more urgent enquiry, please call.</p>' + contact_details() + '</div><aside class="form-panel"><span class="eyebrow">Your next step</span><h2>Request a free quote</h2><p>Have a service in mind? The quotation page shows the details that will help us understand the job.</p><ul class="checklist"><li>What work is needed?</li><li>Where is the property?</li><li>When would you like to get started?</li></ul>' + button() + '<div class="notice">Development preview: online enquiries are not connected yet. Please telephone or email us.</div></aside></div></section>' + cta())

options = ['Painting and Decorating', 'Gloss Work and Wood Finishing', 'Property Improvements', 'Jet Washing', 'One-off House MOT', 'Ongoing Property Maintenance', 'Other / Not Sure']
form = '''<div class="form-panel"><h2>Your project details</h2><p id="form-status" class="notice">Development layout only. Online submission is unavailable until Phase 2. Nothing entered here is sent or stored. To request a quotation now, please call or email.</p><div role="group" aria-describedby="form-status"><fieldset><legend>Enquiry form preview</legend><div class="fields"><div class="field-wide"><label for="name">Full name (required)</label><input id="name" name="name" autocomplete="name" maxlength="100" required></div><div><label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="email" maxlength="254" aria-describedby="contact-hint"></div><div><label for="phone">Telephone number</label><input id="phone" name="phone" type="tel" autocomplete="tel" maxlength="30" aria-describedby="contact-hint"></div><p class="hint field-wide" id="contact-hint">At least one contact method will be required. An email acknowledgement will only be possible if you supply an email address.</p><div class="field-wide"><label for="service">Service required (required)</label><select id="service" name="service" required><option value="">Select a service</option>''' + ''.join(f'<option value="{e(o)}">{e(o)}</option>' for o in options) + '''</select></div><div class="field-wide"><label for="description">Short description of the work (required)</label><textarea id="description" name="description" maxlength="3000" required></textarea></div></div><details><summary>Additional information (optional)</summary><div class="fields"><div><label for="postcode">Property postcode</label><input id="postcode" name="postcode" autocomplete="postal-code" maxlength="12"></div><div><label for="timeframe">Preferred timeframe</label><input id="timeframe" name="timeframe" placeholder="e.g. this autumn" maxlength="100"></div><div class="field-wide"><label for="details">Additional details</label><textarea id="details" name="details" maxlength="3000"></textarea></div></div></details></fieldset><p class="hint">Read our <a href="/privacy-policy/">draft privacy notice</a>. Do not enter sensitive information into this development preview.</p><button class="button button-navy" type="button" disabled>Online submission coming in Phase 2</button></div></div>'''
page('/request-quote/', 'Request a free quote', 'Discuss your painting, decorating or property maintenance project. Free, no-obligation quotations from Thomas Property Services in Cheshire.', intro('Your property. Your next project.', 'Request a free, no-obligation quotation. Use the details below to plan your enquiry, then call or email us while online submission is being prepared.') + '<section class="section"><div class="container split service-detail"><div><span class="eyebrow">No obligation, just a conversation</span><h2>Tell us what you have in mind.</h2><p>A short description of the work and a way to get in touch are a good starting point. The scope, materials and timing will be discussed for your project.</p>' + contact_details() + '</div>' + form + '</div></section>')

faqs = [
    ('Which areas do you cover?', 'Cheshire and surrounding areas. Please share your postcode so we can discuss coverage for your property.'),
    ('Are quotations free?', 'Yes. Quotations are free and no-obligation.'),
    ('How long does it take to receive a reply?', 'We aim to respond to enquiries within 48 hours. Please telephone for a more urgent enquiry.'),
    ('Do you provide materials and equipment?', 'Materials and equipment arrangements depend on the work. Please discuss these as part of your quotation.'),
    ('Do you work with landlords and letting agents?', 'Yes. Landlords and letting agents can enquire about property improvements, one-off maintenance visits and ongoing upkeep arrangements.'),
    ('Do you undertake commercial work?', 'Commercial businesses can enquire about the advertised services. Suitability and scope are discussed for each job.'),
    ('Can I enquire about ongoing property maintenance?', 'Yes. Please select ongoing property maintenance on the quotation layout or contact us directly. The scope, frequency and terms still need to be agreed.'),
    ('How can I request a quotation?', 'Call 07410 928465 or email thomaspropertyservicesuk@gmail.com. Online quotation submission will be connected in Phase 2.')
]
page('/faqs/', 'Frequently asked questions', 'Find answers about service areas, free quotations, materials and landlord maintenance from Thomas Property Services.', intro('A few useful answers.', 'Practical information to help you plan your enquiry.') + '<section class="section"><div class="container faq-list">' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in faqs) + '</div></section>' + cta())

privacy = '''<section class="section"><div class="container prose"><p class="notice">Development draft — operator review required before launch. Legal identity, retention periods and future enquiry processors remain to be confirmed.</p><h2>This development website</h2><p>The online enquiry form is a layout preview. Form entries are not transmitted or stored by this website. No analytics, advertising cookies or external embedded content are configured.</p><h2>Contacting the business</h2><p>If you telephone or email Thomas Property Services, the information you provide will be used to respond to your enquiry and discuss the requested work. Email is received at the published Gmail address. The operator must confirm the applicable lawful basis, retention periods, processor arrangements and any further uses before publication.</p><h2>External links</h2><p>Links to Facebook, your email application and your telephone application open services governed by their own privacy practices. Facebook content is not embedded here.</p><h2>Your information</h2><p>To ask about the use of your information, contact <a href="mailto:thomaspropertyservicesuk@gmail.com">thomaspropertyservicesuk@gmail.com</a>. The final notice must explain applicable information rights and complaint routes.</p><h2>Before online enquiries launch</h2><p>This notice must be updated to describe the confirmed hosting, spam protection and email providers, data retention and rights procedures. Additional analytics or tracking must be reviewed before activation.</p></div></section>'''
page('/privacy-policy/', 'Privacy policy — development draft', 'Development privacy notice describing the current local website and outstanding privacy information before launch.', intro('Privacy policy', 'A draft notice for the Phase 1 development website.') + privacy)
page('/404.html', 'Page not found', 'This page could not be found. Return to Thomas Property Services or contact us about your property.', intro('This page could not be found.', 'The page may have moved, or the address may be incorrect.') + '<section class="section"><div class="container">' + button('Return to the homepage', '/', 'navy') + '</div></section>')

# Development is deliberately not indexable. A production sitemap is a later release task.
(OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n', encoding='utf-8')
(OUT / '_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Content-Security-Policy: default-src \'self\'; script-src \'self\'; style-src \'self\'; img-src \'self\'; object-src \'none\'; base-uri \'none\'; frame-ancestors \'none\'; form-action \'none\'\n', encoding='utf-8')
print(f'Built {len(routes)} pages in {OUT}')
