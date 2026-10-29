package com.carolinabarreiro.swifttojava.analyze;

import com.carolinabarreiro.swifttojava.guide.Guide;
import org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import tools.jackson.databind.cfg.CoercionAction;
import tools.jackson.databind.cfg.CoercionInputShape;
import tools.jackson.databind.type.LogicalType;

@Configuration
class AnalyzeConfig {
    @Bean
    JsonMapperBuilderCustomizer strictStrings() {
        return builder -> builder.withCoercionConfig(LogicalType.Textual, c -> c
                .setCoercion(CoercionInputShape.Integer, CoercionAction.Fail)
                .setCoercion(CoercionInputShape.Float, CoercionAction.Fail)
                .setCoercion(CoercionInputShape.Boolean, CoercionAction.Fail));
    }

    @Bean
    Analyzer analyzer(Guide guide) { return new Analyzer(guide); }
}
