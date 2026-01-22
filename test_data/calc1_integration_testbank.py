#!/usr/bin/env python3
"""
Comprehensive Calculus 1 Integration Test Bank
Real problems at varying difficulty levels (not just x^2!)

Based on typical university Calc 1 courses covering:
- Basic antiderivatives
- Substitution (u-sub)
- Integration by parts
- Trig integrals
- Partial fractions (intro level)
- Applications (area, volume)

Difficulty scale: 1 (basic) to 8 (challenging for Calc 1)
"""

CALC1_INTEGRATION_PROBLEMS = {
    'basic_power_rule': [
        # Difficulty 1-2: Direct power rule application
        ("Integrate x^5", "x^6/6 + C", 1),
        ("Find ∫ (3x^2 - 2x + 5) dx", "x^3 - x^2 + 5x + C", 2),
        ("∫ √x dx", "(2/3)x^(3/2) + C", 2),
        ("∫ 1/x^3 dx", "-1/(2x^2) + C", 2),
        ("∫ (x^2 + 1)^2 dx", "(x^5/5) + (2x^3/3) + x + C", 3),  # Need to expand first
        ("∫ (2x - 1)(x + 3) dx", "(2x^3/3) + (5x^2/2) - 3x + C", 3),
    ],

    'basic_trig_exponential': [
        # Difficulty 2: Memorized formulas
        ("∫ cos(x) dx", "sin(x) + C", 2),
        ("∫ sec^2(x) dx", "tan(x) + C", 2),
        ("∫ (sin(x) + cos(x)) dx", "-cos(x) + sin(x) + C", 2),
        ("∫ e^(2x) dx", "(1/2)e^(2x) + C", 2),
        ("∫ 3^x dx", "3^x / ln(3) + C", 3),
        ("∫ csc^2(x) dx", "-cot(x) + C", 2),
        ("∫ sec(x)tan(x) dx", "sec(x) + C", 2),
        ("∫ csc(x)cot(x) dx", "-csc(x) + C", 2),
    ],

    'u_substitution_basic': [
        # Difficulty 3-4: Recognize u-substitution pattern
        ("∫ x·e^(x^2) dx", "(1/2)e^(x^2) + C", 3),
        ("∫ sin(5x) dx", "-(1/5)cos(5x) + C", 3),
        ("∫ (2x + 1)^10 dx", "(1/22)(2x + 1)^11 + C", 3),
        ("∫ x/√(x^2 + 1) dx", "√(x^2 + 1) + C", 3),
        ("∫ cos(x)·sin^3(x) dx", "(1/4)sin^4(x) + C", 4),  # u = sin(x)
        ("∫ e^x/(e^x + 1) dx", "ln|e^x + 1| + C", 4),
        ("∫ tan(x) dx", "-ln|cos(x)| + C", 4),  # u = cos(x)
        ("∫ x^2·√(x^3 + 1) dx", "(2/9)(x^3 + 1)^(3/2) + C", 4),
        ("∫ sin(x)/cos^2(x) dx", "sec(x) + C", 4),  # u = cos(x)
        ("∫ ln(x)/x dx", "(1/2)(ln(x))^2 + C", 4),  # u = ln(x)
    ],

    'u_substitution_harder': [
        # Difficulty 4-5: Less obvious substitutions
        ("∫ x·√(2x + 1) dx", "(1/15)(2x + 1)^(3/2)(3x - 1) + C", 5),  # Requires algebra after u-sub
        ("∫ e^(√x)/√x dx", "2e^(√x) + C", 5),  # u = √x
        ("∫ sin(√x)/√x dx", "-2cos(√x) + C", 5),
        ("∫ (ln(x))^2/x dx", "(1/3)(ln(x))^3 + C", 4),
        ("∫ x/(x^2 + 4) dx", "(1/2)ln|x^2 + 4| + C", 4),  # Recognize derivative in numerator
        ("∫ x^3/(x^2 + 1) dx", "(1/2)(x^2 - ln|x^2 + 1|) + C", 5),  # Poly division first
    ],

    'trig_integrals': [
        # Difficulty 4-6: Require trig identities
        ("∫ sin^2(x) dx", "x/2 - sin(2x)/4 + C", 5),  # Need: sin^2 = (1-cos(2x))/2
        ("∫ cos^2(x) dx", "x/2 + sin(2x)/4 + C", 5),  # Need: cos^2 = (1+cos(2x))/2
        ("∫ sin(x)cos(x) dx", "(1/2)sin^2(x) + C", 4),  # Or -(1/2)cos^2(x) + C
        ("∫ sin^3(x) dx", "-(1/3)cos^3(x) + cos(x) + C", 5),  # sin^2 = 1 - cos^2
        ("∫ cos^4(x) dx", "(3x/8) + (sin(2x)/4) + (sin(4x)/32) + C", 6),  # Repeated reduction
        ("∫ tan^2(x) dx", "tan(x) - x + C", 5),  # tan^2 = sec^2 - 1
        ("∫ sec^3(x) dx", "(1/2)(sec(x)tan(x) + ln|sec(x) + tan(x)|) + C", 7),  # Tricky!
    ],

    'integration_by_parts': [
        # Difficulty 5-6: IBP (LIATE rule)
        ("∫ x·e^x dx", "x·e^x - e^x + C", 5),
        ("∫ x·sin(x) dx", "-x·cos(x) + sin(x) + C", 5),
        ("∫ ln(x) dx", "x·ln(x) - x + C", 5),
        ("∫ x^2·e^x dx", "x^2·e^x - 2x·e^x + 2e^x + C", 6),  # Repeated parts
        ("∫ e^x·sin(x) dx", "(e^x/2)(sin(x) - cos(x)) + C", 7),  # Circular, very tricky
        ("∫ x·ln(x) dx", "(x^2/2)ln(x) - x^2/4 + C", 6),
        ("∫ arctan(x) dx", "x·arctan(x) - (1/2)ln(1 + x^2) + C", 6),
        ("∫ x·sec^2(x) dx", "x·tan(x) + ln|cos(x)| + C", 6),
    ],

    'partial_fractions_intro': [
        # Difficulty 6-7: Basic partial fractions (Calc 1 level)
        ("∫ 1/(x^2 - 1) dx", "(1/2)ln|(x-1)/(x+1)| + C", 6),  # A/(x-1) + B/(x+1)
        ("∫ 1/(x(x + 1)) dx", "ln|x/(x+1)| + C", 6),
        ("∫ (2x + 3)/(x^2 + 3x + 2) dx", "ln|(x+1)^2/(x+2)| + C", 7),
        ("∫ 1/(x^2 + 2x + 1) dx", "-1/(x+1) + C", 5),  # Perfect square (x+1)^2
        ("∫ x/(x^2 + x - 2) dx", "(1/3)ln|x+2| + (2/3)ln|x-1| + C", 6),
    ],

    'definite_integrals': [
        # Difficulty varies: Computation + FTC
        ("∫[0 to 1] x^2 dx", "1/3", 2),
        ("∫[0 to π/2] sin(x) dx", "1", 3),
        ("∫[1 to e] (1/x) dx", "1", 3),  # ln(e) - ln(1) = 1
        ("∫[-1 to 1] x^3 dx", "0", 3),  # Odd function
        ("∫[0 to 1] e^x dx", "e - 1", 3),
        ("∫[0 to π] cos(x) dx", "0", 3),
        ("∫[0 to 4] √x dx", "16/3", 3),
    ],

    'area_applications': [
        # Difficulty 5-6: Set up integral for area
        ("Area between y = x^2 and y = x from 0 to 1", "1/6", 5),
        ("Area under y = sin(x) from 0 to π", "2", 4),
        ("Area enclosed by y = x^2 and y = 4", "32/3", 5),
    ],

    'challenging_calc1': [
        # Difficulty 7-8: Hardest problems in typical Calc 1
        ("∫ 1/(1 + x^2) dx", "arctan(x) + C", 4),  # Memorize or derive
        ("∫ 1/√(1 - x^2) dx", "arcsin(x) + C", 4),
        ("∫ x^3·e^(x^2) dx", "(1/2)(x^2 - 1)e^(x^2) + C", 7),  # Parts + substitution
        ("∫ (sin(x))/(1 + cos(x)) dx", "-ln|1 + cos(x)| + C", 5),  # u = 1 + cos(x)
        ("∫ √(1 + x^2) dx", "(x/2)√(1 + x^2) + (1/2)ln|x + √(1 + x^2)| + C", 8),  # Trig sub
        ("∫ x·arctan(x) dx", "(x^2 + 1)arctan(x)/2 - x/2 + C", 7),  # Parts
        ("∫ sec(x) dx", "ln|sec(x) + tan(x)| + C", 6),  # Clever trick
    ],

    'word_problems': [
        # Application problems requiring integration
        ("Velocity is v(t) = 3t^2 - 2t. Find position s(t) if s(0) = 5", "s(t) = t^3 - t^2 + 5", 4),
        ("Acceleration a(t) = sin(t). Find velocity if v(0) = 0", "v(t) = 1 - cos(t)", 4),
        ("Rate of water flow is r(t) = 100 - 2t L/min. Total water in first 10 min?", "900 L", 4),
    ],

    'conceptual_questions': [
        # Understanding, not just computation
        ("If f'(x) = 2x and f(0) = 3, find f(x)", "f(x) = x^2 + 3", 3),
        ("What is the derivative of ∫[a to x] f(t) dt?", "f(x)", 4),  # FTC Part 1
        ("Evaluate ∫[a to b] f'(x) dx", "f(b) - f(a)", 4),  # FTC Part 2
    ],

    'common_student_errors': [
        # Problems designed to catch mistakes
        ("∫ 1/x dx", "ln|x| + C", 2),  # NOT x^0/0 !
        ("∫ sin(2x) dx", "-(1/2)cos(2x) + C", 3),  # NOT -cos(2x) (forget chain rule)
        ("∫ (x + 1)^2 dx", "x^3/3 + x^2 + x + C", 3),  # Must expand first
        ("∫ e^(3x) dx", "(1/3)e^(3x) + C", 3),  # NOT e^(3x)/3x
        ("∫ sec^2(2x) dx", "(1/2)tan(2x) + C", 3),  # Don't forget 1/2
    ],
}

