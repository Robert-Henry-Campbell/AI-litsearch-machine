from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PaperMetadata(BaseModel):
    """Metadata fields extracted by Agent 1.

    Example:
        >>> from schemas.metadata import PaperMetadata
        >>> PaperMetadata(title="Example", authors="Doe et al.")
    """

    title: Optional[str] = None
    authors: Optional[str] = None
    doi: Optional[str] = None
    pub_date: Optional[str] = None
    data_sources: Optional[List[str]] = None
    omics_modalities: Optional[List[str]] = None
    targets: Optional[List[str]] = None
    p_threshold: Optional[str] = None
    ld_r2: Optional[str] = None
    outcome: Optional[str] = None
    additional_QC: Optional[str] = None
