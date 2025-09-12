"""
Text Summarization Tool for Chat with Tools Framework

This tool provides text summarization capabilities using
various strategies for condensing long texts.
"""

import re
import math
from typing import Dict, Any, List, Optional
from collections import Counter
from .base_tool import BaseTool


class TextSummarizer:
    """Text summarization engine with multiple strategies."""
    
    def __init__(self):
        # Common English stop words
        self.stop_words = set([
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was',
            'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'but', 'and', 'or', 'if', 'then',
            'else', 'for', 'from', 'of', 'to', 'in', 'with', 'by', 'about',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further'
        ])
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Convert to lowercase and split by non-alphanumeric characters
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return words
    
    def _sentence_split(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _calculate_word_frequencies(self, words: List[str]) -> Dict[str, float]:
        """Calculate word frequencies excluding stop words."""
        word_freq = Counter(w for w in words if w not in self.stop_words)
        
        # Normalize frequencies
        if word_freq:
            max_freq = max(word_freq.values())
            for word in word_freq:
                word_freq[word] = word_freq[word] / max_freq
        
        return word_freq
    
    def _score_sentences(self, sentences: List[str], word_freq: Dict[str, float]) -> List[float]:
        """Score sentences based on word frequencies."""
        sentence_scores = []
        
        for sentence in sentences:
            words = self._tokenize(sentence)
            score = 0
            word_count = 0
            
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
                    word_count += 1
            
            # Average score per word (avoid division by zero)
            if word_count > 0:
                sentence_scores.append(score / word_count)
            else:
                sentence_scores.append(0)
        
        return sentence_scores
    
    def extractive_summarize(
        self,
        text: str,
        ratio: float = 0.3,
        min_sentences: int = 1,
        max_sentences: Optional[int] = None
    ) -> str:
        """
        Extractive summarization using frequency-based scoring.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to keep (0-1)
            min_sentences: Minimum number of sentences
            max_sentences: Maximum number of sentences
        
        Returns:
            Summary text
        """
        # Split into sentences
        sentences = self._sentence_split(text)
        
        if not sentences:
            return ""
        
        if len(sentences) <= min_sentences:
            return text
        
        # Tokenize and calculate word frequencies
        words = self._tokenize(text)
        word_freq = self._calculate_word_frequencies(words)
        
        # Score sentences
        scores = self._score_sentences(sentences, word_freq)
        
        # Determine number of sentences to keep
        num_sentences = max(
            min_sentences,
            min(
                int(len(sentences) * ratio),
                max_sentences if max_sentences else len(sentences)
            )
        )
        
        # Get top sentences (maintain original order)
        sentence_indices = sorted(
            range(len(sentences)),
            key=lambda i: scores[i],
            reverse=True
        )[:num_sentences]
        
        # Sort by original position
        sentence_indices.sort()
        
        # Build summary
        summary_sentences = [sentences[i] for i in sentence_indices]
        summary = '. '.join(summary_sentences)
        
        # Add period if not present
        if summary and not summary[-1] in '.!?':
            summary += '.'
        
        return summary
    
    def key_points_extraction(self, text: str, num_points: int = 5) -> List[str]:
        """
        Extract key points from text.
        
        Args:
            text: Text to analyze
            num_points: Number of key points to extract
        
        Returns:
            List of key points
        """
        sentences = self._sentence_split(text)
        
        if not sentences:
            return []
        
        # Calculate word frequencies
        words = self._tokenize(text)
        word_freq = self._calculate_word_frequencies(words)
        
        # Score sentences
        scores = self._score_sentences(sentences, word_freq)
        
        # Get top sentences as key points
        num_points = min(num_points, len(sentences))
        top_indices = sorted(
            range(len(sentences)),
            key=lambda i: scores[i],
            reverse=True
        )[:num_points]
        
        # Sort by original order
        top_indices.sort()
        
        key_points = []
        for i, idx in enumerate(top_indices, 1):
            # Clean up sentence
            sentence = sentences[idx].strip()
            if sentence and not sentence[-1] in '.!?':
                sentence += '.'
            key_points.append(sentence)
        
        return key_points
    
    def statistics(self, text: str) -> Dict[str, Any]:
        """
        Calculate text statistics.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary of statistics
        """
        words = self._tokenize(text)
        sentences = self._sentence_split(text)
        paragraphs = text.split('\n\n')
        
        # Calculate readability (simple approximation)
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Flesch Reading Ease approximation
        if sentences and words:
            syllables_per_word = avg_word_length / 3  # Very rough approximation
            flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * syllables_per_word
            flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
            
            if flesch_score >= 90:
                reading_level = "Very Easy"
            elif flesch_score >= 80:
                reading_level = "Easy"
            elif flesch_score >= 70:
                reading_level = "Fairly Easy"
            elif flesch_score >= 60:
                reading_level = "Standard"
            elif flesch_score >= 50:
                reading_level = "Fairly Difficult"
            elif flesch_score >= 30:
                reading_level = "Difficult"
            else:
                reading_level = "Very Difficult"
        else:
            flesch_score = 0
            reading_level = "Unknown"
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "unique_words": len(set(words)),
            "lexical_diversity": round(len(set(words)) / len(words), 2) if words else 0,
            "flesch_reading_ease": round(flesch_score, 1),
            "reading_level": reading_level
        }


