"""
LORENZ SaaS - Social History Ingestion Service
==============================================

Collects user's history from social media platforms:
- LinkedIn (profile, experience, posts)
- Twitter/X (profile, tweets, interests)
- Meta (Facebook profile, Instagram posts)

This data helps build the user's Digital Twin profile.
"""

import logging
import aiohttp
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class SocialPlatform(str, Enum):
    """Supported social platforms"""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class ContentType(str, Enum):
    """Types of social content"""
    PROFILE = "profile"
    POST = "post"
    ARTICLE = "article"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILL = "skill"
    CONNECTION = "connection"
    TWEET = "tweet"
    LIKE = "like"
    COMMENT = "comment"


@dataclass
class SocialContent:
    """A piece of social media content"""
    id: str
    platform: SocialPlatform
    content_type: ContentType
    text: Optional[str]
    created_at: Optional[datetime]
    url: Optional[str]
    engagement: Dict = field(default_factory=dict)  # likes, comments, shares
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "content_type": self.content_type.value,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": self.url,
            "engagement": self.engagement,
            "metadata": self.metadata,
        }


@dataclass
class SocialProfile:
    """User's social media profile"""
    platform: SocialPlatform
    user_id: str
    username: Optional[str]
    name: str
    bio: Optional[str]
    headline: Optional[str]  # LinkedIn
    location: Optional[str]
    profile_url: str
    avatar_url: Optional[str]
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "platform": self.platform.value,
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "bio": self.bio,
            "headline": self.headline,
            "location": self.location,
            "profile_url": self.profile_url,
            "avatar_url": self.avatar_url,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "posts_count": self.posts_count,
            "verified": self.verified,
            "metadata": self.metadata,
        }


@dataclass
class WorkExperience:
    """Professional experience from LinkedIn"""
    id: str
    company: str
    title: str
    location: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]  # None if current
    description: Optional[str]
    is_current: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "is_current": self.is_current,
        }


@dataclass
class Education:
    """Education from LinkedIn"""
    id: str
    school: str
    degree: Optional[str]
    field_of_study: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    description: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "school": self.school,
            "degree": self.degree,
            "field_of_study": self.field_of_study,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
        }


@dataclass
class SocialHistoryResult:
    """Complete result of social history ingestion"""
    scan_id: str
    platform: SocialPlatform
    started_at: datetime
    completed_at: Optional[datetime]
    profile: Optional[SocialProfile]
    experiences: List[WorkExperience]
    education: List[Education]
    skills: List[str]
    content: List[SocialContent]
    interests: List[str]
    summary: Dict  # AI-generated summary of user's online presence
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "scan_id": self.scan_id,
            "platform": self.platform.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "profile": self.profile.to_dict() if self.profile else None,
            "experiences": [e.to_dict() for e in self.experiences],
            "education": [e.to_dict() for e in self.education],
            "skills": self.skills,
            "content": [c.to_dict() for c in self.content],
            "interests": self.interests,
            "summary": self.summary,
            "errors": self.errors,
        }


