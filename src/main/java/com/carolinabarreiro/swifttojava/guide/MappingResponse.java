package com.carolinabarreiro.swifttojava.guide;

import com.fasterxml.jackson.annotation.JsonUnwrapped;

import java.util.List;

record MappingResponse(@JsonUnwrapped Guide.Mapping mapping, List<RelatedMapping> relatedMappings) { }
