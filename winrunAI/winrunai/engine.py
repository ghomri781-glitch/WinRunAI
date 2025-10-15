from .database import find_fix_for_error, initialize_database

# Ensure the database exists and is populated when the engine is first imported.
initialize_database()

class AIEngine:
    """
    The AI Decision Engine for WinRunAI.

    This class is responsible for taking input (like error messages) and
    deciding on a course of action.
    """
    def __init__(self, config=None):
        """
        Initializes the AI engine.

        Args:
            config: A configuration object (from YAML/JSON) for future settings,
                    like enabling/disabling LLM integration.
        """
        self.config = config or {}
        self.rule_based_only = self.config.get('llm_enabled', False) is False

    def get_suggestion(self, error_string: str, wineprefix: str):
        """
        Analyzes an error string and returns a suggested action plan.

        This currently uses the rule-based expert system. Future versions
        could integrate an LLM as a fallback.

        Args:
            error_string: The error line from the Wine log.
            wineprefix: The full path to the WINEPREFIX for the application.

        Returns:
            A dictionary representing the action plan, or None if no suggestion found.
        """

        # 1. Try the rule-based expert system first.
        fix_rule = find_fix_for_error(error_string)

        if fix_rule:
            # A high-confidence fix was found. Formulate the action plan.
            action_plan = {
                'source': 'Rule-Based System',
                'description': f"Detected issue with '{fix_rule['pattern']}'. The recommended fix is to install '{fix_rule['argument']}' using '{fix_rule['type']}'.",
                'confidence': fix_rule['confidence'],
                'wineprefix': wineprefix,
                'actions': [
                    {
                        'tool': fix_rule['type'],
                        'argument': fix_rule['argument']
                    }
                ]
            }
            return action_plan

        # 2. (Future) If no rule found, and LLM is enabled, query the LLM.
        if not self.rule_based_only:
            # Placeholder for LLM integration
            # llm_suggestion = self.query_local_llm(error_string)
            # if llm_suggestion:
            #     return llm_suggestion
            pass

        # 3. No suggestion found.
        return None

if __name__ == '__main__':
    # Example usage:
    engine = AIEngine()

    test_error = "002c:err:module:import_dll Library msvcp140.dll not found."
    test_prefix = "/home/user/.wine"

    suggestion = engine.get_suggestion(test_error, test_prefix)

    if suggestion:
        print("AI Engine generated a suggestion:")
        print(f"  Source: {suggestion['source']}")
        print(f"  Description: {suggestion['description']}")
        print(f"  Confidence: {suggestion['confidence'] * 100:.0f}%")
        print(f"  Target Prefix: {suggestion['wineprefix']}")
        for i, action in enumerate(suggestion['actions']):
            print(f"  Action #{i+1}: Run '{action['tool']}' with argument '{action['argument']}'")
    else:
        print("AI Engine could not find a suggestion for the test error.")
