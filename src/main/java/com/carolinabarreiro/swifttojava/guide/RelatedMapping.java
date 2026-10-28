package com.carolinabarreiro.swifttojava.guide;

record RelatedMapping(String id, String title, String detailUrl) {
    static RelatedMapping of(Guide.Mapping mapping) {
        return new RelatedMapping(mapping.id(), mapping.title(), "/api/mappings/" + mapping.id());
    }
}
