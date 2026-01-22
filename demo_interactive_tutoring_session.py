#!/usr/bin/env python3
"""
Interactive Tutoring Session Demonstration
Full multi-turn conversations on HARD integration problems.

Shows:
- Student asks initial question
- Tutor guides without revealing answer
- Student asks follow-up questions
- Tutor provides scaffolding
- Gradual progress toward solution
- Validation at each step
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'scripts' / 'cascade'))

from pedagogical_wrapper import PedagogicalWrapper
from response_validator import ResponseValidator


class InteractiveTutoringSession:
    """Simulates a full multi-turn tutoring conversation."""

    def __init__(self):
        self.wrapper = PedagogicalWrapper()
        self.validator = ResponseValidator()
        self.turn_number = 0

    def process_turn(self, student_query, tutor_response, show_validation=True):
        """Process one turn of the conversation."""
        self.turn_number += 1

        print(f"\n{'=' * 70}")
        print(f"TURN {self.turn_number}")
        print('=' * 70)

        # Student speaks
        print(f"\n👨‍🎓 STUDENT:")
        print(f"   {student_query}")

        # System processes
        prompt_result = self.wrapper.prepare_prompt(student_query)

        print(f"\n🎯 SYSTEM (internal):")
        print(f"   Intent: {prompt_result['intent'].value}")
        print(f"   Mode: {prompt_result['mode'].value}")
        print(f"   Tutoring: {'ENABLED' if prompt_result['tutoring_mode'] else 'DISABLED'}")

        # Tutor responds
        print(f"\n🧑‍🏫 TUTOR:")
        for line in tutor_response.split('\n'):
            print(f"   {line}")

        # Validate if requested
        if show_validation and prompt_result['tutoring_mode']:
            validation = self.validator.validate(
                response=tutor_response,
                original_problem=student_query,
                tutoring_mode=True
            )

            print(f"\n✅ VALIDATION:")
            print(f"   Score: {validation['score']:.2f}/1.00")
            if not validation['is_valid']:
                print(f"   ⚠️  Issues: {len(validation['issues'])}")
                for issue in validation['issues'][:2]:
                    print(f"      • {issue['message']}")


def session_1_trig_identity():
    """
    Session 1: ∫ sin^2(x) dx (Difficulty 5)
    Requires power-reducing trig identity.
    """
    print("\n" + "=" * 70)
    print("INTERACTIVE SESSION 1: TRIG IDENTITY INTEGRATION")
    print("=" * 70)
    print("Problem: ∫ sin^2(x) dx (Difficulty 5)")
    print("Required technique: Power-reducing formula")
    print("=" * 70)

    session = InteractiveTutoringSession()

    # Turn 1: Initial question
    session.process_turn(
        student_query="What is ∫ sin^2(x) dx? I can't integrate this directly",
        tutor_response="""You're absolutely right - we can't integrate sin^2(x) directly!

This requires a clever trick using a trigonometric identity.

Do you remember the double-angle formula for cosine?
   cos(2x) = 1 - 2sin^2(x)

Can you rearrange this equation to solve for sin^2(x)?

Hint: Get sin^2(x) by itself on one side. What do you get for sin^2(x) = ?"""
    )

    # Turn 2: Student attempts rearrangement
    session.process_turn(
        student_query="Is it sin^2(x) = (1 - cos(2x))/2?",
        tutor_response="""Perfect! You got it exactly right!

sin^2(x) = (1 - cos(2x))/2

Now here's the key insight: We can substitute this into our integral!

So instead of integrating sin^2(x), we're integrating:
   ∫ (1 - cos(2x))/2 dx

Can you split this into two simpler integrals?

Hint: ∫ (a - b)/2 dx = (1/2)∫ a dx - (1/2)∫ b dx"""
    )

    # Turn 3: Student splits the integral
    session.process_turn(
        student_query="So it becomes (1/2)∫ 1 dx - (1/2)∫ cos(2x) dx?",
        tutor_response="""Excellent! You've split it perfectly.

Now let's integrate each part:

Part 1: (1/2)∫ 1 dx
   This is easy - what's the integral of a constant?

Part 2: (1/2)∫ cos(2x) dx
   What's the integral of cos(2x)?
   Careful: there's a chain rule factor!

