#!/usr/bin/env python3
"""
Demonstration: How Phase 1 Tutoring Handles Integration Problems

Shows complete flow from student query to validated tutoring response.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'scripts' / 'cascade'))

from pedagogical_wrapper import PedagogicalWrapper
from response_validator import ResponseValidator


def demonstrate_integration_tutoring():
    """Show how the system handles various integration queries."""

    wrapper = PedagogicalWrapper()
    validator = ResponseValidator()

    # Example scenarios with simulated LLM responses
    scenarios = [
        {
            'name': 'Tutoring Request - "How do I integrate x^2?"',
            'query': 'How do I integrate x^2?',
            'student_answer': None,
            'simulated_llm_response': """Great question! Integration is like "reverse differentiation."

Let's think about this step by step. You know that when we differentiate x^3, we get 3x^2, right?

So here's the key insight: What function, when differentiated, gives us x^2?

Think about the power rule for derivatives:
- When we differentiate x^n, we get n*x^(n-1)

Can you work backwards from that? What power would we need to start with to end up with x^2 after differentiating?

Try figuring out what exponent would work, and I'll guide you from there!"""
        },

        {
            'name': 'Quick Command - "integrate sin(x)"',
            'query': 'integrate sin(x)',
            'student_answer': None,
            'simulated_llm_response': """Step 1 - Understand the Problem:
We need to find the antiderivative of sin(x).

Step 2 - Plan the Solution:
Recall that integration is the reverse of differentiation. What function has sin(x) as its derivative?

Step 3 - Execute:
We know that d/dx[cos(x)] = -sin(x)
Therefore, d/dx[-cos(x)] = sin(x)

So the integral of sin(x) is -cos(x)

Step 4 - Verify:
Differentiating -cos(x) gives us sin(x) ✓

The answer is: -cos(x) + C"""
        },

        {
            'name': 'Verification - Student checking work',
            'query': 'I got x^3/3 + C for the integral of x^2, is that correct?',
            'student_answer': 'x^3/3 + C',
            'simulated_llm_response': """I see you got x^3/3 + C. Excellent work - let's verify this together!

Here's a great way to check if your integral is correct: take the derivative of your answer. If it gives you back the original function (x^2), then you know you're right!

Can you find the derivative of x^3/3?
- Use the power rule
- Don't forget the constant rule (what's the derivative of C?)

Try that differentiation and see what you get. This self-checking technique is super valuable!"""
        },

        {
            'name': 'BAD Response - Answer Leakage',
            'query': 'How do I integrate x^2?',
            'student_answer': None,
            'simulated_llm_response': """To integrate x^2, you use the power rule for integration.

Add 1 to the exponent: 2 + 1 = 3
Divide by the new exponent: x^3/3

The answer is x^3/3 + C."""
        }
    ]

    print("=" * 70)
    print("INTEGRATION PROBLEM TUTORING - COMPLETE FLOW DEMONSTRATION")
    print("=" * 70)

    for scenario in scenarios:
        print(f"\n{'=' * 70}")
        print(f"SCENARIO: {scenario['name']}")
        print('=' * 70)

        # Step 1: Prepare pedagogical prompt
        print(f"\n📝 STUDENT QUERY:")
        print(f"   \"{scenario['query']}\"")
        if scenario['student_answer']:
            print(f"   Student's answer: {scenario['student_answer']}")

        prompt_result = wrapper.prepare_prompt(
            scenario['query'],
            scenario['student_answer']
        )

        # Step 2: Show intent classification
        print(f"\n🎯 INTENT CLASSIFICATION:")
        print(f"   Intent: {prompt_result['intent'].value}")
        print(f"   Mode: {prompt_result['mode'].value}")
        print(f"   Tutoring enabled: {prompt_result['tutoring_mode']}")
        print(f"   Confidence: {prompt_result['metadata']['confidence']:.2f}")

        # Step 3: Show what prompt is sent to LLM
        print(f"\n📤 PROMPT SENT TO LLM:")
        print(f"   Length: {len(prompt_result['prompt'])} chars")
        print(f"   Type: {prompt_result['mode'].value}")
        print(f"   (Prompt contains pedagogical rules and structure)")

        # Step 4: Simulate LLM response
        print(f"\n🤖 SIMULATED LLM RESPONSE:")
        print("   " + "─" * 66)
        for line in scenario['simulated_llm_response'].split('\n'):
            print(f"   {line}")
        print("   " + "─" * 66)

        # Step 5: Validate response
        print(f"\n✅ RESPONSE VALIDATION:")
        validation = validator.validate(
            response=scenario['simulated_llm_response'],
            original_problem=scenario['query'],
            tutoring_mode=prompt_result['tutoring_mode']
        )

        print(f"   Valid: {'✓ YES' if validation['is_valid'] else '✗ NO'}")
        print(f"   Score: {validation['score']:.2f}/1.00")
        print(f"   Checks passed: {validation['passed_checks']}/{validation['total_checks']}")

        if validation['issues']:
            print(f"\n   Issues found:")
            for issue in validation['issues']:
                severity_icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}
                icon = severity_icon.get(issue['severity'].value, '⚪')
                print(f"      {icon} [{issue['severity'].value.upper()}] {issue['message']}")

        if validation['recommendations']:
            print(f"\n   Recommendations:")
            for rec in validation['recommendations']:
                print(f"      • {rec}")

        # Step 6: Show what student sees
        print(f"\n👁️  WHAT STUDENT SEES:")
        if validation['is_valid']:
            print(f"   ✅ Response delivered as-is (validated)")
        else:
            print(f"   ⚠️  Response has issues - consider regenerating")

        print()


if __name__ == '__main__':
    demonstrate_integration_tutoring()