def get_all_problems():
    """Flatten all problems into single list."""
    all_problems = []
    for category, problems in CALC1_INTEGRATION_PROBLEMS.items():
        for problem, answer, difficulty in problems:
            all_problems.append({
                'problem': problem,
                'answer': answer,
                'difficulty': difficulty,
                'category': category,
            })
    return all_problems

def get_problems_by_difficulty(min_diff=1, max_diff=8):
    """Get problems within difficulty range."""
    all_problems = get_all_problems()
    return [p for p in all_problems if min_diff <= p['difficulty'] <= max_diff]

def print_test_bank_stats():
    """Print statistics about the test bank."""
    all_problems = get_all_problems()

    print("=" * 70)
    print("CALC 1 INTEGRATION TEST BANK - STATISTICS")
    print("=" * 70)
    print(f"\nTotal problems: {len(all_problems)}")

    print(f"\nProblems by category:")
    for category, problems in CALC1_INTEGRATION_PROBLEMS.items():
        print(f"  {category:30s}: {len(problems):3d} problems")

    print(f"\nProblems by difficulty:")
    for diff in range(1, 9):
        count = len([p for p in all_problems if p['difficulty'] == diff])
        print(f"  Level {diff}: {count:3d} problems {'█' * count}")

    # Average difficulty
    avg_diff = sum(p['difficulty'] for p in all_problems) / len(all_problems)
    print(f"\nAverage difficulty: {avg_diff:.2f}")

    print("=" * 70)

if __name__ == '__main__':
    print_test_bank_stats()

    # Show sample problems at each difficulty
    print("\nSAMPLE PROBLEMS BY DIFFICULTY:\n")
    for diff in [1, 3, 5, 7]:
        problems = get_problems_by_difficulty(diff, diff)
        if problems:
            print(f"Difficulty {diff}: {problems[0]['problem']}")
            print(f"  Answer: {problems[0]['answer']}\n")
