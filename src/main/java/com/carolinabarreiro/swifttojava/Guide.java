package com.carolinabarreiro.swifttojava;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Pattern;

/** The loaded, indexed dataset. Immutable after construction. */
public final class Guide {

    public enum Risk { HIGH, MEDIUM, LOW }

    public record Info(String title, String version, String javaBaseline, String description) {}

    public record Category(String id, String title, String summary, int mappingCount) {}

    public record Mapping(
            String id, String category, String title,
            String swift, String java, String summary,
            Risk risk, List<String> detect,
            String swiftExample, String javaExample,
            List<String> gotchas, List<String> related, List<String> tags,
            String since) {}

    public record ChecklistItem(String id, String text, List<String> mappingIds) {}

    private final Info info;
    private final List<Category> categories;
    private final Map<String, Mapping> mappings;              // insertion-ordered by id
    private final Map<String, List<Pattern>> detectPatterns;  // compiled once
    private final List<ChecklistItem> checklist;

    private Guide(Info info, List<Category> categories, Map<String, Mapping> mappings,
                  Map<String, List<Pattern>> detectPatterns, List<ChecklistItem> checklist) {
        this.info = info;
        this.categories = categories;
        this.mappings = mappings;
        this.detectPatterns = detectPatterns;
        this.checklist = checklist;
    }

    public static Guide loadFromClasspath() {
        try (InputStream in = Guide.class.getResourceAsStream("/data/mappings.json")) {
            Objects.requireNonNull(in, "data/mappings.json not found on classpath");
            return fromJson(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) {
            throw new java.io.UncheckedIOException(e);
        }
    }

    @SuppressWarnings("unchecked")
    public static Guide fromJson(String json) {
        var root = (Map<String, Object>) Json.parse(json);
        var g = (Map<String, Object>) root.get("guide");
        var info = new Info(str(g, "title"), str(g, "version"), str(g, "javaBaseline"), str(g, "description"));

        var categories = new ArrayList<Category>();
        for (Object o : (List<Object>) root.get("categories")) {
            var c = (Map<String, Object>) o;
            categories.add(new Category(str(c, "id"), str(c, "title"), str(c, "summary"),
                    ((Number) c.get("mappingCount")).intValue()));
        }

        var mappings = new LinkedHashMap<String, Mapping>();
        var patterns = new LinkedHashMap<String, List<Pattern>>();
        for (Object o : (List<Object>) root.get("mappings")) {
            var m = (Map<String, Object>) o;
            var mapping = new Mapping(
                    str(m, "id"), str(m, "category"), str(m, "title"),
                    str(m, "swift"), str(m, "java"), str(m, "summary"),
                    Risk.valueOf(str(m, "risk").toUpperCase()), strs(m, "detect"),
                    str(m, "swiftExample"), str(m, "javaExample"),
                    strs(m, "gotchas"), strs(m, "related"), strs(m, "tags"),
                    str(m, "since"));
            mappings.put(mapping.id(), mapping);
            patterns.put(mapping.id(), mapping.detect().stream()
                    .map(p -> Pattern.compile(p, Pattern.MULTILINE))
                    .toList());
        }

        var checklist = new ArrayList<ChecklistItem>();
        for (Object o : (List<Object>) root.get("checklist")) {
            var c = (Map<String, Object>) o;
            checklist.add(new ChecklistItem(str(c, "id"), str(c, "text"), strs(c, "mappingIds")));
        }
        return new Guide(info, List.copyOf(categories), mappings, patterns, List.copyOf(checklist));
    }

    private static String str(Map<String, Object> m, String key) {
        return (String) m.get(key);
    }

    @SuppressWarnings("unchecked")
    private static List<String> strs(Map<String, Object> m, String key) {
        var list = (List<Object>) m.get(key);
        return list == null ? List.of() : list.stream().map(String.class::cast).toList();
    }

    // ------------------------------------------------------------------ queries

    public Info info() { return info; }

    public List<Category> categories() { return categories; }

    public List<Mapping> mappings() { return List.copyOf(mappings.values()); }

    public List<ChecklistItem> checklist() { return checklist; }

    public Mapping mapping(String id) { return mappings.get(id); }

    public Category category(String id) {
        return categories.stream().filter(c -> c.id().equals(id)).findFirst().orElse(null);
    }

    public List<Pattern> patterns(String mappingId) {
        return detectPatterns.getOrDefault(mappingId, List.of());
    }

    public List<Mapping> filter(String category, Risk risk, String tag) {
        return mappings.values().stream()
                .filter(m -> category == null || m.category().equals(category))
                .filter(m -> risk == null || m.risk() == risk)
                .filter(m -> tag == null || m.tags().contains(tag))
                .toList();
    }

    public List<String> allTags() {
        return mappings.values().stream()
                .flatMap(m -> m.tags().stream())
                .distinct()
                .sorted(Comparator.naturalOrder())
                .toList();
    }
}
