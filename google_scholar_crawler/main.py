from datetime import datetime, timezone
from pathlib import Path
import os

import requests
import yaml

OPENALEX_API = "https://api.openalex.org"
MAILTO = "YOUR_EMAIL_ADDRESS"
PER_PAGE = 200

author_id = os.environ["OPENALEX_AUTHOR_ID"].strip()

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "gabocas.github.io OpenAlex citation updater",
    }
)

author_response = session.get(
    f"{OPENALEX_API}/authors/{author_id}",
    params={
        "select": "id,display_name,works_count,cited_by_count",
        "mailto": MAILTO,
    },
    timeout=30,
)
author_response.raise_for_status()
author = author_response.json()

works = []
cursor = "*"

while cursor:
    response = session.get(
        f"{OPENALEX_API}/works",
        params={
            "filter": f"authorships.author.id:{author_id}",
            "select": (
                "id,display_name,doi,publication_date,type,"
                "cited_by_count"
            ),
            "per-page": PER_PAGE,
            "cursor": cursor,
            "mailto": MAILTO,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    for work in payload["results"]:
        works.append(
            {
                "openalex_id": work["id"].rsplit("/", 1)[-1],
                "doi": (
                    work["doi"]
                    .removeprefix("https://doi.org/")
                    .lower()
                    if work.get("doi")
                    else None
                ),
                "title": work.get("display_name"),
                "publication_date": work.get("publication_date"),
                "type": work.get("type"),
                "citation_count": int(work.get("cited_by_count", 0)),
            }
        )

    cursor = payload["meta"].get("next_cursor")

works.sort(
    key=lambda work: (
        work["publication_date"] or "0000-00-00",
        work["citation_count"],
    ),
    reverse=True,
)

output = {
    "openalex": {
        "author_id": author_id,
        "author_name": author.get("display_name"),
        "citation_count": int(author["cited_by_count"]),
        "works_count": int(author.get("works_count", 0)),
        "retrieved_works_count": len(works),
        "updated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    },
    "works": works,
}

destination = Path("_data/citations.yml")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(
    yaml.safe_dump(
        output,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ),
    encoding="utf-8",
)

print(
    f"Retrieved {len(works)} works for {author.get('display_name')} "
    f"({author['cited_by_count']} total OpenAlex citations)."
)
