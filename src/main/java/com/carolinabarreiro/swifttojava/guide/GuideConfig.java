package com.carolinabarreiro.swifttojava.guide;

import com.carolinabarreiro.swifttojava.analyze.Analyzer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class GuideConfig {
    @Bean
    Guide guide() {
        return Guide.loadFromClasspath();   // loaded once, injected wherever needed
    }

    @Bean
    Search search(Guide guide, Analyzer analyzer) { return new Search(guide, analyzer); }
}
