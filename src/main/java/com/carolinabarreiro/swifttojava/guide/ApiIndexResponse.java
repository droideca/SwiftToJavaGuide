package com.carolinabarreiro.swifttojava.guide;

import java.util.List;

// The entry point for agents: what the API is, where the docs are, and every endpoint with its purpose.
record ApiIndexResponse(
        String name,
        String version,
        String javaBaseline,
        String description,
        String auth,
        String formats,
        Docs docs,
        List<Endpoint> endpoints,
        Stats stats) {

    record Docs(String llms, String llmsFull, String openapi, String skill) {
        static Docs at(String base) {
            return new Docs(base + "/llms.txt", base + "/llms-full.txt", base + "/openapi.json", base + "/SKILL.md");
        }
    }

    record Endpoint(String method, String path, String purpose) {}

    record Stats(int mappings, int categories, List<String> tags) {}

    static final List<Endpoint> ENDPOINTS = List.of(
            new Endpoint("POST", "/api/analyze", "Detect Swift constructs in source code and return the matching Java mappings, by line and risk. Body: Swift source (text/plain) or {\"code\": ...}."),
            new Endpoint("GET", "/api/search?q={query}&limit={1-50}", "Ranked search by concept or raw Swift syntax (e.g. 'guard let', '??', 'inout')."),
            new Endpoint("GET", "/api/mappings/{id}", "One mapping with examples, pitfalls and related mappings."),
            new Endpoint("GET", "/api/mappings?category=&risk=&tag=", "List and filter mappings."),
            new Endpoint("GET", "/api/categories", "Categories with mapping counts."),
            new Endpoint("GET", "/api/categories/{id}", "One category with its mappings."),
            new Endpoint("GET", "/api/checklist", "Final review checklist for a Swift → Java port."),
            new Endpoint("GET", "/api/guide", "The whole dataset in one response."));

    static ApiIndexResponse of(Guide guide, String base) {
        Guide.Info info = guide.info();
        return new ApiIndexResponse(
                info.title(),
                info.version(),
                info.javaBaseline(),
                info.description(),
                "none",
                "JSON by default; add ?format=md for Markdown on mapping, category, search, checklist and analyze endpoints.",
                Docs.at(base),
                ENDPOINTS,
                new Stats(guide.mappings().size(), guide.categories().size(), guide.allTags()));
    }
}
