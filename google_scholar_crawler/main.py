from datetime import datetime, timezone
from pathlib import Path
import os

import requests
import yaml

author_id = os.environ["OPENALEX_AUTHOR_ID"].strip()
api_url = f"https://api.openalex.org/authors/{author_id}"

response = requests.get(
    api_url,
    params={
        "select": "id,display_name,works_count,cited_by_count",
        "mailto": "gabriel.castrillon@tum.de",
    },
    timeout=30,
)
response.raise_for_status()

author = response.json()

if "cited_by_count" not in author:
    raise RuntimeError(
        f"OpenAlex returned no cited_by_count field for author {author_id}."
    )

output = {
    "openalex": {
        "author_id": author_id,
        "author_name": author.get("display_name"),
        "citation_count": int(author["cited_by_count"]),
        "works_count": int(author.get("works_count", 0)),
        "updated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }
}

destination = Path("_data/citations.yml")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(
    yaml.safe_dump(output, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)

print(
    f"{output['openalex']['author_name']}: "
    f"{output['openalex']['citation_count']} OpenAlex citations"
)
