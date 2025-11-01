#!/usr/bin/env python3
"""Generate 1000+ test statements from base templates."""
import csv
import random

# Load existing 150 statements as templates
templates = []
with open('test_statements.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    templates = list(reader)

print(f"Loaded {len(templates)} template statements")

# Statement variations to multiply test cases
variations = {
    "TRUE": [
        ("", ""),  # Original
        ("Is it true that ", "?"),
        ("Can you confirm that ", "?"),
        ("I heard that ", ". Is this accurate?"),
    ],
    "FALSE": [
        ("", ""),
        ("Is it false that ", "?"),
        ("Someone told me ", ". Is this true?"),
        ("I read that ", ". Can you verify?"),
    ],
    "UNVERIFIED": [
        ("", ""),
        ("What do you think about the claim that ", "?"),
        ("Is there evidence that ", "?"),
    ]
}

# Additional factual statements
additional_statements = [
    ("The Eiffel Tower is in Paris", "TRUE", "Factual_Easy", "Easy", "Well-known landmark location"),
    ("Tokyo is the capital of Japan", "TRUE", "Factual_Easy", "Easy", "Current capital"),
    ("The Atlantic Ocean is larger than the Pacific", "FALSE", "Factual_Easy", "Easy", "Pacific is largest"),
    ("Humans have 206 bones", "TRUE", "Factual_Easy", "Easy", "Human anatomy"),
    ("The Sun revolves around the Earth", "FALSE", "Factual_Easy", "Easy", "Heliocentric model"),
    ("Oxygen is necessary for human life", "TRUE", "Factual_Easy", "Easy", "Basic biology"),
    ("Deserts receive abundant rainfall", "FALSE", "Factual_Easy", "Easy", "Definition of desert"),
    ("The speed of sound is faster than light", "FALSE", "Factual_Easy", "Easy", "Physics constants"),
    ("Brazil is in South America", "TRUE", "Factual_Easy", "Easy", "Geography"),
    ("Penguins can fly", "FALSE", "Factual_Easy", "Easy", "Flightless birds"),
    ("The Sahara is a desert", "TRUE", "Factual_Easy", "Easy", "Largest hot desert"),
    ("Fish can breathe underwater", "TRUE", "Factual_Easy", "Easy", "Aquatic respiration"),
    ("The moon produces its own light", "FALSE", "Factual_Easy", "Easy", "Reflects sunlight"),
    ("Elephants are mammals", "TRUE", "Factual_Easy", "Easy", "Animal classification"),
    ("Lightning is hotter than the sun's surface", "TRUE", "Scientific", "Medium", "Temperature comparison"),
    ("The human brain stops developing at age 18", "FALSE", "Scientific", "Medium", "Neuroscience shows continued development"),
    ("All bacteria are harmful", "FALSE", "Scientific", "Medium", "Many beneficial bacteria exist"),
    ("Photosynthesis requires sunlight", "TRUE", "Scientific", "Medium", "Plant biology"),
    ("Atoms are mostly empty space", "TRUE", "Scientific", "Medium", "Atomic structure"),
    ("Glass is a liquid at room temperature", "FALSE", "Myths", "Medium", "Common misconception"),
]

generated = []
test_id = 1

# Generate variations of existing templates
for template in templates:
    expected = template['expected_verdict']
    if expected in variations:
        for prefix, suffix in variations[expected][:2]:  # Use first 2 variations
            generated.append({
                'test_id': str(test_id),
                'category': template['category'],
                'difficulty': template['difficulty'],
                'statement': f"{prefix}{template['statement']}{suffix}",
                'expected_verdict': template['expected_verdict'],
                'reasoning': template['reasoning']
            })
            test_id += 1
            
            if len(generated) >= 1000:
                break
    
    if len(generated) >= 1000:
        break

# Add additional statements to fill gaps
for stmt, verdict, category, difficulty, reasoning in additional_statements:
    if len(generated) >= 1000:
        break
    for prefix, suffix in variations.get(verdict, [("", "")])[:3]:
        generated.append({
            'test_id': str(test_id),
            'category': category,
            'difficulty': difficulty,
            'statement': f"{prefix}{stmt}{suffix}",
            'expected_verdict': verdict,
            'reasoning': reasoning
        })
        test_id += 1
        if len(generated) >= 1000:
            break

# Save to new file
output_file = 'test_statements_1000.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['test_id', 'category', 'difficulty', 'statement', 'expected_verdict', 'reasoning']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(generated[:1000])

print(f"✅ Generated {len(generated[:1000])} test statements")
print(f"✅ Saved to {output_file}")
