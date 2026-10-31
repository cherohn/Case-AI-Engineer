"""Export the ordered submission documents without importing the application."""

from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import xml.etree.ElementTree as ET

import markdown
from weasyprint import CSS, HTML


ROOT = Path(__file__).resolve().parent.parent


def render_source(path, index, included, repository):
    text = path.read_text(encoding="utf-8")
    fragment = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"], output_format="xhtml",
    )
    article = ET.fromstring("<article>" + fragment + "</article>")
    article.set("id", f"document-{index}")
    article.set("class", "document example" if path.parent.name == "examples" else "document")
    heading = article.find("h1")
    title = "Project documentation" if path.name == "README.md" else "".join(heading.itertext())

    for link in article.iter("a"):
        href = link.get("href", "")
        parts = urlsplit(href)
        if parts.scheme or href.startswith("#"):
            continue
        target = (path.parent / unquote(parts.path)).resolve()
        if target in included and not parts.fragment:
            link.set("href", "#" + included[target])
        else:
            kind = "tree" if target.is_dir() else "blob"
            relative = quote(target.relative_to(ROOT).as_posix(), safe="/")
            anchor = "#" + parts.fragment if parts.fragment else ""
            link.set("href", f"{repository}/{kind}/main/{relative}{anchor}")
    for image in article.iter("img"):
        image.set("src", (path.parent / unquote(image.get("src"))).resolve().as_uri())

    return title, ET.tostring(article, encoding="unicode", method="html")


def main():
    manifest = json.loads((ROOT / "docs/submission.json").read_text(encoding="utf-8"))
    sources = [(ROOT / name).resolve() for name in manifest["sources"]]
    included = {path: f"document-{index}" for index, path in enumerate(sources, 1)}
    sections = [
        render_source(path, index, included, manifest["repository"])
        for index, path in enumerate(sources, 1)
    ]
    toc = "".join(
        f'<li><a href="#document-{index}">{index}. {escape(title)}</a></li>'
        for index, (title, content) in enumerate(sections, 1)
    )
    date = datetime.now(timezone.utc).date().isoformat()
    title = escape(manifest["title"])
    author = escape(manifest["author"])
    repository = escape(manifest["repository"], quote=True)
    content = "".join(section for heading, section in sections)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title><meta name="author" content="{author}">
<meta name="description" content="Artefact AI Engineer written case: project documentation, validation, and recorded conversations.">
</head><body>
<section class="cover">
  <p class="eyebrow">ARTEFACT · TECHNICAL CASE</p>
  <h1>{title}</h1>
  <p class="subtitle">Project documentation and recorded conversations</p>
  <div class="cover-details"><p><strong>{author}</strong></p>
  <p>{escape(manifest['role'])}</p><p>{date}</p></div>
  <p class="repository"><a href="{repository}">{repository}</a></p>
  <p class="cover-note">Python · Groq · Function calling · FastAPI</p>
</section>
<section class="contents"><h1>Contents</h1><ol>{toc}</ol>
<p>Source files are listed in <a href="{repository}/blob/main/docs/submission.json">docs/submission.json</a>.
Links to included documents navigate within this PDF; other repository links open GitHub.</p></section>
{content}
</body></html>"""
    output = ROOT / "submission" / manifest["filename"]
    output.parent.mkdir(exist_ok=True)
    document = HTML(string=html, base_url=str(ROOT)).render(
        stylesheets=[CSS(filename=ROOT / "docs/export.css")],
    )
    document.write_pdf(output, pdf_tags=True, pdf_version="1.7", optimize_images=True)
    size = output.stat().st_size
    if size >= 100 * 1024 * 1024:
        raise RuntimeError("The generated PDF exceeds the 100 MB submission limit.")
    print(f"PDF: {output}")
    print(f"{len(document.pages)} pages; {size / 1024:.1f} KB; {len(sources)} source documents.")


if __name__ == "__main__":
    main()
