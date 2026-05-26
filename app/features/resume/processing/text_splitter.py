# # app/features/resume/processing/text_splitter.py
# import asyncio
# import logging
# import time
# from typing import List, Optional, Callable
# from collections import defaultdict

# from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
# import tiktoken

# from app.shared.config.chunking_config import ChunkingConfig, ChunkingStrategy
# from app.shared.models.chunk import Chunk, ChunkMetadata, ResumeSection
# from app.shared.observability.metrics import CHUNKING_DURATION, CHUNK_COUNT, CHUNKING_ERRORS
# from app.shared.utils.cache import async_cache
# from .section_detector import SectionDetector
# from .semantic_clusterer import SemanticClusterer  # Optional: for semantic splitting

# logger = logging.getLogger(__name__)

# class EnterpriseTextSplitter:
#     """
#     Production-grade text splitter for resumes with:
#     - Section-aware chunking
#     - Context preservation for skill→experience linking
#     - Token-aware limits for embedding models
#     - Async support + caching + observability
#     """
    
#     def __init__(self, config: Optional[ChunkingConfig] = None):
#         self.config = config or ChunkingConfig()
#         self._tokenizer = tiktoken.get_encoding(self.config.tokenizer_model) if self.config.count_tokens else None
#         self._semantic_clusterer = SemanticClusterer() if self.config.strategy == ChunkingStrategy.SEMANTIC else None
        
#     async def split(self, text: str, resume_id: int) -> List[Chunk]:
#         """Main entry point: async, observable, cached"""
#         start_time = time.time()
        
#         try:
#             # 🔥 Cache check
#             if self.config.cache_enabled:
#                 cache_key = hashlib.sha256(f"{resume_id}:{text[:500]}".encode()).hexdigest()
#                 cached = await self._get_from_cache(cache_key)
#                 if cached:
#                     logger.info("chunking_cache_hit", extra={"resume_id": resume_id})
#                     return cached
            
#             # 🔥 Strategy routing
#             if self.config.strategy == ChunkingStrategy.SECTION_AWARE:
#                 chunks = await self._section_aware_split(text, resume_id)
#             elif self.config.strategy == ChunkingStrategy.SEMANTIC:
#                 chunks = await self._semantic_split(text, resume_id)
#             elif self.config.strategy == ChunkingStrategy.HYBRID:
#                 chunks = await self._hybrid_split(text, resume_id)
#             else:
#                 chunks = await self._token_based_split(text, resume_id)
            
#             # 🔥 Post-process: filter, dedupe, enrich
#             chunks = await self._post_process(chunks, text)
            
#             # 🔥 Cache result
#             if self.config.cache_enabled:
#                 await self._set_cache(cache_key, chunks)
            
#             # 🔥 Metrics
#             duration = time.time() - start_time
#             CHUNKING_DURATION.observe(duration)
#             CHUNK_COUNT.observe(len(chunks))
            
#             logger.info(
#                 "chunking_completed",
#                 extra={
#                     "resume_id": resume_id,
#                     "strategy": self.config.strategy.value,
#                     "chunks": len(chunks),
#                     "duration_sec": round(duration, 3)
#                 }
#             )
            
#             if self.config.log_chunk_samples:
#                 for i, chunk in enumerate(chunks[:3]):
#                     logger.debug(f"chunk_sample_{i}", extra={"content": chunk.content[:200]})
            
#             return chunks
            
#         except Exception as e:
#             CHUNKING_ERRORS.inc()
#             logger.exception("chunking_failed", extra={"resume_id": resume_id, "error": str(e)})
#             raise
    
#     async def _section_aware_split(self, text: str, resume_id: int) -> List[Chunk]:
#         """Split by detected resume sections, then sub-chunk within sections"""
#         sections = SectionDetector.detect_sections(text)
#         all_chunks = []
        
#         for idx, (start, end, section_type, header) in enumerate(sections):
#             section_text = text[start:end].strip()
#             if len(section_text) < self.config.min_chunk_length:
#                 continue
            
#             # Sub-chunk within section using RecursiveCharacterTextSplitter
#             sub_splitter = RecursiveCharacterTextSplitter(
#                 chunk_size=self.config.chunk_size,
#                 chunk_overlap=self.config.chunk_overlap,
#                 separators=["\n\n", "\n", ". ", " ", ""] if self.config.use_sentence_boundaries else ["\n\n", "\n", " "]
#             )
            
#             sub_chunks = sub_splitter.split_text(section_text)
            
#             for sub_idx, sub_content in enumerate(sub_chunks):
#                 if len(sub_content.strip()) < self.config.min_chunk_length:
#                     continue
                
#                 # Preserve context window (±2 sentences from original text)
#                 context = self._extract_context_window(text, start + section_text.find(sub_content), radius=2)
                
#                 # Count tokens if enabled
#                 token_count = len(self._tokenizer.encode(sub_content)) if self._tokenizer else None
                
#                 metadata = ChunkMetadata(
#                     resume_id=resume_id,
#                     chunk_index=len(all_chunks),
#                     section=section_type,
#                     char_start=start + section_text.find(sub_content),
#                     char_end=start + section_text.find(sub_content) + len(sub_content),
#                     token_count=token_count,
#                     context_window=context
#                 )
                
#                 chunk = Chunk(content=sub_content.strip(), metadata=metadata)
#                 all_chunks.append(chunk)
            
#             # Limit total chunks
#             if len(all_chunks) >= self.config.max_chunks_per_resume:
#                 logger.warning("chunk_limit_reached", extra={"resume_id": resume_id})
#                 break
        
#         return all_chunks
    
