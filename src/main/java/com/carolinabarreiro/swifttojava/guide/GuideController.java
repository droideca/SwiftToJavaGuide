package com.carolinabarreiro.swifttojava.guide;

import com.fasterxml.jackson.annotation.JsonUnwrapped;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

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

@RestController
@RequestMapping("/api")
class GuideController {
    private final Guide guide;

    GuideController(Guide guide) {          // constructor injection, no @Autowired needed
        this.guide = guide;
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
}