class SocialHistoryIngestion:
    """
    Ingests user's history from social media platforms.

    This is used during onboarding to understand the user's:
    - Professional background (LinkedIn)
    - Interests and opinions (Twitter)
    - Personal life and connections (Facebook/Instagram)

    Privacy note: All data is stored locally and user has full control.
    """

    def __init__(
        self,
        access_token: str,
        platform: SocialPlatform,
        max_posts: int = 100,
        include_engagement: bool = True
    ):
        """
        Initialize social history ingestion.

        Args:
            access_token: OAuth access token for the platform
            platform: Social media platform
            max_posts: Maximum posts/tweets to fetch
            include_engagement: Include likes, comments counts
        """
        self.access_token = access_token
        self.platform = platform
        self.max_posts = max_posts
        self.include_engagement = include_engagement

        self._session: Optional[aiohttp.ClientSession] = None
        self._cancelled = False

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    def cancel(self):
        """Cancel ongoing ingestion"""
        self._cancelled = True

    async def ingest(self) -> SocialHistoryResult:
        """
        Ingest user's social history.

        Returns:
            SocialHistoryResult with all collected data
        """
        scan_id = str(uuid4())
        started_at = datetime.now()
        errors = []

        profile = None
        experiences = []
        education = []
        skills = []
        content = []
        interests = []
        summary = {}

        logger.info(f"Starting social history ingestion for {self.platform.value}")

        try:
            if self.platform == SocialPlatform.LINKEDIN:
                result = await self._ingest_linkedin()
                profile = result.get("profile")
                experiences = result.get("experiences", [])
                education = result.get("education", [])
                skills = result.get("skills", [])
                content = result.get("posts", [])

            elif self.platform == SocialPlatform.TWITTER:
                result = await self._ingest_twitter()
                profile = result.get("profile")
                content = result.get("tweets", [])
                interests = result.get("interests", [])

            elif self.platform == SocialPlatform.FACEBOOK:
                result = await self._ingest_facebook()
                profile = result.get("profile")
                content = result.get("posts", [])

            elif self.platform == SocialPlatform.INSTAGRAM:
                result = await self._ingest_instagram()
                profile = result.get("profile")
                content = result.get("posts", [])

            # Generate summary
            summary = self._generate_summary(
                profile, experiences, education, skills, content, interests
            )

        except Exception as e:
            error_msg = f"Ingestion error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        return SocialHistoryResult(
            scan_id=scan_id,
            platform=self.platform,
            started_at=started_at,
            completed_at=datetime.now(),
            profile=profile,
            experiences=experiences,
            education=education,
            skills=skills,
            content=content,
            interests=interests,
            summary=summary,
            errors=errors,
        )

    # ==========================================================================
    # LinkedIn
    # ==========================================================================

    async def _ingest_linkedin(self) -> Dict:
        """Ingest LinkedIn profile and activity"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        result = {
            "profile": None,
            "experiences": [],
            "education": [],
            "skills": [],
            "posts": [],
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Get profile
        try:
            async with self._session.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["profile"] = SocialProfile(
                        platform=SocialPlatform.LINKEDIN,
                        user_id=data.get("sub", ""),
                        username=None,
                        name=data.get("name", ""),
                        bio=None,
                        headline=None,
                        location=data.get("locale", {}).get("country"),
                        profile_url=f"https://linkedin.com/in/{data.get('sub', '')}",
                        avatar_url=data.get("picture"),
                        metadata=data,
                    )
                else:
                    logger.warning(f"LinkedIn profile fetch failed: {resp.status}")
        except Exception as e:
            logger.error(f"LinkedIn profile error: {e}")

        # Get full profile (requires r_liteprofile or r_fullprofile scope)
        try:
            async with self._session.get(
                "https://api.linkedin.com/v2/me?projection=(id,firstName,lastName,headline,profilePicture,vanityName)",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if result["profile"]:
                        result["profile"].headline = data.get("headline", {}).get("localized", {}).get("en_US")
                        result["profile"].username = data.get("vanityName")
        except Exception as e:
            logger.debug(f"LinkedIn extended profile not available: {e}")

        # Note: Positions, education, skills require additional API permissions
        # that are restricted in LinkedIn's API. Would need partnership access.

        return result

    # ==========================================================================
    # Twitter/X
    # ==========================================================================

    async def _ingest_twitter(self) -> Dict:
        """Ingest Twitter profile and tweets"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        result = {
            "profile": None,
            "tweets": [],
            "interests": [],
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Get profile (Twitter API v2)
        try:
            async with self._session.get(
                "https://api.twitter.com/2/users/me?user.fields=id,name,username,description,location,profile_image_url,public_metrics,verified",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    user = data.get("data", {})
                    metrics = user.get("public_metrics", {})

                    result["profile"] = SocialProfile(
                        platform=SocialPlatform.TWITTER,
                        user_id=user.get("id", ""),
                        username=user.get("username"),
                        name=user.get("name", ""),
                        bio=user.get("description"),
                        headline=None,
                        location=user.get("location"),
                        profile_url=f"https://twitter.com/{user.get('username', '')}",
                        avatar_url=user.get("profile_image_url"),
                        followers_count=metrics.get("followers_count", 0),
                        following_count=metrics.get("following_count", 0),
                        posts_count=metrics.get("tweet_count", 0),
                        verified=user.get("verified", False),
                    )
                else:
                    logger.warning(f"Twitter profile fetch failed: {resp.status}")
        except Exception as e:
            logger.error(f"Twitter profile error: {e}")

        # Get recent tweets
        if result["profile"]:
            try:
                user_id = result["profile"].user_id
                async with self._session.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets?max_results={min(self.max_posts, 100)}&tweet.fields=created_at,public_metrics,text",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tweet in data.get("data", []):
                            metrics = tweet.get("public_metrics", {})
                            created_at = None
                            if tweet.get("created_at"):
                                created_at = datetime.fromisoformat(
                                    tweet["created_at"].replace("Z", "+00:00")
                                )

                            result["tweets"].append(SocialContent(
                                id=tweet.get("id", ""),
                                platform=SocialPlatform.TWITTER,
                                content_type=ContentType.TWEET,
                                text=tweet.get("text"),
                                created_at=created_at,
                                url=f"https://twitter.com/{result['profile'].username}/status/{tweet.get('id')}",
                                engagement={
                                    "likes": metrics.get("like_count", 0),
                                    "retweets": metrics.get("retweet_count", 0),
                                    "replies": metrics.get("reply_count", 0),
                                },
                            ))
            except Exception as e:
                logger.error(f"Twitter tweets error: {e}")

        # Extract interests from tweets (topics, hashtags)
        if result["tweets"]:
            hashtags = set()
            for tweet in result["tweets"]:
                if tweet.text:
                    import re
                    tags = re.findall(r'#(\w+)', tweet.text)
                    hashtags.update(tags)
            result["interests"] = list(hashtags)[:50]

        return result

    # ==========================================================================
    # Facebook
    # ==========================================================================

    async def _ingest_facebook(self) -> Dict:
        """Ingest Facebook profile and posts"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        result = {
            "profile": None,
            "posts": [],
        }

        # Get profile
        try:
            async with self._session.get(
                "https://graph.facebook.com/me?fields=id,name,email,picture,link,about,location",
                params={"access_token": self.access_token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["profile"] = SocialProfile(
                        platform=SocialPlatform.FACEBOOK,
                        user_id=data.get("id", ""),
                        username=None,
                        name=data.get("name", ""),
                        bio=data.get("about"),
                        headline=None,
                        location=data.get("location", {}).get("name"),
                        profile_url=data.get("link", f"https://facebook.com/{data.get('id')}"),
                        avatar_url=data.get("picture", {}).get("data", {}).get("url"),
                    )
                else:
                    logger.warning(f"Facebook profile fetch failed: {resp.status}")
        except Exception as e:
            logger.error(f"Facebook profile error: {e}")

        # Get posts (requires user_posts permission)
        try:
            async with self._session.get(
                f"https://graph.facebook.com/me/posts?fields=id,message,created_time,permalink_url,likes.summary(true),comments.summary(true)&limit={self.max_posts}",
                params={"access_token": self.access_token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for post in data.get("data", []):
                        created_at = None
                        if post.get("created_time"):
                            created_at = datetime.fromisoformat(
                                post["created_time"].replace("+0000", "+00:00")
                            )

                        result["posts"].append(SocialContent(
                            id=post.get("id", ""),
                            platform=SocialPlatform.FACEBOOK,
                            content_type=ContentType.POST,
                            text=post.get("message"),
                            created_at=created_at,
                            url=post.get("permalink_url"),
                            engagement={
                                "likes": post.get("likes", {}).get("summary", {}).get("total_count", 0),
                                "comments": post.get("comments", {}).get("summary", {}).get("total_count", 0),
                            },
                        ))
        except Exception as e:
            logger.error(f"Facebook posts error: {e}")

        return result

    # ==========================================================================
    # Instagram
    # ==========================================================================

    async def _ingest_instagram(self) -> Dict:
        """Ingest Instagram profile and posts"""
        if not self._session:
            self._session = aiohttp.ClientSession()

        result = {
            "profile": None,
            "posts": [],
        }

        # Get profile (Instagram Basic Display API)
        try:
            async with self._session.get(
                "https://graph.instagram.com/me?fields=id,username,account_type,media_count",
                params={"access_token": self.access_token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["profile"] = SocialProfile(
                        platform=SocialPlatform.INSTAGRAM,
                        user_id=data.get("id", ""),
                        username=data.get("username"),
                        name=data.get("username", ""),  # IG doesn't provide name
                        bio=None,
                        headline=None,
                        location=None,
                        profile_url=f"https://instagram.com/{data.get('username', '')}",
                        avatar_url=None,
                        posts_count=data.get("media_count", 0),
                        metadata={"account_type": data.get("account_type")},
                    )
                else:
                    logger.warning(f"Instagram profile fetch failed: {resp.status}")
        except Exception as e:
            logger.error(f"Instagram profile error: {e}")

        # Get media
        try:
            async with self._session.get(
                f"https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count&limit={self.max_posts}",
                params={"access_token": self.access_token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for media in data.get("data", []):
                        created_at = None
                        if media.get("timestamp"):
                            created_at = datetime.fromisoformat(
                                media["timestamp"].replace("Z", "+00:00")
                            )

                        result["posts"].append(SocialContent(
                            id=media.get("id", ""),
                            platform=SocialPlatform.INSTAGRAM,
                            content_type=ContentType.POST,
                            text=media.get("caption"),
                            created_at=created_at,
                            url=media.get("permalink"),
                            engagement={
                                "likes": media.get("like_count", 0),
                                "comments": media.get("comments_count", 0),
                            },
                            metadata={
                                "media_type": media.get("media_type"),
                                "media_url": media.get("media_url"),
                            },
                        ))
        except Exception as e:
            logger.error(f"Instagram media error: {e}")

        return result

    # ==========================================================================
    # Summary Generation
    # ==========================================================================

    def _generate_summary(
        self,
        profile: Optional[SocialProfile],
        experiences: List[WorkExperience],
        education: List[Education],
        skills: List[str],
        content: List[SocialContent],
        interests: List[str]
    ) -> Dict:
        """Generate a summary of the user's social presence"""
        summary = {
            "has_profile": profile is not None,
            "platform": self.platform.value,
            "content_count": len(content),
        }

        if profile:
            summary["name"] = profile.name
            summary["username"] = profile.username
            summary["bio"] = profile.bio
            summary["headline"] = profile.headline
            summary["location"] = profile.location
            summary["followers"] = profile.followers_count

        if experiences:
            current_job = next((e for e in experiences if e.is_current), None)
            if current_job:
                summary["current_role"] = f"{current_job.title} at {current_job.company}"
            summary["total_experiences"] = len(experiences)
            summary["companies"] = list(set(e.company for e in experiences))[:10]

        if education:
            summary["education_count"] = len(education)
            summary["schools"] = list(set(e.school for e in education))[:5]

        if skills:
            summary["skills_count"] = len(skills)
            summary["top_skills"] = skills[:10]

        if interests:
            summary["interests"] = interests[:20]

        if content:
            # Calculate engagement stats
            total_engagement = sum(
                c.engagement.get("likes", 0) + c.engagement.get("comments", 0) + c.engagement.get("retweets", 0)
                for c in content
            )
            summary["total_engagement"] = total_engagement
            summary["avg_engagement"] = total_engagement / len(content) if content else 0

            # Most recent post
            sorted_content = sorted(
                [c for c in content if c.created_at],
                key=lambda x: x.created_at,
                reverse=True
            )
            if sorted_content:
                summary["last_post_date"] = sorted_content[0].created_at.isoformat()

        return summary


# Factory function
async def ingest_social_history(
    access_token: str,
    platform: str,
    max_posts: int = 100
) -> SocialHistoryResult:
    """
    Factory function to ingest social history.

    Args:
        access_token: OAuth access token
        platform: Platform name (linkedin, twitter, facebook, instagram)
        max_posts: Maximum posts to fetch

    Returns:
        SocialHistoryResult
    """
    platform_enum = SocialPlatform(platform)

    async with SocialHistoryIngestion(
        access_token=access_token,
        platform=platform_enum,
        max_posts=max_posts
    ) as ingestion:
        return await ingestion.ingest()
