"""
Gemini Adapter - Clean interface for Gemini API integration.

Provides simple methods for:
- Generating content
- Counting tokens
- Validating prompts
"""

from typing import Any


class GeminiAdapter:
    """
    Simple adapter for Gemini API.

    Use this to connect to Gemini without worrying about API details.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        """
        Initialize Gemini Adapter.

        Args:
            api_key: Your Gemini API key from Google AI Studio
            model_name: Model to use (default: gemini-2.5-flash)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = 1000000  # Default for gemini-2.5-flash

    # ══════════════════════════════════════════════════════════════════════════
    # Generate Content
    # ══════════════════════════════════════════════════════════════════════════

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate content from a prompt.

        Args:
            prompt: Your question or request
            system_instruction: System instruction (optional)

        Returns:
            {
                "success": True,
                "text": "Generated response",
                "model": "gemini-2.5-flash",
                "tokens_used": 150
            }

        Example:
            result = adapter.generate(
                prompt="Hello, how can I learn?",
                system_instruction="You are a good teacher"
            )
            if result["success"]:
                print(result["text"])
        """
        try:
            from google import genai
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                system_instruction=system_instruction,
            )

            client = genai.Client(api_key=self.api_key)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            return {
                "success": True,
                "text": response.text,
                "model": self.model_name,
                "tokens_used": self._estimate_tokens(response.text),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": self._get_error_code(str(e)),
            }

    # ══════════════════════════════════════════════════════════════════════════
    # Generate with Context
    # ══════════════════════════════════════════════════════════════════════════

    def generate_with_context(
        self,
        user_input: str,
        context: list[dict] | None = None,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate content with conversation context.

        Args:
            user_input: Current user message
            context: Previous messages [{"role": "user", "text": "..."}, ...]
            system_instruction: System instruction (optional)

        Returns:
            Same as generate()

        Example:
            context = [
                {"role": "user", "text": "Hello"},
                {"role": "assistant", "text": "Hello! How can I help you?"}
            ]
            result = adapter.generate_with_context(
                user_input="Teach me about Python",
                context=context,
                system_instruction="You are a programmer"
            )
        """
        # Build full prompt with context
        prompt_parts = []

        if context:
            for msg in context:
                role = msg.get("role", "user")
                text = msg.get("text", "")
                if role == "user":
                    prompt_parts.append(f"User: {text}")
                else:
                    prompt_parts.append(f"Assistant: {text}")

        prompt_parts.append(f"User: {user_input}")
        full_prompt = "\n\n".join(prompt_parts)

        return self.generate(
            prompt=full_prompt,
            system_instruction=system_instruction,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Count Tokens
    # ══════════════════════════════════════════════════════════════════════════

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Example:
            count = adapter.count_tokens("Hello world")
            print(f"Tokens: {count}")
        """
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)

            response = client.models.count_tokens(
                model=self.model_name,
                contents=text,
            )

            return response.total_tokens

        except Exception:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4

    # ══════════════════════════════════════════════════════════════════════════
    # Validate Prompt
    # ══════════════════════════════════════════════════════════════════════════

    def validate_prompt(
        self,
        system_prompt: str | None = None,
        user_input: str = "",
        context: str = "",
    ) -> tuple[bool, str | None]:
        """
        Check if prompt won't exceed token limit.

        Args:
            system_prompt: System instruction
            user_input: User message
            context: Context/history

        Returns:
            (is_valid, error_message)

        Example:
            is_valid, error = adapter.validate_prompt(
                system_prompt="You are a teacher",
                user_input="Hello",
                context="Conversation history"
            )
            if not is_valid:
                print(f"Error: {error}")
        """
        try:
            # Build full text
            full_text = ""
            if system_prompt:
                full_text += system_prompt + "\n\n"
            if context:
                full_text += context + "\n\n"
            full_text += user_input

            # Count tokens
            token_count = self.count_tokens(full_text)

            # Check limit (leave 20% buffer)
            limit = int(self.max_tokens * 0.8)

            if token_count > limit:
                return (
                    False,
                    f"Token limit exceeded: {token_count}/{limit}",
                )

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    # ══════════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ══════════════════════════════════════════════════════════════════════════

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)."""
        return len(text) // 4

    def _get_error_code(self, error_msg: str) -> str:
        """Extract error code from error message."""
        error_lower = error_msg.lower()

        if "api_key" in error_lower or "authentication" in error_lower:
            return "INVALID_API_KEY"
        elif "rate" in error_lower or "quota" in error_lower:
            return "RATE_LIMIT"
        elif "token" in error_lower or "length" in error_lower:
            return "TOKEN_LIMIT_EXCEEDED"
        else:
            return "API_ERROR"
