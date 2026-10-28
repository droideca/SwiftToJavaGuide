package com.carolinabarreiro.swifttojava.guide;

import java.util.List;

record MappingsResponse(int count, List<Guide.Mapping> mappings) {
    static MappingsResponse of(List<Guide.Mapping> mappings) {
        return new MappingsResponse(mappings.size(), mappings);
    }
}