#     async def _hybrid_split(self, text: str, resume_id: int) -> List[Chunk]:
#         """Hybrid: section-aware first, then semantic deduplication"""
#         # Step 1: Section-aware split
#         chunks = await self._section_aware_split(text, resume_id)
        
#         # Step 2: Semantic deduplication (optional, for high-similarity chunks)
#         if self.config.semantic_threshold < 1.0 and len(chunks) > 10:
#             chunks = await self._semantic_deduplicate(chunks, threshold=self.config.semantic_threshold)
        
#         return chunks
    
#     async def _semantic_deduplicate(self, chunks: List[Chunk], threshold: float) -> List[Chunk]:
#         """Remove near-duplicate chunks using embedding similarity"""
#         if not self._semantic_clusterer:
#             return chunks
        
#         # Generate lightweight embeddings for dedup (use small model)
#         embeddings = await self._semantic_clusterer.embed([c.content for c in chunks])
        
#         # Cluster + keep representative from each cluster
#         keep_indices = await self._semantic_clusterer.deduplicate_by_similarity(
#             embeddings, threshold=threshold
#         )
        
#         deduped = [chunks[i] for i in keep_indices]
#         logger.info("semantic_dedup_applied", extra={"original": len(chunks), "deduped": len(deduped)})
        
#         return deduped
    
#     async def _post_process(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
#         """Filter, enrich, and prepare chunks for downstream use"""
#         processed = []
        
#         for chunk in chunks:
#             # Filter too-short
#             if len(chunk.content.strip()) < self.config.min_chunk_length:
#                 continue
            
#             # Enrich: extract skills/entities mentioned in this chunk (lightweight)
#             if chunk.metadata.section == ResumeSection.SKILLS or chunk.metadata.section == ResumeSection.EXPERIENCE:
#                 chunk.metadata.skills_mentioned = self._extract_inline_skills(chunk.content)
#                 chunk.metadata.entities = self._extract_entities(chunk.content)
            
#             # Generate embedding cache key
#             chunk.metadata.embedding_cache_key = chunk.metadata.generate_cache_key(chunk.content)
            
#             processed.append(chunk)
        
#         # Sort by section priority (Skills/Experience first for matching)
#         section_priority = {
#             ResumeSection.SKILLS: 0,
#             ResumeSection.EXPERIENCE: 1,
#             ResumeSection.PROJECTS: 2,
#             ResumeSection.EDUCATION: 3,
#             ResumeSection.CERTIFICATIONS: 4,
#             ResumeSection.SUMMARY: 5,
#             ResumeSection.UNKNOWN: 6
#         }
#         processed.sort(key=lambda c: (section_priority[c.metadata.section], c.metadata.chunk_index))
        
#         return processed[:self.config.max_chunks_per_resume]
    
#     def _extract_context_window(self, text: str, position: int, radius: int = 2) -> str:
#         """Extract ±N sentences around position for skill→experience linking"""
#         # Simple sentence split (improve with nltk/spaCy in production)
#         sentences = re.split(r'(?<=[.!?])\s+', text)
        
#         # Find which sentence contains position
#         char_count = 0
#         target_idx = -1
#         for i, sent in enumerate(sentences):
#             if char_count <= position < char_count + len(sent):
#                 target_idx = i
#                 break
#             char_count += len(sent) + 1
        
#         if target_idx == -1:
#             return ""
        
#         # Extract window
#         start = max(0, target_idx - radius)
#         end = min(len(sentences), target_idx + radius + 1)
#         return " ".join(sentences[start:end]).strip()
    
#     def _extract_inline_skills(self, text: str) -> List[str]:
#         """Lightweight regex-based skill extraction for chunk enrichment"""
#         # Simple pattern: capitalized words, known tech terms
#         patterns = [
#             r'\b(Python|Java|JavaScript|TypeScript|React|Vue|Angular|Node\.js|FastAPI|Django)\b',
#             r'\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|CI/CD|GraphQL|REST)\b',
#             r'\b(SQL|NoSQL|MongoDB|PostgreSQL|Redis|Elasticsearch)\b'
#         ]
#         skills = []
#         for pattern in patterns:
#             skills.extend(re.findall(pattern, text, re.IGNORECASE))
#         return list(set(s.lower() for s in skills))
    
#     def _extract_entities(self, text: str) -> dict:
#         """Extract companies, dates, roles for context"""
#         entities = {}
        
#         # Company names (heuristic: capitalized words after "at" or "for")
#         companies = re.findall(r'\b(?:at|for)\s+([A-Z][a-zA-Z\s&]+?)(?:\s*(?:,|\.|;|in\s+\d{4}|$))', text)
#         if companies:
#             entities["companies"] = [c.strip() for c in companies[:3]]
        
#         # Date ranges
#         dates = re.findall(r'\b(\d{4}\s*[-–]\s*(?:\d{4}|present|now))\b', text)
#         if dates:
#             entities["date_range"] = dates[0]
        
#         # Job titles (heuristic: capitalized phrase before "at")
#         titles = re.findall(r'\b([A-Z][a-zA-Z\s]+?)\s+at\s+', text)
#         if titles:
#             entities["role"] = titles[0].strip()
        
#         return entities
    
#     @async_cache(ttl=lambda self: self.config.cache_ttl_seconds)
#     async def _get_from_cache(self, key: str) -> Optional[List[Chunk]]:
#         """Fetch chunks from cache (Redis/Memcached)"""
#         # Implementation depends on your cache layer
#         return None  # Placeholder
    
#     @async_cache(ttl=lambda self: self.config.cache_ttl_seconds, set_only=True)
#     async def _set_cache(self, key: str, chunks: List[Chunk]):
#         """Store chunks in cache"""
#         pass  # Placeholder