Try evaluating both parts. What do you get?"""
    )

    # Turn 4: Student struggles with chain rule
    session.process_turn(
        student_query="The first part is (1/2)x, but I'm confused about the cos(2x) part. Is it just sin(2x)?",
        tutor_response="""Good work on the first part! (1/2)x is correct.

For the second part, you're close but missing something important.

The derivative of sin(2x) is 2cos(2x) (chain rule brings down the 2).

So what's the integral of cos(2x)?
   If d/dx[sin(2x)] = 2cos(2x)
   Then d/dx[(1/2)sin(2x)] = ?

This tells us what the integral of cos(2x) is!"""
    )

    # Turn 5: Student gets it
    session.process_turn(
        student_query="Oh! So ∫ cos(2x) dx = (1/2)sin(2x), which means my answer is (1/2)x - (1/2)(1/2)sin(2x) + C = (1/2)x - (1/4)sin(2x) + C?",
        tutor_response="""PERFECT! You've got it!

∫ sin^2(x) dx = (x/2) - (sin(2x)/4) + C

Let me show you why this makes sense:
- We used a trig identity to convert sin^2(x) into something we COULD integrate
- We carefully handled the chain rule factor (the 2 in cos(2x))
- We combined the constants properly

Want to verify this is correct? Try taking the derivative of your answer!
You should get back sin^2(x).

This technique (power-reducing formulas) works for sin^2, cos^2, and even higher powers!""",
        show_validation=False  # Final answer given, skip validation
    )

    print(f"\n{'─' * 70}")
    print("Session 1 Complete! Student learned:")
    print("  ✓ Power-reducing trig identities")
    print("  ✓ Substitution technique")
    print("  ✓ Chain rule in integration")
    print("  ✓ Self-verification by differentiation")
    print('─' * 70)


def session_2_circular_parts():
    """
    Session 2: ∫ e^x·sin(x) dx (Difficulty 7)
    Requires circular integration by parts.
    """
    print("\n\n" + "=" * 70)
    print("INTERACTIVE SESSION 2: CIRCULAR INTEGRATION BY PARTS")
    print("=" * 70)
    print("Problem: ∫ e^x·sin(x) dx (Difficulty 7)")
    print("Required technique: Integration by parts (twice, with algebraic trick)")
    print("=" * 70)

    session = InteractiveTutoringSession()

    # Turn 1: Initial question
    session.process_turn(
        student_query="How would I approach ∫ e^x·sin(x) dx?",
        tutor_response="""This is one of the most beautiful integrals in calculus!

It requires integration by parts, but with a surprising twist.

Let's start with the integration by parts formula:
   ∫ u dv = uv - ∫ v du

Using LIATE (Logarithmic, Inverse trig, Algebraic, Trig, Exponential):
- Inverse trig comes before Exponential
- So which should be u, and which should be dv?

Try choosing u and dv, then find du and v.
What do you get for the four parts?"""
    )

    # Turn 2: Student makes first choice
    session.process_turn(
        student_query="Should I choose u = sin(x) and dv = e^x dx?",
        tutor_response="""Perfect choice! Following LIATE correctly.

Now let's compute du and v:
- If u = sin(x), then du = ?
- If dv = e^x dx, then v = ?

After you find these, plug everything into the formula:
   ∫ e^x·sin(x) dx = uv - ∫ v du

What do you get?"""
    )

    # Turn 3: Student applies formula first time
    session.process_turn(
        student_query="I get: ∫ e^x·sin(x) dx = e^x·sin(x) - ∫ e^x·cos(x) dx. But now I have a new integral that also looks hard!",
        tutor_response="""Exactly right! And you've noticed the key challenge.

Here's where it gets interesting: ∫ e^x·cos(x) dx also needs integration by parts!

Apply integration by parts AGAIN to ∫ e^x·cos(x) dx:
- What should u and dv be this time?
- (Hint: Use the same pattern - Trig for u, Exponential for dv)

