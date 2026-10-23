package com.carolinabarreiro.swifttojava;

import com.carolinabarreiro.swifttojava.Analyzer.Finding;
import com.carolinabarreiro.swifttojava.Analyzer.Report;
import com.carolinabarreiro.swifttojava.guide.Guide.*;
import com.carolinabarreiro.swifttojava.guide.Guide;

/** Markdown renderings for agents: llms.txt, llms-full.txt, single mappings, analyze reports. */
public final class Docs {

    private final Guide guide;

    public Docs(Guide guide) {
        this.guide = guide;
    }

    public String llmsTxt(String base) {
        var info = guide.info();
        var sb = new StringBuilder();
        sb.append("# ").append(info.title()).append("\n\n");
        sb.append("> ").append(info.description()).append(" ")
          .append(guide.mappings().size()).append(" mappings across ")
          .append(guide.categories().size()).append(" categories. Java baseline: ")
          .append(info.javaBaseline()).append(". Public, no auth, JSON by default, add ?format=md for Markdown.\n\n");

        sb.append("Use this API when converting Swift code to Java, or when a Swift developer asks for the Java equivalent of a Swift idiom. ")
          .append("It returns curated, deterministic mappings with examples and pitfalls; it does not translate code for you.\n\n");

        sb.append("## Recommended workflow\n\n");
        sb.append("1. Porting a Swift file: `POST ").append(base).append("/api/analyze` with the Swift source as text/plain. ")
          .append("You get every detected construct, the lines it occurs on, its Java mapping and its pitfalls, ordered by risk, plus the relevant checklist items.\n");
        sb.append("2. One idiom (\"what is guard let in Java?\"): `GET ").append(base).append("/api/search?q=guard+let`. Raw Swift syntax works too: `q=??`, `q=$0`, `q=inout`.\n");
        sb.append("3. Full detail for one mapping: `GET ").append(base).append("/api/mappings/{id}` (add `?format=md` to paste into context).\n");
        sb.append("4. Before finishing a port: `GET ").append(base).append("/api/checklist`.\n\n");

        sb.append("## Endpoints\n\n");
        sb.append("- [API index](").append(base).append("/api): machine-readable list of endpoints\n");
        sb.append("- [OpenAPI spec](").append(base).append("/openapi.json)\n");
        sb.append("- [Full guide as JSON](").append(base).append("/api/guide)\n");
        sb.append("- [Categories](").append(base).append("/api/categories)\n");
        sb.append("- [All mappings](").append(base).append("/api/mappings): filter with `category`, `risk` (high|medium|low), `tag`\n");
        sb.append("- [Checklist](").append(base).append("/api/checklist)\n");
        sb.append("- [Agent skill](").append(base).append("/SKILL.md)\n");
        sb.append("- [Everything in one Markdown file](").append(base).append("/llms-full.txt)\n\n");

        sb.append("## Categories\n\n");
        for (Category c : guide.categories()) {
            sb.append("- [").append(c.title()).append("](").append(base).append("/api/categories/").append(c.id())
              .append("): ").append(c.summary()).append(" (").append(c.mappingCount()).append(")\n");
        }

        sb.append("\n## High-risk mappings (most common sources of bugs)\n\n");
        for (Mapping m : guide.filter(null, Guide.Risk.HIGH, null)) {
            sb.append("- [").append(m.title()).append("](").append(base).append("/api/mappings/").append(m.id())
              .append("?format=md): ").append(m.summary()).append("\n");
        }
        return sb.toString();
    }

    public String llmsFull(String base) {
        var sb = new StringBuilder(llmsTxt(base));
        sb.append("\n---\n\n# All mappings\n");
        for (Category c : guide.categories()) {
            sb.append("\n## ").append(c.title()).append("\n\n");
            for (Mapping m : guide.filter(c.id(), null, null)) {
                sb.append(mapping(m, 3)).append("\n");
            }
        }
        sb.append("\n## Translation checklist\n\n");
        guide.checklist().forEach(c -> sb.append("- [ ] ").append(c.text()).append("\n"));
        return sb.toString();
    }

    public String mapping(Mapping m, int level) {
        String h = "#".repeat(level);
        var sb = new StringBuilder();
        sb.append(h).append(' ').append(m.title()).append("\n\n");
        sb.append("- id: `").append(m.id()).append("`\n");
        sb.append("- risk: ").append(m.risk().name().toLowerCase()).append("\n");
        sb.append("- Swift: `").append(m.swift()).append("`\n");
        sb.append("- Java: `").append(m.java()).append("`\n");
        if (m.since() != null) sb.append("- Requires: ").append(m.since()).append("\n");
        sb.append("\n").append(m.summary()).append("\n");
        if (m.swiftExample() != null) {
            sb.append("\n```swift\n").append(m.swiftExample()).append("\n```\n");
        }
        if (m.javaExample() != null) {
            sb.append("\n```java\n").append(m.javaExample()).append("\n```\n");
        }
        if (!m.gotchas().isEmpty()) {
            sb.append("\nWatch out:\n");
            m.gotchas().forEach(g -> sb.append("- ").append(g).append("\n"));
        }
        if (!m.related().isEmpty()) {
            sb.append("\nRelated: ").append(String.join(", ", m.related().stream().map(r -> "`" + r + "`").toList())).append("\n");
        }
        return sb.toString();
    }

    public String report(Report r) {
        var sb = new StringBuilder("# Swift → Java analysis\n\n");
        var s = r.summary();
        sb.append(s.constructsFound()).append(" constructs found in ").append(s.linesAnalyzed())
          .append(" lines (high: ").append(s.byRisk().get("high"))
          .append(", medium: ").append(s.byRisk().get("medium"))
          .append(", low: ").append(s.byRisk().get("low")).append(").\n\n");
        sb.append("_").append(r.note()).append("_\n");
        for (Finding f : r.findings()) {
            sb.append("\n## [").append(f.risk().name().toLowerCase()).append("] ").append(f.title())
              .append(" (`").append(f.mappingId()).append("`)\n\n");
            sb.append("Swift `").append(f.swift()).append("` → Java `").append(f.java()).append("`\n\n");
            sb.append(f.summary()).append("\n\n");
            sb.append("Lines: ");
            sb.append(String.join(", ", f.lines().stream().map(l -> "L" + l.line() + " `" + l.code() + "`").toList()));
            if (f.occurrences() > f.lines().size()) sb.append(" …");
            sb.append("\n");
            if (!f.gotchas().isEmpty()) {
                sb.append("\n");
                f.gotchas().forEach(g -> sb.append("- ").append(g).append("\n"));
            }
        }
        if (!r.checklist().isEmpty()) {
            sb.append("\n## Checklist\n\n");
            r.checklist().forEach(c -> sb.append("- [ ] ").append(c.text()).append("\n"));
        }
        return sb.toString();
    }
}
