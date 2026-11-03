package com.carolinabarreiro.swifttojava.docs;

import com.carolinabarreiro.swifttojava.web.BaseUrl;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;

// The files agents look for. These mappings take priority over the copies in resources/static,
// which Spring would otherwise serve as-is, with {{BASE_URL}} left unfilled.
@RestController
class DocsController {
    static final String TEXT = MediaType.TEXT_PLAIN_VALUE + ";charset=UTF-8";

    private final Docs docs;
    private final BaseUrl baseUrl;
    private final String skillTemplate = read("static/SKILL.md");
    private final String openapiTemplate = read("static/openapi.json");

    DocsController(Docs docs, BaseUrl baseUrl) {
        this.docs = docs;
        this.baseUrl = baseUrl;
    }

    @GetMapping(path = "/llms.txt", produces = TEXT)
    String llmsTxt() {
        return docs.llmsTxt(baseUrl.get());
    }

    @GetMapping(path = "/llms-full.txt", produces = TEXT)
    String llmsFull() {
        return docs.llmsFull(baseUrl.get());
    }

    @GetMapping(path = "/SKILL.md", produces = Docs.MARKDOWN)
    String skill() {
        return skillTemplate.replace("{{BASE_URL}}", baseUrl.get());
    }

    @GetMapping(path = "/openapi.json", produces = MediaType.APPLICATION_JSON_VALUE)
    String openapi() {
        return openapiTemplate.replace("{{BASE_URL}}", baseUrl.get());
    }

    private static String read(String path) {
        try {
            return new ClassPathResource(path).getContentAsString(StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException("Missing classpath resource " + path, e);
        }
    }
}
