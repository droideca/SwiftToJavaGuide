package com.carolinabarreiro.swifttojava.web;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class WebConfig {
    @Bean
    BaseUrl baseUrl(@Value("${BASE_URL:}") String configured) {   // env var, property or --BASE_URL=; empty if unset
        return new BaseUrl(configured);
    }
}