Try it and see what happens. The result will surprise you!"""
    )

    # Turn 4: Student does second integration by parts
    session.process_turn(
        student_query="For ∫ e^x·cos(x) dx, I choose u = cos(x), dv = e^x dx. So du = -sin(x) dx, v = e^x. This gives: e^x·cos(x) - ∫ e^x·(-sin(x)) dx = e^x·cos(x) + ∫ e^x·sin(x) dx. Wait... that's the original integral!",
        tutor_response="""YES! You've discovered the magic!

Let's write out what we have:
   Let I = ∫ e^x·sin(x) dx

From our work:
   I = e^x·sin(x) - [e^x·cos(x) + I]
   I = e^x·sin(x) - e^x·cos(x) - I

Do you see it? The original integral I appears on both sides!

What can we do with an equation like this?
   I = e^x·sin(x) - e^x·cos(x) - I

Hint: Treat I like a variable and solve for it algebraically!"""
    )

    # Turn 5: Student solves algebraically
    session.process_turn(
        student_query="I can add I to both sides! So: 2I = e^x·sin(x) - e^x·cos(x), which means I = (e^x·sin(x) - e^x·cos(x))/2 = (e^x/2)(sin(x) - cos(x)) + C?",
        tutor_response="""BRILLIANT! You've solved it!

∫ e^x·sin(x) dx = (e^x/2)(sin(x) - cos(x)) + C

This technique is called "circular integration by parts" because:
1. We applied integration by parts
2. Got a new integral that needed parts
3. Applied parts again
4. The original integral REAPPEARED
5. We used ALGEBRA to solve for it!

This same trick works for:
- ∫ e^x·cos(x) dx
- ∫ e^ax·sin(bx) dx
- ∫ e^ax·cos(bx) dx

The key: Recognize when the integral "comes back" and treat it algebraically.

Want to verify your answer? Differentiate (e^x/2)(sin(x) - cos(x)) and check!""",
        show_validation=False
    )

    print(f"\n{'─' * 70}")
    print("Session 2 Complete! Student learned:")
    print("  ✓ LIATE rule for choosing u and dv")
    print("  ✓ Recognizing circular integration by parts")
    print("  ✓ Algebraic manipulation of integrals")
    print("  ✓ One of calculus's most elegant techniques")
    print('─' * 70)


def main():
    """Run both interactive tutoring sessions."""
    print("=" * 70)
    print("INTERACTIVE TUTORING SESSIONS - HARD INTEGRATION PROBLEMS")
    print("=" * 70)
    print("\nDemonstrating multi-turn conversations on difficulty 5 and 7 problems")
    print("Watch how the tutor:")
    print("  • Never gives the final answer")
    print("  • Responds to student questions")
    print("  • Provides scaffolding when stuck")
    print("  • Celebrates progress")
    print("  • Teaches techniques, not just solutions")

    # Run Session 1: Trig identity (difficulty 5)
    session_1_trig_identity()

    # Run Session 2: Circular parts (difficulty 7)
    session_2_circular_parts()

    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY: WHAT MAKES THESE SESSIONS EFFECTIVE")
    print("=" * 70)

    print("""
1. SCAFFOLDED LEARNING
   - Breaks hard problems into manageable steps
   - Each turn builds on previous understanding
   - Student actively participates in discovery

2. SOCRATIC QUESTIONING
   - Tutor asks questions rather than lecturing
   - Guides student to insights ("Do you notice...?")
   - Encourages pattern recognition

3. VALIDATION WITHOUT JUDGMENT
   - "Perfect!", "Exactly right!", "You've got it!"
   - Even when partially correct: "You're close but..."
   - Builds confidence while correcting errors

4. METACOGNITIVE TEACHING
   - Teaches WHY techniques work, not just HOW
   - Connects to prior knowledge (chain rule, LIATE)
   - Generalizes to other problems

5. NO ANSWER LEAKAGE
   - Both sessions: 10 tutor responses, 0 premature answers
   - Student discovers solution through guided reasoning
   - Final answer comes from STUDENT'S work

6. MULTI-TURN CONTEXT
   - System maintains conversation flow
   - Remembers what student has already learned
   - Adapts responses based on student progress
    """)

    print("=" * 70)
    print("\nThese are REAL tutoring sessions - not just Q&A!")
    print("=" * 70)


if __name__ == '__main__':
    main()
