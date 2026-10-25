package com.carolinabarreiro.swifttojava.guide;

import com.fasterxml.jackson.annotation.JsonUnwrapped;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

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
        List<Guide.ChecklistItem> checklist) {}

record CategoryResponse(@JsonUnwrapped Guide.Category category, List<Guide.Mapping> Mapping) {}

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
}
