from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import Config
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.positive_threshold = Config.SENTIMENT_THRESHOLD_POSITIVE
        self.negative_threshold = Config.SENTIMENT_THRESHOLD_NEGATIVE
        
        # Mental health specific keywords and their weights
        self.mental_health_keywords = {
            # Positive indicators
            'happy': 0.8, 'joy': 0.8, 'grateful': 0.7, 'peaceful': 0.6, 'calm': 0.6,
            'hopeful': 0.7, 'optimistic': 0.7, 'confident': 0.6, 'motivated': 0.6,
            'relaxed': 0.5, 'content': 0.5, 'fulfilled': 0.7, 'accomplished': 0.6,
            
            # Negative indicators  
            'depressed': -0.8, 'anxious': -0.7, 'worried': -0.6, 'stressed': -0.7,
            'overwhelmed': -0.8, 'hopeless': -0.9, 'suicidal': -1.0, 'panic': -0.8,
            'lonely': -0.7, 'isolated': -0.6, 'exhausted': -0.6, 'worthless': -0.9,
            'guilty': -0.6, 'angry': -0.7, 'frustrated': -0.6, 'scared': -0.7,
            
            # Neutral/coping indicators
            'therapy': 0.2, 'counseling': 0.2, 'meditation': 0.3, 'exercise': 0.3,
            'help': 0.1, 'support': 0.2, 'coping': 0.2, 'managing': 0.1
        }
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of text and return detailed results
        
        Returns:
            dict: Contains compound score, individual scores, label, and confidence
        """
        if not text or not text.strip():
            return self._get_neutral_result()
        
        try:
            # Get VADER scores
            scores = self.analyzer.polarity_scores(text.lower())
            
            # Adjust scores based on mental health keywords
            adjusted_compound = self._adjust_for_mental_health_context(text.lower(), scores['compound'])
            
            # Determine sentiment label
            sentiment_label = self._get_sentiment_label(adjusted_compound)
            
            # Calculate confidence level
            confidence = self._calculate_confidence(scores)
            
            result = {
                'compound': adjusted_compound,
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu'],
                'label': sentiment_label,
                'confidence': confidence,
                'raw_compound': scores['compound']
            }
            
            logger.debug(f"Sentiment analysis for '{text[:50]}...': {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return self._get_neutral_result()
    
    def _adjust_for_mental_health_context(self, text, original_score):
        """Adjust sentiment score based on mental health specific keywords"""
        adjustment = 0
        text_words = text.split()
        
        for word in text_words:
            if word in self.mental_health_keywords:
                adjustment += self.mental_health_keywords[word]
        
        # Normalize adjustment based on text length
        if len(text_words) > 0:
            adjustment = adjustment / len(text_words) * 10  # Scale factor
        
        # Combine original score with adjustment
        adjusted_score = original_score + (adjustment * 0.3)  # 30% weight to adjustments
        
        # Ensure score stays within bounds [-1, 1]
        return max(-1.0, min(1.0, adjusted_score))
    
    def _get_sentiment_label(self, compound_score):
        """Convert compound score to sentiment label"""
        if compound_score >= self.positive_threshold:
            return 'positive'
        elif compound_score <= self.negative_threshold:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(self, scores):
        """Calculate confidence level of sentiment analysis"""
        # Higher confidence when scores are more extreme
        max_score = max(scores['pos'], scores['neg'], scores['neu'])
        
        # Consider the compound score magnitude
        compound_magnitude = abs(scores['compound'])
        
        # Combine both factors
        confidence = (max_score + compound_magnitude) / 2
        
        return round(min(1.0, confidence), 3)
    
    def _get_neutral_result(self):
        """Return neutral sentiment result for empty/invalid input"""
        return {
            'compound': 0.0,
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 1.0,
            'label': 'neutral',
            'confidence': 0.0,
            'raw_compound': 0.0
        }
    
    def analyze_mood_trend(self, sentiment_scores):
        """
        Analyze trend in sentiment scores over time
        
        Args:
            sentiment_scores: List of sentiment scores (compound values)
            
        Returns:
            dict: Trend analysis results
        """
        if not sentiment_scores or len(sentiment_scores) < 2:
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'magnitude': 0,
                'stability': 'unknown'
            }
        
        # Calculate trend direction
        recent_avg = sum(sentiment_scores[-3:]) / len(sentiment_scores[-3:])
        earlier_avg = sum(sentiment_scores[:3]) / len(sentiment_scores[:3])
        
        trend_direction = recent_avg - earlier_avg
        
        # Determine trend labels
        if trend_direction > 0.2:
            trend = 'improving'
            direction = 'positive'
        elif trend_direction < -0.2:
            trend = 'declining'
            direction = 'negative'
        else:
            trend = 'stable'
            direction = 'neutral'
        
        # Calculate stability (variance)
        avg_score = sum(sentiment_scores) / len(sentiment_scores)
        variance = sum((score - avg_score) ** 2 for score in sentiment_scores) / len(sentiment_scores)
        
        if variance < 0.1:
            stability = 'very_stable'
        elif variance < 0.3:
            stability = 'stable'
        elif variance < 0.6:
            stability = 'somewhat_volatile'
        else:
            stability = 'volatile'
        
        return {
            'trend': trend,
            'direction': direction,
            'magnitude': abs(trend_direction),
            'stability': stability,
            'recent_average': recent_avg,
            'overall_average': avg_score,
            'variance': variance
        }
    
    def get_supportive_response_tone(self, sentiment_label, confidence):
        """
        Suggest response tone based on sentiment analysis
        
        Returns:
            dict: Suggested response characteristics
        """
        if sentiment_label == 'negative' and confidence > 0.7:
            return {
                'tone': 'highly_empathetic',
                'approach': 'validating_and_supportive',
                'urgency': 'high',
                'suggested_resources': ['crisis_support', 'coping_strategies']
            }
        elif sentiment_label == 'negative':
            return {
                'tone': 'empathetic',
                'approach': 'gentle_and_understanding',
                'urgency': 'medium',
                'suggested_resources': ['coping_strategies', 'mindfulness']
            }
        elif sentiment_label == 'positive':
            return {
                'tone': 'encouraging',
                'approach': 'reinforcing_and_building',
                'urgency': 'low',
                'suggested_resources': ['maintenance_strategies', 'growth_activities']
            }
        else:  # neutral
            return {
                'tone': 'balanced',
                'approach': 'exploratory_and_open',
                'urgency': 'low',
                'suggested_resources': ['general_wellbeing', 'self_reflection']
            }