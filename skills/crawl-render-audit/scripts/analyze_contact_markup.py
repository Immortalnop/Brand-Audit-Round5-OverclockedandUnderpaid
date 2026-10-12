"""analyze_contact_markup.py -- contact details shown to people but not to machines.

"How do I contact X?" is answered from explicit facts. When the site shows an
email address or phone number but no structured data states one, the detail
exists only as page text, where it is easily missed or attributed to the wrong
entity.

Only the site's own contact details count, so a third-party address quoted in
user content (a package README, a forum post) never triggers this:
  - an email address counts when its domain is the site's domain (or a
    subdomain of it) and it is not a no-reply mailbox;
  - a phone number counts when it is shown on the home, contact or about page,
    or on at least two sampled pages (a footer number).
The check runs only when the site already publishes JSON-LD: a site with none
gets the no-jsonld finding, whose draft Organization markup carries the same
contact details.
"""
from collections.abc import Mapping

from check_helpers import content_pages, organization_contact, site_host as _site_host
from models import make_finding, skill_result
from structured_data import iter_nodes

_CONTACT_PROPS = ("email", "telephone", "contactPoint", "faxNumber")


def _declares_contact(pages):
    for p in pages:
        for node in iter_nodes(p.jsonld_blocks):
            if isinstance(node, Mapping) and any(node.get(k) for k in _CONTACT_PROPS):
                return True
    return False


def analyze_contact_markup(artifacts, deadline):
    pages = content_pages(artifacts, require_features=False)
    with_jsonld = [p for p in pages if p.jsonld_blocks]
    findings = []
    emails, phones = organization_contact(pages, _site_host(artifacts.site_url))
    if with_jsonld and (emails or phones) and not _declares_contact(pages):
        shown_on = [p.url for p in pages
                    if set((p.features or {}).get("contact_emails") or ()) & set(emails)
                    or set((p.features or {}).get("contact_phones") or ()) & set(phones)]
        details = ", ".join([f"email {e}" for e in emails[:2]] + [f"phone {n}" for n in phones[:2]])
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.75,
            title=f"Contact details shown on {len(shown_on)} page(s) are stated in no structured data",
            root_cause=f"The site shows {details}, but no JSON-LD node on the {len(pages)} sampled page(s) states an "
                       "email, telephone or contactPoint.",
            evidence=[{"type": "contact_signal",
                       "description": f"shown: {details}; JSON-LD present on {len(with_jsonld)} page(s) without "
                                      "email, telephone or contactPoint", "urls": shown_on[:10]}],
            affected_pages=shown_on,
            suggested_action={
                "summary": "Add email, telephone and contactPoint to the Organization JSON-LD on the homepage",
                "steps": ["Add the email address and telephone the site already shows to the Organization node",
                          "Add a contactPoint with contactType (for example 'customer service')",
                          "Write the telephone in international format (+country code)"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Contact questions can be answered from explicit facts",
                "verification": "The homepage JSON-LD carries email and telephone matching the visible values"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_contact_markup.py",
                        "rule_id": "contact-markup-missing"}))
    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"own_emails_shown": len(emails), "phones_shown": len(phones),
                                 "contact_in_structured_data": _declares_contact(pages)})
