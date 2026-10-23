package com.carolinabarreiro.swifttojava.guide;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
}
