package com.carolinabarreiro.swifttojava;

import com.carolinabarreiro.swifttojava.Guide.Mapping;
import com.carolinabarreiro.swifttojava.Guide.Risk;

import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Ranked keyword search. Two signals:
 *  1. weighted token overlap with title / swift / java / tags / summary / gotchas;
 *  2. the raw query run through the Swift detectors, so "??" or "guard let" find the right entry.
 */
public final class Search {

    public record Hit(String id, String title, Risk risk, String category, String swift, String java,
                      String summary, double score, String detailUrl) {}

    private static final Set<String> STOP = Set.of("a", "an", "the", "to", "in", "of", "how", "do", "i",
            "is", "what", "java", "swift", "convert", "equivalent", "for", "with", "and", "or", "my");

    private final Guide guide;
    private final Analyzer analyzer;

    public Search(Guide guide, Analyzer analyzer) {
        this.guide = guide;
        this.analyzer = analyzer;
    }

    public List<Hit> search(String query, int limit) {
        String q = query.toLowerCase(Locale.ROOT).strip();
        List<String> tokens = Arrays.stream(q.split("[^a-z0-9$?!@#]+"))
                .filter(t -> !t.isBlank() && !STOP.contains(t))
                .toList();
        Set<String> syntaxHits = analyzer.matchingIds(query);

        return guide.mappings().stream()
                .map(m -> new Hit(m.id(), m.title(), m.risk(), m.category(), m.swift(), m.java(),
                        m.summary(), score(m, q, tokens, syntaxHits), "/api/mappings/" + m.id()))
                .filter(h -> h.score() > 0)
                .sorted(Comparator.comparingDouble(Hit::score).reversed().thenComparing(Hit::id))
                .limit(limit)
                .toList();
    }

    private static double score(Mapping m, String q, List<String> tokens, Set<String> syntaxHits) {
        double s = 0;
        String title = m.title().toLowerCase(Locale.ROOT);
        String swift = m.swift().toLowerCase(Locale.ROOT);
        String java = m.java().toLowerCase(Locale.ROOT);
        String id = m.id();
        String summary = m.summary().toLowerCase(Locale.ROOT);
        String gotchas = String.join(" ", m.gotchas()).toLowerCase(Locale.ROOT);
        String examples = ((m.swiftExample() == null ? "" : m.swiftExample()) + " "
                + (m.javaExample() == null ? "" : m.javaExample())).toLowerCase(Locale.ROOT);

        if (q.length() > 2 && (swift.contains(q) || java.contains(q) || title.contains(q))) s += 10;
        if (id.equals(q.replace(' ', '-'))) s += 15;
        if (syntaxHits.contains(m.id())) s += 8;

        for (String t : tokens) {
            if (title.contains(t)) s += 5;
            if (swift.contains(t)) s += 4;
            if (java.contains(t)) s += 4;
            if (id.contains(t)) s += 3;
            if (m.tags().contains(t) || m.tags().contains(t + "s")) s += 3;
            if (summary.contains(t)) s += 2;
            if (gotchas.contains(t)) s += 1;
            if (examples.contains(t)) s += 0.5;
        }
        return s;
    }
}
