"""
Sequential Thinking Tool for Chat with Tools Framework

This tool enables structured, step-by-step reasoning through complex problems.
It supports revision of previous thoughts, branching into alternative solutions,
and maintains a complete thinking history.

Inspired by MCP's sequential thinking approach.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_tool import BaseTool


class ThoughtNode:
    """Represents a single thought in the thinking chain."""
    
    def __init__(
        self,
        thought_number: int,
        content: str,
        thought_type: str = "analysis",
        confidence: float = 1.0,
        parent_thought: Optional[int] = None,
        revises_thought: Optional[int] = None,
        branches_from: Optional[int] = None
    ):
        self.thought_number = thought_number
        self.content = content
        self.thought_type = thought_type  # analysis, hypothesis, revision, conclusion, question
        self.confidence = confidence
        self.parent_thought = parent_thought
        self.revises_thought = revises_thought
        self.branches_from = branches_from
        self.timestamp = datetime.now().isoformat()
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thought node to dictionary."""
        return {
            "thought_number": self.thought_number,
            "content": self.content,
            "type": self.thought_type,
            "confidence": self.confidence,
            "parent_thought": self.parent_thought,
            "revises_thought": self.revises_thought,
            "branches_from": self.branches_from,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ThinkingSession:
    """Manages a complete thinking session with history and branches."""
    
    def __init__(self, problem_statement: str):
        self.problem_statement = problem_statement
        self.thoughts: List[ThoughtNode] = []
        self.current_thought_number = 0
        self.branches: Dict[str, List[int]] = {"main": []}
        self.current_branch = "main"
        self.start_time = time.time()
        self.metadata = {
            "total_thoughts": 0,
            "revisions": 0,
            "branches_created": 0,
            "confidence_trend": []
        }
    
    def add_thought(
        self,
        content: str,
        thought_type: str = "analysis",
        confidence: float = 1.0,
        revises_thought: Optional[int] = None,
        branch_from: Optional[int] = None,
        branch_name: Optional[str] = None
    ) -> ThoughtNode:
        """Add a new thought to the session."""
        self.current_thought_number += 1
        
        # Handle branching
        if branch_from is not None and branch_name:
            if branch_name not in self.branches:
                self.branches[branch_name] = []
                self.metadata["branches_created"] += 1
            self.current_branch = branch_name
            parent = branch_from
        else:
            parent = self.thoughts[-1].thought_number if self.thoughts else None
        
        # Create thought node
        thought = ThoughtNode(
            thought_number=self.current_thought_number,
            content=content,
            thought_type=thought_type,
            confidence=confidence,
            parent_thought=parent,
            revises_thought=revises_thought,
            branches_from=branch_from
        )
        
        # Update metadata
        if revises_thought:
            self.metadata["revisions"] += 1
        
        self.metadata["total_thoughts"] += 1
        self.metadata["confidence_trend"].append(confidence)
        
        # Add to appropriate branch
        self.thoughts.append(thought)
        self.branches[self.current_branch].append(self.current_thought_number)
        
        return thought
    
    def get_thinking_path(self, branch: str = "main") -> List[ThoughtNode]:
        """Get the thinking path for a specific branch."""
        if branch not in self.branches:
            return []
        
        return [t for t in self.thoughts if t.thought_number in self.branches[branch]]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the thinking session."""
        elapsed_time = time.time() - self.start_time
        avg_confidence = (
            sum(self.metadata["confidence_trend"]) / len(self.metadata["confidence_trend"])
            if self.metadata["confidence_trend"] else 0
        )
        
        return {
            "problem": self.problem_statement,
            "total_thoughts": self.metadata["total_thoughts"],
            "revisions": self.metadata["revisions"],
            "branches": len(self.branches),
            "average_confidence": round(avg_confidence, 2),
            "thinking_time": round(elapsed_time, 2),
            "thoughts_per_minute": round(self.metadata["total_thoughts"] / (elapsed_time / 60), 2) if elapsed_time > 0 else 0
        }
    
    def export_thinking_chain(self) -> Dict[str, Any]:
        """Export the complete thinking chain."""
        return {
            "problem": self.problem_statement,
            "summary": self.get_summary(),
            "branches": {
                branch: [self.thoughts[i-1].to_dict() for i in thought_nums if i <= len(self.thoughts)]
                for branch, thought_nums in self.branches.items()
            },
            "all_thoughts": [t.to_dict() for t in self.thoughts]
        }


class SequentialThinkingTool(BaseTool):
    """
    Sequential thinking tool that enables step-by-step reasoning with revision capabilities.
    
    This tool helps break down complex problems into manageable thinking steps,
    supports revising previous thoughts, and can branch into alternative solutions.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.sessions: Dict[str, ThinkingSession] = {}
        self.current_session_id: Optional[str] = None
    
    @property
    def name(self) -> str:
        return "sequential_thinking"
    
    @property
    def description(self) -> str:
        return """Think through a problem step-by-step with the ability to revise and branch thoughts.
        
        Use this tool to:
        - Break down complex problems into sequential steps
        - Revise previous thoughts when new insights emerge
        - Branch into alternative solution paths
        - Track confidence levels throughout reasoning
        - Generate structured thinking chains for analysis
        
        Thought types: 'analysis', 'hypothesis', 'revision', 'question', 'conclusion'
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "think", "revise", "branch", "conclude", "get_summary", "export"],
                    "description": "Action to perform"
                },
                "problem": {
                    "type": "string",
                    "description": "Problem statement (required for 'start' action)"
                },
                "thought": {
                    "type": "string",
                    "description": "The thought content (required for 'think', 'revise', 'branch', 'conclude')"
                },
                "thought_type": {
                    "type": "string",
                    "enum": ["analysis", "hypothesis", "revision", "question", "conclusion"],
                    "default": "analysis",
                    "description": "Type of thought being added"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 1.0,
                    "description": "Confidence level in this thought (0-1)"
                },
                "revises_thought_number": {
                    "type": "integer",
                    "description": "Thought number being revised (for 'revise' action)"
                },
                "branch_from_thought": {
                    "type": "integer",
                    "description": "Thought number to branch from (for 'branch' action)"
                },
                "branch_name": {
                    "type": "string",
                    "description": "Name for the new branch (for 'branch' action)"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID (optional, uses current session if not provided)"
                }
            },
            "required": ["action"]
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{int(time.time() * 1000)}"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute sequential thinking operations."""
        action = kwargs.get("action")
        session_id = kwargs.get("session_id", self.current_session_id)
        
        try:
            if action == "start":
                return self._start_session(kwargs.get("problem", "Undefined problem"))
            
            elif action == "think":
                return self._add_thought(
                    session_id=session_id,
                    thought=kwargs.get("thought", ""),
                    thought_type=kwargs.get("thought_type", "analysis"),
                    confidence=kwargs.get("confidence", 1.0)
                )
            
            elif action == "revise":
                return self._revise_thought(
                    session_id=session_id,
                    thought=kwargs.get("thought", ""),
                    revises_number=kwargs.get("revises_thought_number"),
                    confidence=kwargs.get("confidence", 1.0)
                )
            
            elif action == "branch":
                return self._create_branch(
                    session_id=session_id,
                    thought=kwargs.get("thought", ""),
                    branch_from=kwargs.get("branch_from_thought"),
                    branch_name=kwargs.get("branch_name", f"branch_{int(time.time())}"),
                    confidence=kwargs.get("confidence", 1.0)
                )
            
            elif action == "conclude":
                return self._conclude_session(
                    session_id=session_id,
                    conclusion=kwargs.get("thought", "")
                )
            
            elif action == "get_summary":
                return self._get_summary(session_id)
            
            elif action == "export":
                return self._export_session(session_id)
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Sequential thinking error: {str(e)}"}
    
    def _start_session(self, problem: str) -> Dict[str, Any]:
        """Start a new thinking session."""
        session_id = self._generate_session_id()
        self.sessions[session_id] = ThinkingSession(problem)
        self.current_session_id = session_id
        
        # Add initial thought
        initial_thought = self.sessions[session_id].add_thought(
            content=f"Starting analysis of: {problem}",
            thought_type="analysis",
            confidence=1.0
        )
        
        return {
            "status": "session_started",
            "session_id": session_id,
            "problem": problem,
            "initial_thought": initial_thought.to_dict(),
            "instructions": "Use 'think' action to add thoughts, 'revise' to correct, 'branch' to explore alternatives"
        }
    
    def _add_thought(
        self,
        session_id: str,
        thought: str,
        thought_type: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Add a thought to the session."""
        if session_id not in self.sessions:
            return {"error": "Session not found. Start a session first."}
        
        session = self.sessions[session_id]
        thought_node = session.add_thought(
            content=thought,
            thought_type=thought_type,
            confidence=confidence
        )
        
        return {
            "status": "thought_added",
            "thought": thought_node.to_dict(),
            "total_thoughts": session.metadata["total_thoughts"],
            "current_branch": session.current_branch,
            "next_steps": self._suggest_next_steps(session, thought_node)
        }
    
    def _revise_thought(
        self,
        session_id: str,
        thought: str,
        revises_number: Optional[int],
        confidence: float
    ) -> Dict[str, Any]:
        """Revise a previous thought."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        if revises_number is None:
            return {"error": "Must specify which thought number to revise"}
        
        session = self.sessions[session_id]
        
        # Verify thought exists
        if revises_number > len(session.thoughts):
            return {"error": f"Thought {revises_number} not found"}
        
        revision_node = session.add_thought(
            content=thought,
            thought_type="revision",
            confidence=confidence,
            revises_thought=revises_number
        )
        
        return {
            "status": "thought_revised",
            "revision": revision_node.to_dict(),
            "original_thought": session.thoughts[revises_number - 1].to_dict(),
            "total_revisions": session.metadata["revisions"]
        }
    
    def _create_branch(
        self,
        session_id: str,
        thought: str,
        branch_from: Optional[int],
        branch_name: str,
        confidence: float
    ) -> Dict[str, Any]:
        """Create a new thinking branch."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        branch_node = session.add_thought(
            content=thought,
            thought_type="hypothesis",
            confidence=confidence,
            branch_from=branch_from,
            branch_name=branch_name
        )
        
        return {
            "status": "branch_created",
            "branch_name": branch_name,
            "branch_thought": branch_node.to_dict(),
            "total_branches": len(session.branches),
            "branches": list(session.branches.keys())
        }
    
    def _conclude_session(self, session_id: str, conclusion: str) -> Dict[str, Any]:
        """Add a conclusion and finalize the thinking session."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        conclusion_node = session.add_thought(
            content=conclusion,
            thought_type="conclusion",
            confidence=1.0
        )
        
        # Generate final analysis
        summary = session.get_summary()
        thinking_chain = session.export_thinking_chain()
        
        # Analyze the thinking process
        insights = self._analyze_thinking_process(session)
        
        return {
            "status": "session_concluded",
            "conclusion": conclusion_node.to_dict(),
            "summary": summary,
            "insights": insights,
            "export_data": thinking_chain
        }
    
    def _get_summary(self, session_id: str) -> Dict[str, Any]:
        """Get current session summary."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        return {
            "status": "summary",
            "summary": session.get_summary(),
            "current_branch": session.current_branch,
            "branches": list(session.branches.keys()),
            "latest_thought": session.thoughts[-1].to_dict() if session.thoughts else None
        }
    
    def _export_session(self, session_id: str) -> Dict[str, Any]:
        """Export complete thinking session."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        return {
            "status": "exported",
            "data": self.sessions[session_id].export_thinking_chain()
        }
    
    def _suggest_next_steps(self, session: ThinkingSession, latest_thought: ThoughtNode) -> List[str]:
        """Suggest next steps based on current thinking state."""
        suggestions = []
        
        # Based on thought type
        if latest_thought.thought_type == "question":
            suggestions.append("Answer the question with a hypothesis or analysis")
        elif latest_thought.thought_type == "hypothesis":
            suggestions.append("Test or validate the hypothesis")
            suggestions.append("Consider alternative hypotheses (branch)")
        elif latest_thought.confidence < 0.5:
            suggestions.append("Revise with more confident analysis")
            suggestions.append("Gather more information")
        
        # Based on session state
        if session.metadata["total_thoughts"] > 10 and not any(t.thought_type == "conclusion" for t in session.thoughts):
            suggestions.append("Consider concluding the analysis")
        
        if session.metadata["revisions"] == 0 and session.metadata["total_thoughts"] > 5:
            suggestions.append("Review and potentially revise earlier thoughts")
        
        return suggestions
    
    def _analyze_thinking_process(self, session: ThinkingSession) -> Dict[str, Any]:
        """Analyze the thinking process for insights."""
        thoughts = session.thoughts
        
        # Calculate metrics
        thought_types = {}
        for t in thoughts:
            thought_types[t.thought_type] = thought_types.get(t.thought_type, 0) + 1
        
        confidence_trend = session.metadata["confidence_trend"]
        avg_confidence = sum(confidence_trend) / len(confidence_trend) if confidence_trend else 0
        
        # Detect patterns
        confidence_improving = False
        if len(confidence_trend) >= 3:
            recent_avg = sum(confidence_trend[-3:]) / 3
            early_avg = sum(confidence_trend[:3]) / 3
            confidence_improving = recent_avg > early_avg
        
        return {
            "thought_distribution": thought_types,
            "average_confidence": round(avg_confidence, 2),
            "confidence_improving": confidence_improving,
            "revision_rate": round(session.metadata["revisions"] / session.metadata["total_thoughts"], 2) if session.metadata["total_thoughts"] > 0 else 0,
            "branches_explored": len(session.branches),
            "thinking_style": self._determine_thinking_style(thought_types),
            "depth": session.metadata["total_thoughts"]
        }
    
    def _determine_thinking_style(self, thought_types: Dict[str, int]) -> str:
        """Determine the dominant thinking style."""
        if not thought_types:
            return "undefined"
        
        dominant = max(thought_types, key=thought_types.get)
        
        styles = {
            "analysis": "analytical",
            "hypothesis": "exploratory",
            "revision": "iterative",
            "question": "inquisitive",
            "conclusion": "decisive"
        }
        
        return styles.get(dominant, "balanced")
