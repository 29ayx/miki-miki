import json
import os
import time
from datetime import datetime
from collections import defaultdict
import hashlib

class AILearningSystem:
    def __init__(self, learning_file="ai_learning_data.json"):
        self.learning_file = learning_file
        self.learning_data = self.load_learning_data()
        
    def load_learning_data(self):
        """Load existing learning data from file"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Initialize new learning data structure
        return {
            "task_patterns": {},           # Patterns in successful vs failed tasks
            "element_failures": {},        # Elements that failed to be found/clicked
            "website_patterns": {},        # Website-specific patterns
            "action_success_rates": {},    # Success rates of different actions
            "common_mistakes": [],         # List of common mistakes
            "improvement_suggestions": {}, # Suggestions for different scenarios
            "task_completion_stats": {},   # Statistics about task completion
            "last_updated": datetime.now().isoformat()
        }
    
    def save_learning_data(self):
        """Save learning data to file"""
        self.learning_data["last_updated"] = datetime.now().isoformat()
        with open(self.learning_file, 'w') as f:
            json.dump(self.learning_data, f, indent=2)
    
    def record_task_attempt(self, user_goal, actions_taken, success, final_url, screenshot_path=None):
        """Record a task attempt for learning"""
        task_hash = hashlib.md5(user_goal.encode()).hexdigest()[:8]
        
        # Extract key information
        task_info = {
            "goal": user_goal,
            "actions": actions_taken,
            "success": success,
            "final_url": final_url,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path
        }
        
        # Store in learning data
        if task_hash not in self.learning_data["task_patterns"]:
            self.learning_data["task_patterns"][task_hash] = []
        
        self.learning_data["task_patterns"][task_hash].append(task_info)
        
        # Update success statistics
        if user_goal not in self.learning_data["task_completion_stats"]:
            self.learning_data["task_completion_stats"][user_goal] = {"success": 0, "total": 0}
        
        self.learning_data["task_completion_stats"][user_goal]["total"] += 1
        if success:
            self.learning_data["task_completion_stats"][user_goal]["success"] += 1
        
        self.save_learning_data()
    
    def record_element_failure(self, element_description, website, action_type, error_message):
        """Record when an element couldn't be found or interacted with"""
        failure_key = f"{website}_{element_description}_{action_type}"
        
        if failure_key not in self.learning_data["element_failures"]:
            self.learning_data["element_failures"][failure_key] = {
                "count": 0,
                "errors": [],
                "suggestions": []
            }
        
        self.learning_data["element_failures"][failure_key]["count"] += 1
        self.learning_data["element_failures"][failure_key]["errors"].append({
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate suggestions based on failure patterns
        suggestions = self.generate_element_suggestions(element_description, website, action_type)
        self.learning_data["element_failures"][failure_key]["suggestions"] = suggestions
        
        self.save_learning_data()
    
    def record_action_success(self, action_type, description, success, website):
        """Record success/failure of specific actions"""
        action_key = f"{action_type}_{website}"
        
        if action_key not in self.learning_data["action_success_rates"]:
            self.learning_data["action_success_rates"][action_key] = {
                "success": 0,
                "total": 0,
                "descriptions": []
            }
        
        self.learning_data["action_success_rates"][action_key]["total"] += 1
        if success:
            self.learning_data["action_success_rates"][action_key]["success"] += 1
        
        self.learning_data["action_success_rates"][action_key]["descriptions"].append({
            "description": description,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_learning_data()
    
    def generate_element_suggestions(self, element_description, website, action_type):
        """Generate suggestions based on common failure patterns"""
        suggestions = []
        
        # Website-specific suggestions
        if "youtube" in website.lower():
            if "video" in element_description.lower():
                suggestions.extend([
                    "Try YouTube-specific selectors: ytd-video-renderer, video-title",
                    "Look for video thumbnails with specific positioning",
                    "Check if video is in a grid or list layout"
                ])
            elif "search" in element_description.lower():
                suggestions.extend([
                    "YouTube search bar is usually at the top center",
                    "Try clicking the search box before typing",
                    "Look for search suggestions that appear"
                ])
        
        elif "google" in website.lower():
            if "search" in element_description.lower():
                suggestions.extend([
                    "Google search box is in the center of the page",
                    "Try input[name='q'] or textarea[name='q']",
                    "Look for the large search box below the logo"
                ])
        
        elif "amazon" in website.lower():
            if "product" in element_description.lower():
                suggestions.extend([
                    "Amazon products are in data-component-type='search-result'",
                    "Look for product images and titles",
                    "Check for 'Add to Cart' buttons"
                ])
        
        # Action-specific suggestions
        if action_type == "click":
            suggestions.extend([
                "Try multiple selectors: button, a, [role='button']",
                "Check if element is visible and enabled",
                "Try scrolling to element before clicking",
                "Look for alternative text or aria-labels"
            ])
        elif action_type == "type":
            suggestions.extend([
                "Try input[type='text'], input[type='search'], textarea",
                "Check if input field is focused/active",
                "Look for placeholder text to identify fields"
            ])
        
        return suggestions
    
    def get_improvement_suggestions(self, user_goal, current_website):
        """Get improvement suggestions based on past learning"""
        suggestions = []
        
        # Check for similar failed tasks
        for task_hash, attempts in self.learning_data["task_patterns"].items():
            for attempt in attempts:
                if not attempt["success"] and self.similar_goals(user_goal, attempt["goal"]):
                    # Analyze what went wrong - actions are tuples (action_type, description)
                    failed_actions = [a for a in attempt["actions"] if isinstance(a, tuple) and len(a) >= 2]
                    if failed_actions:
                        suggestions.append(f"Similar task failed: {attempt['goal']}")
                        suggestions.append(f"Failed actions: {[f'{a[0]}: {a[1]}' for a in failed_actions[:3]]}")
        
        # Check for website-specific patterns
        if current_website in self.learning_data["website_patterns"]:
            website_patterns = self.learning_data["website_patterns"][current_website]
            if "common_elements" in website_patterns:
                suggestions.extend(website_patterns["common_elements"])
        
        # Check for element failures on this website
        for failure_key, failure_data in self.learning_data["element_failures"].items():
            if current_website in failure_key and failure_data["count"] > 2:
                suggestions.extend(failure_data["suggestions"][:3])  # Top 3 suggestions
        
        return list(set(suggestions))  # Remove duplicates
    
    def similar_goals(self, goal1, goal2):
        """Check if two goals are similar"""
        # Simple similarity check - can be enhanced with NLP
        keywords1 = set(goal1.lower().split())
        keywords2 = set(goal2.lower().split())
        common = keywords1.intersection(keywords2)
        return len(common) >= 2  # At least 2 common keywords
    
    def get_learned_strategies(self, user_goal, website):
        """Get learned strategies for similar tasks"""
        strategies = []
        
        # Find successful similar tasks
        for task_hash, attempts in self.learning_data["task_patterns"].items():
            successful_attempts = [a for a in attempts if a["success"]]
            for attempt in successful_attempts:
                if self.similar_goals(user_goal, attempt["goal"]) and website in attempt["final_url"]:
                    strategies.append({
                        "goal": attempt["goal"],
                        "actions": attempt["actions"],
                        "success_rate": len(successful_attempts) / len(attempts)
                    })
        
        return strategies
    
    def analyze_common_mistakes(self):
        """Analyze and identify common mistakes"""
        common_mistakes = []
        
        # Analyze element failures
        for failure_key, failure_data in self.learning_data["element_failures"].items():
            if failure_data["count"] >= 3:  # Mistake made 3+ times
                common_mistakes.append({
                    "type": "element_failure",
                    "description": failure_key,
                    "count": failure_data["count"],
                    "suggestions": failure_data["suggestions"]
                })
        
        # Analyze low success rate actions
        for action_key, action_data in self.learning_data["action_success_rates"].items():
            if action_data["total"] >= 5:  # At least 5 attempts
                success_rate = action_data["success"] / action_data["total"]
                if success_rate < 0.5:  # Less than 50% success
                    common_mistakes.append({
                        "type": "low_success_action",
                        "description": action_key,
                        "success_rate": success_rate,
                        "total_attempts": action_data["total"]
                    })
        
        self.learning_data["common_mistakes"] = common_mistakes
        self.save_learning_data()
        return common_mistakes
    
    def get_learning_summary(self):
        """Get a summary of what the AI has learned"""
        total_tasks = sum(len(attempts) for attempts in self.learning_data["task_patterns"].values())
        successful_tasks = sum(
            sum(1 for attempt in attempts if attempt["success"])
            for attempts in self.learning_data["task_patterns"].values()
        )
        
        return {
            "total_tasks_attempted": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "common_mistakes_count": len(self.learning_data["common_mistakes"]),
            "element_failures_count": len(self.learning_data["element_failures"]),
            "websites_learned": list(set(
                key.split('_')[0] for key in self.learning_data["element_failures"].keys()
            )),
            "last_updated": self.learning_data["last_updated"]
        }
