package com.carolinabarreiro.swifttojava.docs;

import com.carolinabarreiro.swifttojava.guide.Guide;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class DocsConfig {
    @Bean
    Docs docs(Guide guide) { return new Docs(guide); }
}
