package com.carolinabarreiro.swifttojava.analyze;

import com.carolinabarreiro.swifttojava.guide.Guide;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class AnalyzeConfig {
    @Bean
    Analyzer analyzer(Guide guide) { return new Analyzer(guide); }
}
