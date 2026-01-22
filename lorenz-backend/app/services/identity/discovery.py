"""
LORENZ - Identity Discovery Service
Uses web search and AI to discover information about users during onboarding
"""

import logging
import httpx
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredProfile:
    """Profile information discovered about a user"""
    full_name: str
    first_name: str
    last_name: str

    # Professional
    profession: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    industry: Optional[str] = None

    # Personal
    age: Optional[int] = None
    birth_year: Optional[int] = None
    location: Optional[str] = None
    nationality: Optional[str] = None

    # Family
    marital_status: Optional[str] = None
    has_children: Optional[bool] = None
    children_count: Optional[int] = None

    # Online presence
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    wikipedia_url: Optional[str] = None
    website: Optional[str] = None

    # Bio & achievements
    bio_summary: Optional[str] = None
    notable_achievements: List[str] = None
    education: Optional[str] = None

    # Confidence
    confidence_score: float = 0.0  # 0-1 how confident we are this is the right person
    disambiguation_needed: bool = False
    disambiguation_options: List[Dict[str, Any]] = None

    # Sources
    sources: List[str] = None

    def __post_init__(self):
        if self.notable_achievements is None:
            self.notable_achievements = []
        if self.disambiguation_options is None:
            self.disambiguation_options = []
        if self.sources is None:
            self.sources = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IdentityDiscoveryService:
    """
    Service for discovering user identity information from public sources.
    Uses web search and Claude AI to analyze and synthesize information.
    """

    def __init__(self, claude_api_key: str = None):
        self.claude_api_key = claude_api_key
        self.search_results_cache: Dict[str, Any] = {}

    async def discover_identity(
        self,
        full_name: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> DiscoveredProfile:
        """
        Discover information about a person from their name.

        Args:
            full_name: The person's full name
            additional_context: Optional hints like location, company, etc.

        Returns:
            DiscoveredProfile with found information
        """
        logger.info(f"Discovering identity for: {full_name}")

        # Parse name
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Initialize profile
        profile = DiscoveredProfile(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
        )

        try:
            # Step 1: Search for the person
            search_results = await self._web_search(full_name, additional_context)

            if not search_results:
                logger.warning(f"No search results for: {full_name}")
                return profile

            # Step 2: Use Claude to analyze results and extract profile
            profile = await self._analyze_with_ai(full_name, search_results, additional_context)

        except Exception as e:
            logger.error(f"Error discovering identity: {e}", exc_info=True)

        return profile

    async def _web_search(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search for the person.
        Uses DuckDuckGo Instant Answer API (free, no auth needed).
        """
        results = []

        # Build search query with context
        search_query = query
        if context:
            if context.get("company"):
                search_query += f" {context['company']}"
            if context.get("profession"):
                search_query += f" {context['profession']}"
            if context.get("location"):
                search_query += f" {context['location']}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # DuckDuckGo Instant Answer API
                ddg_response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": search_query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 0,
                    }
                )

                if ddg_response.status_code == 200:
                    data = ddg_response.json()

                    # Extract relevant information
                    if data.get("Abstract"):
                        results.append({
                            "source": "duckduckgo",
                            "type": "abstract",
                            "content": data["Abstract"],
                            "url": data.get("AbstractURL"),
                            "source_name": data.get("AbstractSource"),
                        })

                    # Related topics (for disambiguation)
                    for topic in data.get("RelatedTopics", [])[:5]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "source": "duckduckgo",
                                "type": "related",
                                "content": topic["Text"],
                                "url": topic.get("FirstURL"),
                            })

                    # Disambiguation results
                    if data.get("Type") == "D":  # Disambiguation
                        for topic in data.get("RelatedTopics", [])[:5]:
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append({
                                    "source": "duckduckgo",
                                    "type": "disambiguation",
                                    "content": topic["Text"],
                                    "url": topic.get("FirstURL"),
                                })

                # Also try Wikipedia API for more details
                wiki_response = await client.get(
                    "https://en.wikipedia.org/api/rest_v1/page/summary/" +
                    query.replace(" ", "_"),
                    headers={"User-Agent": "LORENZ/1.0"}
                )

                if wiki_response.status_code == 200:
                    wiki_data = wiki_response.json()
                    if wiki_data.get("extract"):
                        results.append({
                            "source": "wikipedia",
                            "type": "summary",
                            "content": wiki_data["extract"],
                            "url": wiki_data.get("content_urls", {}).get("desktop", {}).get("page"),
                            "thumbnail": wiki_data.get("thumbnail", {}).get("source"),
                        })

        except Exception as e:
            logger.warning(f"Web search error: {e}")

        return results

    async def _analyze_with_ai(
        self,
        full_name: str,
        search_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> DiscoveredProfile:
        """
        Use Claude AI to analyze search results and build profile.
        """
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        if not self.claude_api_key:
            # Return basic profile from search results without AI
            return self._build_basic_profile(full_name, search_results)

        # Build context for Claude
        search_context = "\n\n".join([
            f"Source: {r.get('source_name', r.get('source'))}\n"
            f"Type: {r.get('type')}\n"
            f"Content: {r.get('content')}"
            for r in search_results
        ])

        prompt = f"""Analizza le seguenti informazioni trovate online su "{full_name}" e crea un profilo dettagliato.

Informazioni trovate:
{search_context}

Contesto aggiuntivo: {json.dumps(context) if context else "Nessuno"}

Rispondi con un JSON valido con questa struttura (usa null per i campi non trovati):
{{
    "profession": "professione/ruolo principale",
    "company": "azienda attuale o principale",
    "role": "ruolo specifico",
    "industry": "settore",
    "age": numero o null,
    "birth_year": anno di nascita o null,
    "location": "città/paese",
    "nationality": "nazionalità",
    "marital_status": "single/married/divorced/unknown",
    "has_children": true/false/null,
    "children_count": numero o null,
    "linkedin_url": "URL LinkedIn se trovato",
    "twitter_handle": "@handle se trovato",
    "wikipedia_url": "URL Wikipedia se esiste",
    "website": "sito personale se trovato",
    "bio_summary": "breve biografia di 2-3 frasi in italiano che impressioni l'utente",
    "notable_achievements": ["achievement1", "achievement2"],
    "education": "formazione principale",
    "confidence_score": 0.0-1.0 quanto sei sicuro sia la persona giusta,
    "disambiguation_needed": true/false se ci sono più persone possibili,
    "disambiguation_options": [
        {{"description": "Prima opzione possibile", "context": "dettagli"}},
        {{"description": "Seconda opzione", "context": "dettagli"}}
    ] se disambiguation_needed è true
}}

Rispondi SOLO con il JSON, senza markdown o altro testo."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.claude_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-5-haiku-20241022",
                        "max_tokens": 1500,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    ai_text = result["content"][0]["text"]

                    # Parse JSON response
                    try:
                        # Clean up response if needed
                        ai_text = ai_text.strip()
                        if ai_text.startswith("```"):
                            ai_text = ai_text.split("```")[1]
                            if ai_text.startswith("json"):
                                ai_text = ai_text[4:]

                        profile_data = json.loads(ai_text)

                        # Build profile from AI response
                        sources = [r.get("url") for r in search_results if r.get("url")]

                        return DiscoveredProfile(
                            full_name=full_name,
                            first_name=first_name,
                            last_name=last_name,
                            profession=profile_data.get("profession"),
                            company=profile_data.get("company"),
                            role=profile_data.get("role"),
                            industry=profile_data.get("industry"),
                            age=profile_data.get("age"),
                            birth_year=profile_data.get("birth_year"),
                            location=profile_data.get("location"),
                            nationality=profile_data.get("nationality"),
                            marital_status=profile_data.get("marital_status"),
                            has_children=profile_data.get("has_children"),
                            children_count=profile_data.get("children_count"),
                            linkedin_url=profile_data.get("linkedin_url"),
                            twitter_handle=profile_data.get("twitter_handle"),
                            wikipedia_url=profile_data.get("wikipedia_url"),
                            website=profile_data.get("website"),
                            bio_summary=profile_data.get("bio_summary"),
                            notable_achievements=profile_data.get("notable_achievements", []),
                            education=profile_data.get("education"),
                            confidence_score=profile_data.get("confidence_score", 0.5),
                            disambiguation_needed=profile_data.get("disambiguation_needed", False),
                            disambiguation_options=profile_data.get("disambiguation_options", []),
                            sources=sources,
                        )

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse AI response: {e}")

        except Exception as e:
            logger.error(f"AI analysis error: {e}")

        # Fallback to basic profile
        return self._build_basic_profile(full_name, search_results)

    def _build_basic_profile(
        self,
        full_name: str,
        search_results: List[Dict[str, Any]]
    ) -> DiscoveredProfile:
        """Build a basic profile from search results without AI."""
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        profile = DiscoveredProfile(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
        )

        # Extract what we can from search results
        for result in search_results:
            if result.get("type") == "summary" and result.get("source") == "wikipedia":
                profile.bio_summary = result.get("content", "")[:300]
                profile.wikipedia_url = result.get("url")
                profile.sources.append(result.get("url"))
            elif result.get("type") == "abstract":
                if not profile.bio_summary:
                    profile.bio_summary = result.get("content", "")[:300]
                if result.get("url"):
                    profile.sources.append(result.get("url"))

        # Check for disambiguation
        disambig_results = [r for r in search_results if r.get("type") == "disambiguation"]
        if disambig_results:
            profile.disambiguation_needed = True
            profile.disambiguation_options = [
                {"description": r.get("content", ""), "url": r.get("url")}
                for r in disambig_results[:3]
            ]
            profile.confidence_score = 0.3
        elif profile.bio_summary:
            profile.confidence_score = 0.7
        else:
            profile.confidence_score = 0.1

        return profile

    async def ask_disambiguation_question(
        self,
        profile: DiscoveredProfile,
        user_answer: str
    ) -> str:
        """
        Generate a follow-up question based on disambiguation options and user answer.
        """
        if not profile.disambiguation_needed:
            return None

        options = profile.disambiguation_options
        if not options:
            return None

        # Build question based on options
        question_parts = ["Ho trovato più persone con questo nome:"]
        for i, opt in enumerate(options[:3], 1):
            desc = opt.get("description", "")[:100]
            question_parts.append(f"{i}. {desc}")

        question_parts.append("\nQuale di queste sei tu? (rispondi con il numero o dai più dettagli)")

        return "\n".join(question_parts)


# Factory function
def create_identity_service(claude_api_key: str = None) -> IdentityDiscoveryService:
    """Create an identity discovery service instance."""
    import os
    api_key = claude_api_key or os.getenv("CLAUDE_API_KEY")
    return IdentityDiscoveryService(claude_api_key=api_key)
