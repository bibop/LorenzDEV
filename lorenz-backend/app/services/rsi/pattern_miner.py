"""
LORENZ SaaS - RSI Pattern Miner
================================

Analyzes user interaction patterns to discover potential emergent skills.
Part of the Recursive Self Improvement (RSI) subsystem.

Pattern Detection:
- Repeated tool sequences within sessions
- Common parameter patterns
- Success/failure correlations
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import SkillRun, SkillProposal

logger = logging.getLogger(__name__)


class PatternMiner:
    """
    Mines user interaction patterns to propose emergent skills.
    """
    
    MIN_PATTERN_OCCURRENCES = 3
    MIN_SUCCESS_RATE = 0.7
    LOOKBACK_DAYS = 30
    
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def analyze_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze recent skill runs to find repeating patterns.
        """
        cutoff = datetime.utcnow() - timedelta(days=self.LOOKBACK_DAYS)
        
        # Fetch recent skill runs
        query = select(SkillRun).where(
            SkillRun.tenant_id == self.tenant_id,
            SkillRun.user_id == self.user_id,
            SkillRun.created_at >= cutoff
        ).order_by(SkillRun.created_at)
        
        result = await self.db.execute(query)
        runs = result.scalars().all()
        
        if len(runs) < self.MIN_PATTERN_OCCURRENCES:
            return []
        
        patterns = []
        
        # Pattern 1: Repeated skill sequences
        sequence_patterns = self._find_sequence_patterns(runs)
        patterns.extend(sequence_patterns)
        
        # Pattern 2: Common parameter combinations
        param_patterns = self._find_param_patterns(runs)
        patterns.extend(param_patterns)
        
        return patterns

    def _find_sequence_patterns(self, runs: List[SkillRun]) -> List[Dict[str, Any]]:
        """
        Find repeated sequences of 2-3 skill calls.
        """
        patterns = []
        
        # Build bigrams (pairs of consecutive skills)
        bigrams = []
        for i in range(len(runs) - 1):
            pair = (str(runs[i].skill_id), str(runs[i + 1].skill_id))
            bigrams.append(pair)
        
        # Count occurrences
        counter = Counter(bigrams)
        
        for pair, count in counter.items():
            if count >= self.MIN_PATTERN_OCCURRENCES:
                patterns.append({
                    "type": "sequence",
                    "skills": list(pair),
                    "count": count,
                    "confidence": min(1.0, count / 10),  # Scale to 0-1
                    "suggested_name": f"workflow_{pair[0][:8]}_{pair[1][:8]}",
                    "reasoning": f"Detected repeated sequence of skills ({count} occurrences)"
                })
        
        return patterns

    def _find_param_patterns(self, runs: List[SkillRun]) -> List[Dict[str, Any]]:
        """
        Find common parameter patterns within skill usage.
        """
        patterns = []
        
        # Group by skill
        skill_runs: Dict[str, List[SkillRun]] = {}
        for run in runs:
            skill_id = str(run.skill_id)
            if skill_id not in skill_runs:
                skill_runs[skill_id] = []
            skill_runs[skill_id].append(run)
        
        # Analyze each skill's parameter patterns
        for skill_id, skill_run_list in skill_runs.items():
            if len(skill_run_list) < self.MIN_PATTERN_OCCURRENCES:
                continue
            
            # Extract parameter keys used
            param_keys: List[tuple] = []
            for run in skill_run_list:
                if run.input_data and isinstance(run.input_data, dict):
                    keys = tuple(sorted(run.input_data.keys()))
                    param_keys.append(keys)
            
            # Find common parameter templates
            counter = Counter(param_keys)
            for keys, count in counter.items():
                if count >= self.MIN_PATTERN_OCCURRENCES and len(keys) > 1:
                    patterns.append({
                        "type": "param_template",
                        "skill_id": skill_id,
                        "param_keys": list(keys),
                        "count": count,
                        "confidence": min(1.0, count / 10),
                        "suggested_name": f"template_{skill_id[:8]}",
                        "reasoning": f"Common parameter pattern detected ({count} uses with keys: {', '.join(keys)})"
                    })
        
        return patterns

    async def propose_skills(self) -> List[SkillProposal]:
        """
        Run pattern analysis and create skill proposals.
        """
        patterns = await self.analyze_patterns()
        
        proposals = []
        for pattern in patterns:
            if pattern["confidence"] < self.MIN_SUCCESS_RATE:
                continue
            
            # Check for existing proposal
            existing_query = select(SkillProposal).where(
                SkillProposal.tenant_id == self.tenant_id,
                SkillProposal.suggested_name == pattern["suggested_name"],
                SkillProposal.status == "pending"
            )
            existing = await self.db.execute(existing_query)
            if existing.scalar_one_or_none():
                continue
            
            # Create proposal
            proposal = SkillProposal(
                tenant_id=self.tenant_id,
                suggested_name=pattern["suggested_name"],
                reasoning=pattern["reasoning"],
                confidence=pattern["confidence"],
                proposed_schema={
                    "type": "function",
                    "function": {
                        "name": pattern["suggested_name"],
                        "description": pattern["reasoning"],
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                },
                pattern_data=pattern,
                status="pending"
            )
            
            self.db.add(proposal)
            proposals.append(proposal)
        
        if proposals:
            await self.db.commit()
            logger.info(f"Created {len(proposals)} skill proposals from pattern mining")
        
        return proposals


async def run_pattern_mining(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID
) -> List[SkillProposal]:
    """
    Convenience function to run pattern mining for a user.
    """
    miner = PatternMiner(db, tenant_id, user_id)
    return await miner.propose_skills()
