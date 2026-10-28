package com.carolinabarreiro.swifttojava.guide;

import com.carolinabarreiro.swifttojava.Analyzer;
import com.carolinabarreiro.swifttojava.Search;
import com.fasterxml.jackson.annotation.JsonUnwrapped;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

@Configuration
class GuideConfig {
    @Bean
    Guide guide() {
        return Guide.loadFromClasspath();   // loaded once, injected wherever needed
    }

    @Bean
    Analyzer analyzer(Guide guide) { return new Analyzer(guide); }

    @Bean
    Search search(Guide guide, Analyzer analyzer) { return new Search(guide, analyzer); }
}

record GuideResponse(
        Guide.Info guide,
        List<Guide.Category> categories,
        List<Guide.Mapping> mappings,
        List<Guide.ChecklistItem> checklist) {
}

record CategoryResponse(@JsonUnwrapped Guide.Category category, List<Guide.Mapping> mappings) {
}

record MappingsResponse(int count, List<Guide.Mapping> mappings) {
    static MappingsResponse of(List<Guide.Mapping> mappings) {
        return new MappingsResponse(mappings.size(), mappings);
    }
}

record MappingResponse(@JsonUnwrapped Guide.Mapping mapping, List<RelatedMapping> relatedMappings) { }

record RelatedMapping(String id, String title, String detailUrl) {
    static RelatedMapping of(Guide.Mapping mapping) {
        return new RelatedMapping(mapping.id(), mapping.title(), "/api/mappings/" + mapping.id());
    }
}

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

@RestController
@RequestMapping("/api")
class GuideController {
    private final Guide guide;
    private final Search search;

    GuideController(Guide guide, Search search) {          // constructor injection, no @Autowired needed
        this.guide = guide;
        this.search = search;
    }

    @GetMapping("/categories")
    Map<String, Object> categories() {
        return Map.of("categories", guide.categories());
    }

    @GetMapping("/guide")
    GuideResponse guide() {
        return new GuideResponse(guide.info(), guide.categories(), guide.mappings(), guide.checklist());
    }

    @GetMapping("/checklist")
    Map<String, Object> checklists() {
        return Map.of("checklist", guide.checklist());
    }

    @GetMapping("/categories/{id}")
    CategoryResponse category(@PathVariable String id) {
        Guide.Category category = guide.category(id);
        if (category == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No category '" + id + "'");
        }
        return new CategoryResponse(category, guide.filter(id, null, null));
    }

    @GetMapping("/mappings")
    MappingsResponse mappings(@RequestParam(required = false) String category,
                              @RequestParam(required = false) String risk,
                              @RequestParam(required = false) String tag) {
        Guide.Risk riskEnum = null;
        if (risk != null) {
            try {
                riskEnum = Guide.Risk.valueOf(risk.toUpperCase(Locale.ROOT));
            } catch (IllegalArgumentException e) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown risk");
            }
        }

        if (category != null && guide.category(category) == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown category");
        }

        if (tag != null && !guide.allTags().contains(tag)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown tag");
        }

        return MappingsResponse.of(guide.filter(category, riskEnum, tag));
    }

    @GetMapping("/mappings/{id}")
    MappingResponse mapping(@PathVariable String id) {
        Guide.Mapping mapping = guide.mapping(id);
        if (mapping == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No mapping '" + id + "'");
        }
        List<RelatedMapping> relatedMappings = mapping.related().stream()
                .map(guide::mapping)
                .filter(Objects::nonNull)
                .map(RelatedMapping::of)
                .toList();
        return new MappingResponse(mapping, relatedMappings);
    }

    @GetMapping("/search")
    SearchResponse search(@RequestParam @NotBlank String q,
                          @RequestParam(defaultValue = "5") @Min(1) @Max(50) int limit) {
        List<Search.Hit> searchResult = search.search(q, limit);
        return SearchResponse.of(q, searchResult);
    }

    @GetMapping
    ApiIndexResponse index() {
        // TODO step 5: let a BASE_URL env var override the URL taken from the request
        String base = ServletUriComponentsBuilder.fromCurrentContextPath().toUriString();
        return ApiIndexResponse.of(guide, base);
    }
}