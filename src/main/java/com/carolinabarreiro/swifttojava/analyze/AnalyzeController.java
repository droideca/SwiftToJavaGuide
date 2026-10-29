package com.carolinabarreiro.swifttojava.analyze;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/api")
class AnalyzeController {
    static final int MAX_BODY_BYTES = 200_000;

    private final Analyzer analyzer;

    record AnalyzeRequest(@NotBlank String code) { }

    AnalyzeController(Analyzer analyzer) {          // constructor injection, no @Autowired needed
        this.analyzer = analyzer;
    }

    @PostMapping(path = "/analyze")
    Analyzer.Report analyzeText(@RequestBody @NotBlank String code) {
        return validateAndAnalyze(code);
    }

    @PostMapping(path = "/analyze", consumes = MediaType.APPLICATION_JSON_VALUE)
    Analyzer.Report analyzeJson(@RequestBody @Valid AnalyzeRequest request) {
        return validateAndAnalyze(request.code());
    }

    @PostMapping(path = "/analyze", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE)
    Analyzer.Report analyzeForm(HttpServletRequest request) throws IOException {
        String code = new String(request.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        return validateAndAnalyze(code);
    }

    private Analyzer.Report validateAndAnalyze(String code) {
        if (code.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "The content is empty");
        }
        if (code.getBytes(StandardCharsets.UTF_8).length > MAX_BODY_BYTES) {
            throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Maximum body size is " + MAX_BODY_BYTES + " bytes");
        }
        return analyzer.analyze(code);
    }
}
