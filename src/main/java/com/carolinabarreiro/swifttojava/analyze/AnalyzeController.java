package com.carolinabarreiro.swifttojava.analyze;

import com.carolinabarreiro.swifttojava.docs.Docs;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.util.UriComponentsBuilder;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/api")
class AnalyzeController {
    static final int MAX_BODY_BYTES = 200_000;
    static final MediaType MARKDOWN = MediaType.parseMediaType(Docs.MARKDOWN);

    private final Analyzer analyzer;
    private final Docs docs;

    record AnalyzeRequest(@NotBlank String code) { }

    AnalyzeController(Analyzer analyzer, Docs docs) {          // constructor injection, no @Autowired needed
        this.analyzer = analyzer;
        this.docs = docs;
    }

    // No `params = "format=md"` here: checking it calls request.getParameter(), and for a form-urlencoded POST
    // Tomcat answers that by consuming the whole body as form fields, so analyzeForm would read nothing.
    // Each handler reads the format from the raw query string instead and builds the response itself.

    @PostMapping(path = "/analyze")
    ResponseEntity<?> analyzeText(@RequestBody @NotBlank String code, HttpServletRequest request) {
        return respond(validateAndAnalyze(code), request);
    }

    @PostMapping(path = "/analyze", consumes = MediaType.APPLICATION_JSON_VALUE)
    ResponseEntity<?> analyzeJson(@RequestBody @Valid AnalyzeRequest body, HttpServletRequest request) {
        return respond(validateAndAnalyze(body.code()), request);
    }

    @PostMapping(path = "/analyze", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE)
    ResponseEntity<?> analyzeForm(HttpServletRequest request) throws IOException {
        String code = new String(request.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        return respond(validateAndAnalyze(code), request);
    }

    private ResponseEntity<?> respond(Analyzer.Report report, HttpServletRequest request) {
        if (wantsMarkdown(request)) {
            return ResponseEntity.ok().contentType(MARKDOWN).body(docs.report(report));
        }
        return ResponseEntity.ok(report);
    }

    private static boolean wantsMarkdown(HttpServletRequest request) {
        String format = UriComponentsBuilder.newInstance().query(request.getQueryString()).build()
                .getQueryParams().getFirst("format");
        return "md".equals(format) || "markdown".equals(format);
    }

    private Analyzer.Report validateAndAnalyze(String code) {
        if (code.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "The content is empty");
        }
        if (code.getBytes(StandardCharsets.UTF_8).length > MAX_BODY_BYTES) {
            throw new ResponseStatusException(HttpStatus.CONTENT_TOO_LARGE, "Maximum body size is " + MAX_BODY_BYTES + " bytes");
        }
        return analyzer.analyze(code);
    }
}
