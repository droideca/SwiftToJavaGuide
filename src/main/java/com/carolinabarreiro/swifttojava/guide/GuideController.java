package com.carolinabarreiro.swifttojava.guide;

import com.carolinabarreiro.swifttojava.docs.Docs;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

@RestController
@RequestMapping("/api")
class GuideController {
    private final Guide guide;
    private final Search search;
    private final Docs docs;

    GuideController(Guide guide, Search search, Docs docs) {          // constructor injection, no @Autowired needed
        this.guide = guide;
        this.search = search;
        this.docs = docs;
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
    Map<String, Object> checklist() {
        return Map.of("checklist", guide.checklist());
    }

    @GetMapping(path = "/checklist", params = "format=md", produces = Docs.MARKDOWN)
    String checklistMarkdown() {
        return docs.checklist();
    }

    @GetMapping("/categories/{id}")
    CategoryResponse category(@PathVariable String id) {
        return new CategoryResponse(findCategory(id), guide.filter(id, null, null));
    }

    @GetMapping(path = "/categories/{id}", params = "format=md", produces = Docs.MARKDOWN)
    String categoryMarkdown(@PathVariable String id) {
        return docs.category(findCategory(id), guide.filter(id, null, null));
    }

    @GetMapping("/mappings")
    MappingsResponse mappings(@RequestParam(required = false) String category,
                              @RequestParam(required = false) String risk,
                              @RequestParam(required = false) String tag) {
        return MappingsResponse.of(filterMappings(category, risk, tag));
    }

    @GetMapping(path = "/mappings", params = "format=md", produces = Docs.MARKDOWN)
    String mappingsMarkdown(@RequestParam(required = false) String category,
                            @RequestParam(required = false) String risk,
                            @RequestParam(required = false) String tag) {
        return docs.mappings(filterMappings(category, risk, tag));
    }

    @GetMapping("/mappings/{id}")
    MappingResponse mapping(@PathVariable String id) {
        Guide.Mapping mapping = findMapping(id);
        List<RelatedMapping> relatedMappings = mapping.related().stream()
                .map(guide::mapping)
                .filter(Objects::nonNull)
                .map(RelatedMapping::of)
                .toList();
        return new MappingResponse(mapping, relatedMappings);
    }

    @GetMapping(path = "/mappings/{id}", params = "format=md", produces = Docs.MARKDOWN)
    String mappingMarkdown(@PathVariable String id) {
        return docs.mapping(findMapping(id), 1);
    }

    @GetMapping("/search")
    SearchResponse search(@RequestParam @NotBlank String q,
                          @RequestParam(defaultValue = "5") @Min(1) @Max(50) int limit) {
        List<Search.Hit> searchResult = search.search(q, limit);
        return SearchResponse.of(q, searchResult);
    }

    @GetMapping(path = "/search", params = "format=md", produces = Docs.MARKDOWN)
    String searchMarkdown(@RequestParam @NotBlank String q,
                          @RequestParam(defaultValue = "5") @Min(1) @Max(50) int limit) {
        List<Guide.Mapping> results = search.search(q, limit).stream()
                .map(hit -> guide.mapping(hit.id()))
                .toList();
        return docs.search(q, results);
    }

    @GetMapping
    ApiIndexResponse index() {
        // TODO step 5: let a BASE_URL env var override the URL taken from the request
        String base = ServletUriComponentsBuilder.fromCurrentContextPath().toUriString();
        return ApiIndexResponse.of(guide, base);
    }

    // Lookups and validation shared by the JSON and Markdown handlers, so both formats fail the same way.

    private Guide.Category findCategory(String id) {
        Guide.Category category = guide.category(id);
        if (category == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No category '" + id + "'");
        }
        return category;
    }

    private Guide.Mapping findMapping(String id) {
        Guide.Mapping mapping = guide.mapping(id);
        if (mapping == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "No mapping '" + id + "'");
        }
        return mapping;
    }

    private List<Guide.Mapping> filterMappings(String category, String risk, String tag) {
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

        return guide.filter(category, riskEnum, tag);
    }
}
