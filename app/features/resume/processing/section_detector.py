# app/features/resume/processing/section_detector.py
import re
import logging
from typing import List, Tuple
from app.shared.models.chunk import ResumeSection

logger = logging.getLogger(__name__)

class SectionDetector:
    # Resume section patterns (case-insensitive, flexible)
    SECTION_PATTERNS = {
        ResumeSection.SKILLS: [
            r"\b(skills|technical\s*skills|core\s*competencies|technologies|tools)\b",
            r"\b(proficient\s*in|familiar\s*with|experience\s*with)\b"
        ],
        ResumeSection.EXPERIENCE: [
            r"\b(work\s*experience|professional\s*experience|employment|career)\b",
            r"\b(\d{4}\s*[-–]\s*(?:\d{4}|present|now))\b"  # Date ranges
        ],
        ResumeSection.EDUCATION: [
            r"\b(education|academic\s*background|degrees|qualifications)\b",
            r"\b(bachelor|master|phd|bsc|msc|mba)\b"
        ],
        ResumeSection.PROJECTS: [
            r"\b(projects|key\s*projects|portfolio|achievements)\b"
        ],
        ResumeSection.CERTIFICATIONS: [
            r"\b(certifications|licenses|credentials|awards)\b"
        ],
        ResumeSection.SUMMARY: [
            r"\b(summary|profile|objective|about\s*me)\b"
        ]
    }
    
    @classmethod
    def detect_sections(cls, text: str) -> List[Tuple[int, int, ResumeSection, str]]:
        """
        Returns: List of (start_idx, end_idx, section_type, section_header)
        """
        sections = []
        text_lower = text.lower()
        
        # Find all section headers with positions
        matches = []
        for section_type, patterns in cls.SECTION_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text_lower):
                    matches.append((match.start(), match.end(), section_type, match.group()))
        
        # Sort by position and merge overlapping
        matches.sort(key=lambda x: x[0])
        
        # Assign text ranges to each section (heuristic: until next section or 500 chars)
        for i, (start, end, section_type, header) in enumerate(matches):
            next_start = matches[i+1][0] if i+1 < len(matches) else len(text)
            section_end = min(next_start, start + 1500)  # Max section length heuristic
            
            # Extract actual section text
            section_text = text[start:section_end].strip()
            
            sections.append((start, section_end, section_type, header))
            logger.debug(f"Detected section: {section_type.value} at [{start}:{section_end}]")
        
        return sections if sections else [(0, len(text), ResumeSection.UNKNOWN, "full_text")]