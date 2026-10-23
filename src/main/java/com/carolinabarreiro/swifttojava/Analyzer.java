package com.carolinabarreiro.swifttojava;

import com.carolinabarreiro.swifttojava.guide.Guide.*;
import com.carolinabarreiro.swifttojava.guide.Guide;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Matcher;

/**
 * Deterministic Swift-construct detector. It does NOT translate code: it tells the caller
 * which guide mappings apply to which lines, so an agent can translate with the right rules.
 */
public final class Analyzer {

    public static final int MAX_LINES_PER_FINDING = 5;

    public record Line(int line, String code) {}

    public record Finding(String mappingId, String title, Risk risk, String category,
                          String swift, String java, String summary, List<String> gotchas,
                          int occurrences, List<Line> lines, String detailUrl) {}

    public record Summary(int linesAnalyzed, int constructsFound, Map<String, Integer> byRisk) {}

    public record Report(Summary summary, List<Finding> findings, List<ChecklistItem> checklist,
                         String note) {}

    private final Guide guide;

    public Analyzer(Guide guide) {
        this.guide = guide;
    }

    public Report analyze(String swiftSource) {
        String source = stripLineComments(swiftSource.replace("\r\n", "\n"));
        String[] lines = source.split("\n", -1);
        int[] lineStarts = lineStarts(source);

        var findings = new ArrayList<Finding>();
        for (Mapping m : guide.mappings()) {
            var hitLines = new TreeMap<Integer, String>();
            int occurrences = 0;
            for (var pattern : guide.patterns(m.id())) {
                Matcher matcher = pattern.matcher(source);
                while (matcher.find()) {
                    occurrences++;
                    int lineNo = lineOf(lineStarts, matcher.start());
                    hitLines.putIfAbsent(lineNo, lines[lineNo - 1].strip());
                }
            }
            if (occurrences == 0) continue;
            var sample = hitLines.entrySet().stream()
                    .limit(MAX_LINES_PER_FINDING)
                    .map(e -> new Line(e.getKey(), e.getValue()))
                    .toList();
            findings.add(new Finding(m.id(), m.title(), m.risk(), m.category(), m.swift(), m.java(),
                    m.summary(), m.gotchas(), occurrences, sample, "/api/mappings/" + m.id()));
        }

        findings.sort(Comparator.comparing(Finding::risk)
                .thenComparing(f -> f.lines().getFirst().line()));

        var byRisk = new LinkedHashMap<String, Integer>();
        for (Risk r : Risk.values()) {
            byRisk.put(r.name().toLowerCase(), (int) findings.stream().filter(f -> f.risk() == r).count());
        }

        Set<String> found = new LinkedHashSet<>();
        findings.forEach(f -> found.add(f.mappingId()));
        var checklist = guide.checklist().stream()
                .filter(c -> c.mappingIds().stream().anyMatch(found::contains))
                .toList();

        String note = findings.isEmpty()
                ? "No known Swift constructs detected. If this is Swift code, use /api/search for specific idioms."
                : "Pattern-based detection: review each finding; it may include false positives. Resolve high-risk findings first.";

        return new Report(new Summary(lines.length, findings.size(), byRisk), findings, checklist, note);
    }

    /** Which mapping ids would fire for this text? Used by search to match raw Swift syntax like "??". */
    public Set<String> matchingIds(String text) {
        var ids = new LinkedHashSet<String>();
        for (Mapping m : guide.mappings()) {
            for (var p : guide.patterns(m.id())) {
                if (p.matcher(text).find()) { ids.add(m.id()); break; }
            }
        }
        return ids;
    }

    /** Removes // comments that are not inside a string literal. Keeps line count intact. */
    static String stripLineComments(String src) {
        var out = new StringBuilder(src.length());
        for (String line : src.split("\n", -1)) {
            boolean inString = false;
            int cut = line.length();
            for (int i = 0; i < line.length(); i++) {
                char c = line.charAt(i);
                if (c == '\\') { i++; continue; }
                if (c == '"') inString = !inString;
                if (!inString && c == '/' && i + 1 < line.length() && line.charAt(i + 1) == '/') {
                    cut = i;
                    break;
                }
            }
            out.append(line, 0, cut).append('\n');
        }
        out.setLength(out.length() - 1);
        return out.toString();
    }

    private static int[] lineStarts(String s) {
        var starts = new ArrayList<Integer>();
        starts.add(0);
        for (int i = 0; i < s.length(); i++) if (s.charAt(i) == '\n') starts.add(i + 1);
        return starts.stream().mapToInt(Integer::intValue).toArray();
    }

    private static int lineOf(int[] starts, int offset) {
        int lo = 0, hi = starts.length - 1;
        while (lo < hi) {
            int mid = (lo + hi + 1) >>> 1;
            if (starts[mid] <= offset) lo = mid; else hi = mid - 1;
        }
        return lo + 1;
    }
}
