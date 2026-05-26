# app/shared/config/chunking_config.py
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum

class ChunkingStrategy(str, Enum):
    SECTION_AWARE = "section_aware"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    TOKEN_BASED = "token_based"

class ChunkingConfig(BaseModel):
    # Core parameters
    strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    chunk_size: int = Field(512, ge=100, le=2000)  # tokens or chars
    chunk_overlap: int = Field(100, ge=0, le=500)
    
    # Resume-specific
    preserve_section_context: bool = True
    min_chunk_length: int = Field(40, ge=10)
    max_chunks_per_resume: int = Field(200, ge=50)
    
    # Tokenization
    tokenizer_model: str = "cl100k_base"  # tiktoken for OpenAI compat
    count_tokens: bool = True
    
    # Semantic options
    semantic_threshold: float = Field(0.85, ge=0.0, le=1.0)  # for dedup
    use_sentence_boundaries: bool = True
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # Observability
    emit_metrics: bool = True
    log_chunk_samples: bool = False
    
    @validator("chunk_overlap")
    def validate_overlap(cls, v, values):
        if v >= values.get("chunk_size", 512):
            raise ValueError("chunk_overlap must be < chunk_size")
        return v

# Usage: config = ChunkingConfig.from_env() or load from YAML/consul