class SummarizationTool(BaseTool):
    """
    Text summarization tool for condensing long texts.
    
    This tool provides various summarization strategies including
    extractive summarization and key points extraction.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.summarizer = TextSummarizer()
    
    @property
    def name(self) -> str:
        return "summarizer"
    
    @property
    def description(self) -> str:
        return """Summarize and analyze text using various strategies.
        
        Actions:
        - summarize: Create an extractive summary
        - key_points: Extract main points from text
        - statistics: Analyze text statistics and readability
        
        Use this tool to:
        - Condense long articles or documents
        - Extract main ideas from text
        - Analyze text complexity and readability
        - Create bullet points from paragraphs
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summarize", "key_points", "statistics"],
                    "description": "Type of summarization to perform"
                },
                "text": {
                    "type": "string",
                    "description": "Text to summarize or analyze"
                },
                "ratio": {
                    "type": "number",
                    "default": 0.3,
                    "minimum": 0.1,
                    "maximum": 0.9,
                    "description": "Ratio of original text to keep (for 'summarize')"
                },
                "num_points": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Number of key points to extract (for 'key_points')"
                },
                "min_sentences": {
                    "type": "integer",
                    "default": 1,
                    "description": "Minimum sentences in summary (for 'summarize')"
                },
                "max_sentences": {
                    "type": "integer",
                    "description": "Maximum sentences in summary (for 'summarize')"
                }
            },
            "required": ["action", "text"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute summarization operations."""
        action = kwargs.get("action")
        text = kwargs.get("text", "")
        
        if not text:
            return {"error": "No text provided"}
        
        try:
            if action == "summarize":
                summary = self.summarizer.extractive_summarize(
                    text=text,
                    ratio=kwargs.get("ratio", 0.3),
                    min_sentences=kwargs.get("min_sentences", 1),
                    max_sentences=kwargs.get("max_sentences")
                )
                
                # Calculate reduction
                original_length = len(text)
                summary_length = len(summary)
                reduction = round((1 - summary_length / original_length) * 100, 1) if original_length > 0 else 0
                
                return {
                    "status": "summarized",
                    "summary": summary,
                    "original_length": original_length,
                    "summary_length": summary_length,
                    "reduction_percentage": reduction
                }
            
            elif action == "key_points":
                points = self.summarizer.key_points_extraction(
                    text=text,
                    num_points=kwargs.get("num_points", 5)
                )
                
                return {
                    "status": "extracted",
                    "key_points": points,
                    "num_points": len(points)
                }
            
            elif action == "statistics":
                stats = self.summarizer.statistics(text)
                
                return {
                    "status": "analyzed",
                    "statistics": stats
                }
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}
