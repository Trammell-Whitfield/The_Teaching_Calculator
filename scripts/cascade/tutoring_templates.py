#!/usr/bin/env python3
"""
Tutoring Templates - Phase 1 AI Tutor Enhancement
Structured prompt templates for different teaching modes.

Implements Socratic questioning and Chain-of-Thought pedagogical methods.
"""

from typing import Dict, Any, Optional
from enum import Enum


class TutoringMode(Enum):
    """Different modes of tutoring interaction."""
    STANDARD_PROBLEM = "standard_problem"       # Step-by-step problem solving
    CONCEPT_EXPLANATION = "concept_explanation" # Explaining mathematical concepts
    VERIFICATION = "verification"               # Checking student work
    WORD_PROBLEM = "word_problem"              # Context-rich problems
    QUICK_ANSWER = "quick_answer"              # Direct answer (original mode)


class TutoringTemplates:
    """
    Collection of pedagogically-sound prompt templates.

    Each template follows Socratic principles:
    - Never give the final answer initially
    - Ask guiding questions
    - Break problems into manageable steps
    - Encourage student discovery
    """

    # Few-shot examples showing ideal tutoring behavior
    FEW_SHOT_EXAMPLES = {
        'algebra': {
            'problem': 'Solve: 2x + 5 = 13',
            'bad_response': 'The answer is x = 4. You subtract 5 from both sides then divide by 2.',
            'good_response': """Great question about solving equations! Let's think through this together.

Looking at 2x + 5 = 13, what's our goal? We want to get x by itself.

First, what operation is being applied to x? (Hint: look at the left side)
- We have 2x (multiplication)
- And +5 (addition)

Which operation should we undo first to isolate x? Think about what's "closest" to x and what's "farther" from it.

Take your time and tell me what you think the first step should be!"""
        },
        'calculus': {
            'problem': 'Find derivative of x^2',
            'bad_response': 'The derivative is 2x using the power rule.',
            'good_response': """Good question! Before we find the derivative, let's make sure we understand what we're doing.

What does a derivative represent? (Hint: think about slopes or rates of change)

For x^2, do you remember the power rule pattern?
- When we have x^n, what happens to the exponent?
- Where does that exponent go?

Think about the pattern and see if you can apply it to x^2. What do you get?"""
        }
    }

    @staticmethod
    def get_standard_tutoring_template(problem: str) -> str:
        """
        Template for standard math problem tutoring.

        Used when student asks: "How do I solve X?"
        """
        return f"""You are a patient, encouraging mathematics tutor helping a student solve this problem:

"{problem}"

CRITICAL RULES - NEVER VIOLATE:
1. DO NOT give the final answer in your response
2. DO NOT solve the problem completely for the student
3. Ask 1-2 guiding questions to help the student think
4. Offer hints about the approach, not the solution
5. Break the problem into clear steps, but only guide through the FIRST step
6. Keep your response under 150 words (battery efficiency)
7. Use an encouraging, supportive tone

RESPONSE STRUCTURE:
1. Acknowledge the question positively
2. Ask what they think the first step should be
3. Provide a strategic hint or guiding question
4. Invite them to try the first step

EXAMPLE GOOD RESPONSE:
"Great question about [problem type]! Let's work through this step by step.

Looking at this problem, what type of mathematical concept do we need? [Guiding question]

I notice [key observation about the problem]. What do you think we should do first?

Hint: Think about [strategic guidance without giving answer]

Try taking that first step and let me know what you get!"

Now respond to help the student with: "{problem}"

Remember: Guide, don't solve. Encourage discovery, not dependence."""

    @staticmethod
    def get_concept_explanation_template(concept: str) -> str:
        """
        Template for explaining mathematical concepts.

        Used when student asks: "What is X?" or "Explain Y"
        """
        return f"""You are a mathematics tutor explaining the concept of "{concept}" to a student.

TEACHING APPROACH:
1. Start with an intuitive explanation or real-world analogy (30%)
2. Build up to the formal mathematical definition (30%)
3. Show a simple example to illustrate (30%)
4. Invite the student to practice or ask questions (10%)

RULES:
- Keep it conversational and accessible
- Avoid jargon until you've explained the intuition
- Use concrete examples before abstract ones
- Keep under 200 words total
- End with an invitation to explore further

STRUCTURE:
"Let me explain [concept] in a way that builds your intuition.

[Intuitive explanation - use analogy or concrete example]

More formally, [formal definition]

Here's a simple example: [concrete illustration]

Want to try a problem using this concept, or have questions?"

Now explain: "{concept}"

Remember: Understanding before formalism. Intuition before abstraction."""

    @staticmethod
    def get_verification_template(problem: str, student_answer: str) -> str:
        """
        Template for verifying student's work.

        Used when student asks: "Is my answer correct?"
        """
        return f"""You are a mathematics tutor helping a student check their work.

PROBLEM: {problem}
STUDENT'S ANSWER: {student_answer}

VERIFICATION APPROACH - NEVER SAY "CORRECT" OR "WRONG" IMMEDIATELY:
1. Ask the student to explain their reasoning
2. Guide them to self-check their work
3. If wrong, help them find the error without revealing the answer
4. If correct, ask them to verify it a different way

RESPONSE STRUCTURE:
"I see you got {student_answer}. Let's verify this together!

Before I confirm, can you walk me through:
- How did you arrive at that answer?
- What steps did you take?
- Does the answer seem reasonable for this problem?

[If you notice an error, give a hint]:
Let's check [specific step where error occurred]. What happens if we...?

[If correct]:
Good work! Can you verify this is correct by [alternative method]?"

RULES:
- Encourage student self-assessment first
- If wrong, point to WHERE the error is, not what the right answer is
- If correct, build confidence by asking them to verify independently
- Keep under 150 words

Now help the student verify their work on: "{problem}"
Their answer: {student_answer}"""

    @staticmethod
    def get_word_problem_template(problem: str) -> str:
        """
        Template for word problems requiring interpretation.

        Used when problem has real-world context.
        """
        return f"""You are a mathematics tutor helping a student solve this word problem:

"{problem}"

WORD PROBLEM STRATEGY:
1. Help them extract the mathematical structure from the story (30%)
2. Identify what they're looking for (20%)
3. Identify what information is given (20%)
4. Guide them to set up the equation/approach (30%)

RESPONSE STRUCTURE:
"Let's break down this word problem together.

First, what is the problem asking us to find? [Help identify the unknown]

What information does the problem give us? [Help list known values]

Now, what mathematical relationship connects these? [Guide toward equation/formula]

Try setting up the equation based on what we identified. What do you think it should look like?"

RULES:
- Focus on UNDERSTANDING the problem, not just solving it
- Help translate words into math
- Don't solve it for them - guide the setup
- Keep under 150 words

Now help with: "{problem}"

Remember: Understanding the problem is half the solution."""

    @staticmethod
    def get_quick_answer_template(problem: str) -> str:
        """
        Original Chain-of-Thought template for direct answer mode.

        Used when student explicitly wants just the answer (backward compatibility).
        """
        return f"""You are a mathematical expert. Solve this problem using clear step-by-step reasoning.

Problem: {problem}

Solve this problem systematically:

Step 1 - Understand the Problem:
- What is being asked?
- What information is given?
- What mathematical concepts apply?

Step 2 - Plan the Solution:
- What formulas or theorems are needed?
- What is the logical sequence of steps?

Step 3 - Execute the Solution:
[Show all calculations clearly]

Step 4 - Verify the Answer:
- Does the result make sense?
- Can I check it a different way?

IMPORTANT: End your response with "The answer is:" followed by ONLY the final numerical or algebraic answer.

Solution:"""

    @staticmethod
    def select_template(mode: TutoringMode, problem: str,
                       student_answer: Optional[str] = None) -> str:
        """
        Select appropriate template based on tutoring mode.

        Args:
            mode: The tutoring mode to use
            problem: The mathematical problem or concept
            student_answer: Student's proposed answer (for verification mode)

        Returns:
            Formatted prompt template string
        """
        templates = {
            TutoringMode.STANDARD_PROBLEM: TutoringTemplates.get_standard_tutoring_template,
            TutoringMode.CONCEPT_EXPLANATION: TutoringTemplates.get_concept_explanation_template,
            TutoringMode.VERIFICATION: lambda p: TutoringTemplates.get_verification_template(p, student_answer),
            TutoringMode.WORD_PROBLEM: TutoringTemplates.get_word_problem_template,
            TutoringMode.QUICK_ANSWER: TutoringTemplates.get_quick_answer_template,
        }

        template_func = templates.get(mode)
        if template_func:
            return template_func(problem)
        else:
            # Default to standard tutoring
            return TutoringTemplates.get_standard_tutoring_template(problem)

    @staticmethod
    def get_few_shot_examples(problem_type: str, num_examples: int = 2) -> str:
        """
        Get few-shot examples for the given problem type.

        Args:
            problem_type: Type of problem ('algebra', 'calculus', etc.)
            num_examples: Number of examples to include

        Returns:
            Formatted few-shot examples string
        """
        if problem_type in TutoringTemplates.FEW_SHOT_EXAMPLES:
            example = TutoringTemplates.FEW_SHOT_EXAMPLES[problem_type]
            return f"""
EXAMPLE OF GOOD TUTORING:
Problem: {example['problem']}

Bad Response (Don't do this):
{example['bad_response']}

Good Response (Do this):
{example['good_response']}

---
"""
        return ""


def main():
    """Test template generation."""
    print("=" * 70)
    print("TUTORING TEMPLATES TEST")
    print("=" * 70)

    # Test each template type
    test_cases = [
        (TutoringMode.STANDARD_PROBLEM, "Solve: 2x + 5 = 13", None),
        (TutoringMode.CONCEPT_EXPLANATION, "derivative", None),
        (TutoringMode.VERIFICATION, "2x + 5 = 13", "x = 4"),
        (TutoringMode.WORD_PROBLEM, "If Alice has 10 apples and gives 3 to Bob, how many does she have?", None),
        (TutoringMode.QUICK_ANSWER, "Solve: 2x + 5 = 13", None),
    ]

    for mode, problem, student_answer in test_cases:
        print(f"\n{'=' * 70}")
        print(f"MODE: {mode.value}")
        print(f"PROBLEM: {problem}")
        if student_answer:
            print(f"STUDENT ANSWER: {student_answer}")
        print('=' * 70)

        template = TutoringTemplates.select_template(mode, problem, student_answer)
        print(template)
        print()


if __name__ == "__main__":
    main()
