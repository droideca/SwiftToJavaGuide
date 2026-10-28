package com.carolinabarreiro.swifttojava.guide;

import java.util.List;

record SearchResponse(String query, int count, List<Search.Hit> results, String hint) {
    // Note to Caro: Hint is for the agent.
    // The longer text is also more useful to an agent: it says what to try next and where to go (/api/categories).
    static SearchResponse of(String query, List<Search.Hit> searchResult) {
        String hint = null;
        if (searchResult.isEmpty()) {
            hint = "No results. Try a broader term, a Swift keyword (e.g. 'inout'), or browse /api/categories.";
        }
        return new SearchResponse(query, searchResult.size(), searchResult, hint);
    }
}
