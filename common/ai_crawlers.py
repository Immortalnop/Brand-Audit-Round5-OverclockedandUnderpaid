"""AI and search crawlers whose robots.txt access the audit reads, each labelled
with the purpose its operator documents for it.

  search      fetches pages for an AI search index or answer engine; blocking it
              keeps the site out of that assistant's answers and citations.
  training    collects content for model training (or is the robots.txt token
              that controls such use); blocking it is an opt-out, not a loss of
              search visibility.
  user_fetch  fetches a page when a user asks an assistant to read it; blocking
              it stops the assistant from opening the page on request.

A crawler whose documented use mixes product answers with model training is
labelled training: the label decides severity, and the lower one is the safe
choice when the operator's own description is not clear-cut. Only robots.txt
rules are read; no request is ever made as any of these crawlers.
"""
from types import MappingProxyType

SEARCH = "search"
TRAINING = "training"
USER_FETCH = "user_fetch"
# A name not in CRAWLERS (an older snapshot or a caller's own list).
UNCLASSIFIED = "unclassified"

PURPOSE_LABELS = MappingProxyType({
    SEARCH: "AI search",
    TRAINING: "model training",
    USER_FETCH: "user-requested fetch",
    UNCLASSIFIED: "unclassified",
})

# (robots.txt product token, operator, purpose), in report order.
CRAWLERS = (
    ("OAI-SearchBot", "OpenAI", SEARCH),
    ("ChatGPT-User", "OpenAI", USER_FETCH),
    ("GPTBot", "OpenAI", TRAINING),
    ("Claude-SearchBot", "Anthropic", SEARCH),
    ("Claude-User", "Anthropic", USER_FETCH),
    ("ClaudeBot", "Anthropic", TRAINING),
    ("PerplexityBot", "Perplexity", SEARCH),
    ("Perplexity-User", "Perplexity", USER_FETCH),
    ("Googlebot", "Google", SEARCH),
    ("Google-Extended", "Google", TRAINING),
    ("Applebot", "Apple", SEARCH),
    ("Applebot-Extended", "Apple", TRAINING),
    ("Amazonbot", "Amazon", TRAINING),
    ("Meta-ExternalAgent", "Meta", TRAINING),
    ("Meta-ExternalFetcher", "Meta", USER_FETCH),
    ("MistralAI-User", "Mistral AI", USER_FETCH),
    ("CCBot", "Common Crawl", TRAINING),
    ("Bytespider", "ByteDance", TRAINING),
)

AI_CRAWLER_NAMES = tuple(name for name, _, _ in CRAWLERS)
PURPOSE = MappingProxyType({name: purpose for name, _, purpose in CRAWLERS})
OPERATOR = MappingProxyType({name: operator for name, operator, _ in CRAWLERS})
SEARCH_CRAWLERS = frozenset(name for name, _, purpose in CRAWLERS if purpose == SEARCH)


def purpose_of(name):
    """The purpose of a crawler name; UNCLASSIFIED for a name not in the list."""
    return PURPOSE.get(name, UNCLASSIFIED)


def group_by_purpose(names):
    """{purpose: [names]} in the fixed purpose order search, user_fetch,
    training, unclassified; names in CRAWLERS order, unlisted names last in
    alphabetical order."""
    order = {name: i for i, name in enumerate(AI_CRAWLER_NAMES)}
    out = {}
    for purpose in (SEARCH, USER_FETCH, TRAINING, UNCLASSIFIED):
        members = sorted((n for n in set(names) if purpose_of(n) == purpose),
                         key=lambda n: (order.get(n, len(order)), n))
        if members:
            out[purpose] = members
    return out


def describe(names):
    """'AI search: A, B; model training: C' for a set of crawler names."""
    return "; ".join(f"{PURPOSE_LABELS[purpose]}: {', '.join(members)}"
                     for purpose, members in group_by_purpose(names).items())
