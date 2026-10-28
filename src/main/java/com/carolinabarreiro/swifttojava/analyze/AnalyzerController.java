package com.carolinabarreiro.swifttojava.analyze;

import com.carolinabarreiro.swifttojava.guide.Guide;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class AnalyzerController {
    private final Guide guide;
    private final Analyzer analyzer;

    AnalyzerController(Guide guide, Analyzer analyzer) {          // constructor injection, no @Autowired needed
        this.guide = guide;
        this.analyzer = analyzer;
    }
}
