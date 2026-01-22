"""
LORENZ SaaS - Apify Integration Service
Automated scraping for WhatsApp, LinkedIn, and other social platforms
"""

import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class ApifyActorStatus(str, Enum):
    """Actor run status"""
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    TIMED_OUT = "TIMED-OUT"


class ApifyService:
    """
    Apify integration service for automated web scraping.

    Supports:
    - WhatsApp Messages Scraper (requires QR code auth)
    - LinkedIn Profile Scraper
    - LinkedIn Bulk Scraper
    """

    BASE_URL = "https://api.apify.com/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.APIFY_API_KEY
        if not self.api_key:
            raise ValueError("Apify API key not configured. Set APIFY_API_KEY in environment.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Make async HTTP request to Apify API"""
        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data
            )
            response.raise_for_status()
            return response.json()

    async def run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        wait_for_finish: bool = True,
        max_wait_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Run an Apify actor and optionally wait for results.

        Args:
            actor_id: Actor ID (e.g., "extremescrapes~whatsapp-messages-scraper")
            input_data: Input configuration for the actor
            wait_for_finish: If True, wait for actor to complete
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            Dict with run info and results (if wait_for_finish is True)
        """
        # Start the actor run
        run_data = await self._make_request(
            "POST",
            f"acts/{actor_id}/runs",
            json_data=input_data
        )

        run_id = run_data["data"]["id"]
        logger.info(f"Started Apify actor {actor_id}, run ID: {run_id}")

        if not wait_for_finish:
            return {"run_id": run_id, "status": "RUNNING", "data": run_data}

        # Poll for completion
        start_time = datetime.now()
        while True:
            run_info = await self._make_request("GET", f"actor-runs/{run_id}")
            status = run_info["data"]["status"]

            if status in [ApifyActorStatus.SUCCEEDED, ApifyActorStatus.FAILED,
                         ApifyActorStatus.ABORTED, ApifyActorStatus.TIMED_OUT]:
                break

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                logger.warning(f"Actor run {run_id} timed out after {max_wait_seconds}s")
                return {"run_id": run_id, "status": "TIMEOUT", "data": run_info}

            await asyncio.sleep(5)  # Poll every 5 seconds

        if status == ApifyActorStatus.SUCCEEDED:
            # Fetch results from default dataset
            dataset_id = run_info["data"]["defaultDatasetId"]
            results = await self._make_request("GET", f"datasets/{dataset_id}/items")
            return {
                "run_id": run_id,
                "status": status,
                "items": results,
                "data": run_info
            }

        return {"run_id": run_id, "status": status, "data": run_info}

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a running actor"""
        return await self._make_request("GET", f"actor-runs/{run_id}")

    async def get_run_results(self, run_id: str) -> List[Dict[str, Any]]:
        """Get results from a completed actor run"""
        run_info = await self._make_request("GET", f"actor-runs/{run_id}")
        dataset_id = run_info["data"]["defaultDatasetId"]
        results = await self._make_request("GET", f"datasets/{dataset_id}/items")
        return results

    # ==================== WhatsApp Scraping ====================

    async def scrape_whatsapp_messages(
        self,
        phone_numbers: Optional[List[str]] = None,
        group_names: Optional[List[str]] = None,
        max_messages: int = 100,
        wait_for_finish: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape WhatsApp messages using Apify actor.

        NOTE: This actor requires WhatsApp Web QR code authentication.
        First run will prompt for QR scan in Apify console.

        Args:
            phone_numbers: List of phone numbers to scrape chats from
            group_names: List of group names to scrape
            max_messages: Maximum messages per chat
            wait_for_finish: Wait for completion (may take a while)

        Returns:
            Actor run info or results
        """
        input_data = {
            "maxMessages": max_messages,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        if phone_numbers:
            input_data["phoneNumbers"] = phone_numbers
        if group_names:
            input_data["groupNames"] = group_names

        actor_id = settings.APIFY_WHATSAPP_ACTOR_ID

        logger.info(f"Starting WhatsApp scraping for {len(phone_numbers or [])} contacts, {len(group_names or [])} groups")

        return await self.run_actor(
            actor_id=actor_id,
            input_data=input_data,
            wait_for_finish=wait_for_finish,
            max_wait_seconds=600  # WhatsApp scraping can be slow
        )

    def parse_whatsapp_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse WhatsApp scraper results into unified contact format.

        Args:
            results: Raw results from Apify actor

        Returns:
            List of parsed contacts with messages
        """
        contacts = []

        for item in results:
            contact_data = {
                "source": "whatsapp",
                "phone_number": item.get("phoneNumber"),
                "display_name": item.get("contactName") or item.get("pushname"),
                "profile_pic_url": item.get("profilePicUrl"),
                "is_group": item.get("isGroup", False),
                "group_name": item.get("groupName") if item.get("isGroup") else None,
                "messages": []
            }

            # Parse messages
            for msg in item.get("messages", []):
                contact_data["messages"].append({
                    "timestamp": msg.get("timestamp"),
                    "from_me": msg.get("fromMe", False),
                    "content": msg.get("body"),
                    "type": msg.get("type", "text"),
                    "has_media": msg.get("hasMedia", False)
                })

            contacts.append(contact_data)

        return contacts

    # ==================== LinkedIn Scraping ====================

    async def scrape_linkedin_profiles(
        self,
        profile_urls: List[str],
        include_skills: bool = True,
        include_experience: bool = True,
        wait_for_finish: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape LinkedIn profiles using Apify actor.

        Args:
            profile_urls: List of LinkedIn profile URLs
            include_skills: Include skills section
            include_experience: Include experience section
            wait_for_finish: Wait for completion

        Returns:
            Actor run info or results
        """
        input_data = {
            "startUrls": [{"url": url} for url in profile_urls],
            "includeSkills": include_skills,
            "includeExperience": include_experience,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        actor_id = settings.APIFY_LINKEDIN_ACTOR_ID

        logger.info(f"Starting LinkedIn profile scraping for {len(profile_urls)} profiles")

        return await self.run_actor(
            actor_id=actor_id,
            input_data=input_data,
            wait_for_finish=wait_for_finish,
            max_wait_seconds=300
        )

    async def search_linkedin_profiles(
        self,
        search_query: str,
        max_results: int = 50,
        location: Optional[str] = None,
        wait_for_finish: bool = True
    ) -> Dict[str, Any]:
        """
        Search and scrape LinkedIn profiles by query.
        Uses the bulk scraper actor.

        Args:
            search_query: Search keywords (e.g., "CEO tech startup")
            max_results: Maximum profiles to return
            location: Filter by location
            wait_for_finish: Wait for completion

        Returns:
            Actor run info or results
        """
        input_data = {
            "searchKeyword": search_query,
            "maxResults": max_results,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        if location:
            input_data["location"] = location

        actor_id = settings.APIFY_LINKEDIN_BULK_ACTOR_ID

        logger.info(f"Starting LinkedIn search for '{search_query}', max {max_results} results")

        return await self.run_actor(
            actor_id=actor_id,
            input_data=input_data,
            wait_for_finish=wait_for_finish,
            max_wait_seconds=600
        )

    def parse_linkedin_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse LinkedIn scraper results into unified contact format.

        Args:
            results: Raw results from Apify actor

        Returns:
            List of parsed contacts
        """
        contacts = []

        for item in results:
            contact_data = {
                "source": "linkedin",
                "linkedin_url": item.get("url") or item.get("profileUrl"),
                "display_name": item.get("fullName") or f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                "first_name": item.get("firstName"),
                "last_name": item.get("lastName"),
                "headline": item.get("headline") or item.get("title"),
                "profile_pic_url": item.get("profilePicture") or item.get("imageUrl"),
                "location": item.get("location") or item.get("geoLocation"),
                "company": item.get("company") or self._extract_current_company(item),
                "job_title": item.get("jobTitle") or item.get("title"),
                "connections": item.get("connectionsCount"),
                "about": item.get("summary") or item.get("about"),
                "skills": item.get("skills", []),
                "experience": self._parse_linkedin_experience(item.get("experience", [])),
                "education": self._parse_linkedin_education(item.get("education", []))
            }

            contacts.append(contact_data)

        return contacts

    def _extract_current_company(self, profile: Dict) -> Optional[str]:
        """Extract current company from experience"""
        experience = profile.get("experience", [])
        if experience and len(experience) > 0:
            return experience[0].get("companyName")
        return None

    def _parse_linkedin_experience(self, experience: List[Dict]) -> List[Dict]:
        """Parse LinkedIn experience into structured format"""
        parsed = []
        for exp in experience:
            parsed.append({
                "company": exp.get("companyName"),
                "title": exp.get("title"),
                "location": exp.get("location"),
                "start_date": exp.get("startDate"),
                "end_date": exp.get("endDate"),
                "description": exp.get("description"),
                "is_current": exp.get("isCurrent", False)
            })
        return parsed

    def _parse_linkedin_education(self, education: List[Dict]) -> List[Dict]:
        """Parse LinkedIn education into structured format"""
        parsed = []
        for edu in education:
            parsed.append({
                "school": edu.get("schoolName"),
                "degree": edu.get("degree"),
                "field_of_study": edu.get("fieldOfStudy"),
                "start_year": edu.get("startDate"),
                "end_year": edu.get("endDate"),
                "description": edu.get("description")
            })
        return parsed

    # ==================== Twitter/X Scraping ====================

    async def scrape_twitter_profiles(
        self,
        usernames: List[str],
        include_tweets: bool = True,
        max_tweets: int = 50,
        wait_for_finish: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape Twitter/X profiles.

        Args:
            usernames: List of Twitter usernames (without @)
            include_tweets: Include recent tweets
            max_tweets: Maximum tweets per profile
            wait_for_finish: Wait for completion

        Returns:
            Actor run info or results
        """
        # Use a common Twitter scraper actor
        actor_id = "apidojo~tweet-scraper"

        input_data = {
            "handles": usernames,
            "tweetsDesired": max_tweets if include_tweets else 0,
            "proxyConfiguration": {"useApifyProxy": True}
        }

        logger.info(f"Starting Twitter scraping for {len(usernames)} profiles")

        return await self.run_actor(
            actor_id=actor_id,
            input_data=input_data,
            wait_for_finish=wait_for_finish,
            max_wait_seconds=300
        )

    def parse_twitter_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Twitter results into unified contact format"""
        contacts = []

        for item in results:
            user = item.get("user", item)
            contact_data = {
                "source": "twitter",
                "twitter_handle": user.get("screen_name") or user.get("username"),
                "display_name": user.get("name"),
                "bio": user.get("description"),
                "profile_pic_url": user.get("profile_image_url_https"),
                "location": user.get("location"),
                "followers_count": user.get("followers_count"),
                "following_count": user.get("friends_count"),
                "tweets_count": user.get("statuses_count"),
                "verified": user.get("verified", False),
                "website": user.get("url"),
                "recent_tweets": []
            }

            # Parse tweets if available
            for tweet in item.get("tweets", [])[:10]:
                contact_data["recent_tweets"].append({
                    "id": tweet.get("id_str"),
                    "text": tweet.get("full_text") or tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "retweet_count": tweet.get("retweet_count"),
                    "like_count": tweet.get("favorite_count")
                })

            contacts.append(contact_data)

        return contacts


# ==================== Unified Import Service ====================

class SocialGraphApifyImporter:
    """
    High-level service for importing social data via Apify
    into the Social Graph system.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.apify = ApifyService(api_key)

    async def import_whatsapp_chats(
        self,
        phone_numbers: Optional[List[str]] = None,
        group_names: Optional[List[str]] = None,
        max_messages: int = 100
    ) -> Dict[str, Any]:
        """
        Import WhatsApp chats into Social Graph.

        Returns:
            Dict with import status and parsed contacts
        """
        result = await self.apify.scrape_whatsapp_messages(
            phone_numbers=phone_numbers,
            group_names=group_names,
            max_messages=max_messages,
            wait_for_finish=True
        )

        if result.get("status") == ApifyActorStatus.SUCCEEDED:
            contacts = self.apify.parse_whatsapp_results(result.get("items", []))
            return {
                "success": True,
                "source": "whatsapp",
                "contacts_imported": len(contacts),
                "contacts": contacts
            }

        return {
            "success": False,
            "source": "whatsapp",
            "error": f"Actor run failed with status: {result.get('status')}",
            "run_id": result.get("run_id")
        }

    async def import_linkedin_connections(
        self,
        profile_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Import LinkedIn connections into Social Graph.

        Returns:
            Dict with import status and parsed contacts
        """
        result = await self.apify.scrape_linkedin_profiles(
            profile_urls=profile_urls,
            include_skills=True,
            include_experience=True,
            wait_for_finish=True
        )

        if result.get("status") == ApifyActorStatus.SUCCEEDED:
            contacts = self.apify.parse_linkedin_results(result.get("items", []))
            return {
                "success": True,
                "source": "linkedin",
                "contacts_imported": len(contacts),
                "contacts": contacts
            }

        return {
            "success": False,
            "source": "linkedin",
            "error": f"Actor run failed with status: {result.get('status')}",
            "run_id": result.get("run_id")
        }

    async def search_and_import_linkedin(
        self,
        search_query: str,
        max_results: int = 50,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search LinkedIn and import matching profiles.

        Returns:
            Dict with import status and parsed contacts
        """
        result = await self.apify.search_linkedin_profiles(
            search_query=search_query,
            max_results=max_results,
            location=location,
            wait_for_finish=True
        )

        if result.get("status") == ApifyActorStatus.SUCCEEDED:
            contacts = self.apify.parse_linkedin_results(result.get("items", []))
            return {
                "success": True,
                "source": "linkedin_search",
                "query": search_query,
                "contacts_imported": len(contacts),
                "contacts": contacts
            }

        return {
            "success": False,
            "source": "linkedin_search",
            "error": f"Actor run failed with status: {result.get('status')}",
            "run_id": result.get("run_id")
        }

    async def import_twitter_profiles(
        self,
        usernames: List[str],
        include_tweets: bool = True
    ) -> Dict[str, Any]:
        """
        Import Twitter profiles into Social Graph.

        Returns:
            Dict with import status and parsed contacts
        """
        result = await self.apify.scrape_twitter_profiles(
            usernames=usernames,
            include_tweets=include_tweets,
            wait_for_finish=True
        )

        if result.get("status") == ApifyActorStatus.SUCCEEDED:
            contacts = self.apify.parse_twitter_results(result.get("items", []))
            return {
                "success": True,
                "source": "twitter",
                "contacts_imported": len(contacts),
                "contacts": contacts
            }

        return {
            "success": False,
            "source": "twitter",
            "error": f"Actor run failed with status: {result.get('status')}",
            "run_id": result.get("run_id")
        }
