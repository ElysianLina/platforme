#!/usr/bin/env python3
"""
Speaking Exercise Generator for English Learning Platform
Generates unique oral reading prompts for each sub-unit theme.
All sentences are manually crafted to be 100% unique and theme-appropriate.

Usage:
    python generate_speaking_exercises.py

Output:
    - data/speaking/speaking_exercises_a1.json
"""

import json
import random
from pathlib import Path

# A1 Vocabulary organized by category (for reference)
VOCABULARY = {
    "greetings": ["hello", "goodbye", "hi", "bye", "good morning", "good afternoon", "good evening", "good night", "thank you", "thanks", "please", "ok", "yes", "no", "sorry", "welcome"],
    "people": ["man", "woman", "boy", "girl", "friend", "boyfriend", "girlfriend", "person", "people", "adult", "baby", "mr", "mrs", "miss"],
    "numbers": ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred"],
    "family": ["parent", "father", "mother", "dad", "mom", "wife", "husband", "child", "son", "daughter", "sister", "brother", "family", "grandmother", "grandfather", "grandchild", "aunt", "uncle", "niece", "nephew", "cousin"],
    "colors": ["black", "white", "blue", "green", "yellow", "red", "pink", "orange", "purple", "gray", "brown", "dark", "light", "color"],
    "time": ["month", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "season", "spring", "summer", "fall", "winter", "clock", "year", "time", "date", "day", "hour", "minute", "second", "morning", "afternoon", "evening", "night", "week", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "weekend", "next", "half"],
    "personal_info": ["name", "last name", "age", "address", "birthday", "birthdate", "single", "married", "passport", "phone number", "question", "answer"],
    "body": ["body", "hand", "arm", "foot", "head", "leg", "knee", "back", "stomach", "hair", "neck", "face", "eye", "nose", "ear", "cheek", "chin", "mouth", "tooth", "lip"],
    "adjectives": ["good", "bad", "high", "low", "big", "small", "heavy", "expensive", "cheap", "old", "new", "beautiful", "ugly", "clean", "dirty", "easy", "difficult", "fast", "slow", "different", "same", "right", "wrong", "open", "closed", "true", "false", "rich", "poor", "sure", "unsure", "correct", "incorrect"],
    "home": ["building", "house", "home", "apartment", "floor", "door", "window", "wall", "room", "roof", "ceiling", "living room", "dining room", "kitchen", "bedroom", "bathroom", "garden", "upstairs", "downstairs", "closet", "part", "elevator", "yard"],
    "furniture": ["desk", "chair", "table", "sofa", "bed", "cabinet", "fridge", "tv", "stove"],
    "jobs": ["money", "job", "work", "doctor", "dentist", "nurse", "teacher", "engineer", "actor", "actress", "police officer", "waiter", "waitress", "driver"],
    "clothes": ["clothes", "shirt", "pants", "dress", "skirt", "coat", "jacket", "jeans", "sweater", "suit", "tie", "hat", "purse", "shoe", "boot", "sock", "pajamas", "underwear", "swimsuit"],
    "animals": ["animal", "cat", "dog", "horse", "sheep", "cow", "pig", "lion", "rabbit", "mouse", "snake", "fish", "elephant", "bird", "chicken"],
    "verbs": ["be", "wake up", "sleep", "drive", "buy", "sell", "read", "write", "play", "pay", "rest", "wash", "drink", "cook", "eat", "have", "make", "wear", "think", "take", "stand", "speak", "spell", "dislike", "add", "call", "create", "cut"],
    "kitchen_items": ["dish", "spoon", "fork", "knife", "plate", "glass", "bottle", "cup", "soap", "brush", "toothbrush", "pillow", "trash can", "box", "thing", "ball", "doll"],
    "food": ["food", "meat", "vegetable", "cucumber", "potato", "onion", "tomato", "carrot", "pepper", "fruit", "apple", "grape", "banana", "peach", "lemon", "milk", "cheese", "butter", "egg", "cream", "meal", "breakfast", "lunch", "dinner", "tea", "coffee", "cake", "cookie", "bread", "honey", "jam", "juice", "ice cream", "water", "rice", "chocolate milk", "soup", "salad", "pizza", "sandwich", "sugar", "salt"],
    "feelings": ["young", "stupid", "thirsty", "fat", "thin", "tall", "smart", "angry", "fine", "sad", "happy", "hungry", "excited", "ready"],
    "weather": ["weather", "fire", "hot", "cold", "sunny", "cloud", "cloudy", "rain", "rainy", "snowy", "ice", "nature", "sun", "moon", "earth", "sky", "river", "sea", "mountain", "beach", "forest", "island", "star", "tree", "flower"],
    "senses_actions": ["hear", "listen", "see", "look", "watch", "touch", "feel", "talk", "like", "love", "hate", "know", "learn", "ask", "study", "teach", "need", "want", "share", "put", "prepare", "plan", "explain", "fill", "fly", "get", "become"],
    "education": ["school", "college", "university", "preschool", "classroom", "student", "book", "notebook", "bag", "pen", "pencil", "eraser", "marker", "homework", "history", "language", "science", "class"],
    "places": ["city", "town", "street", "bank", "hospital", "restaurant", "movie theater", "supermarket", "post office", "bench", "museum", "park", "hotel", "police", "map"],
    "hobbies": ["hobby", "movie", "music", "guitar", "piano", "violin", "swimming", "soccer", "volleyball", "hiking", "tennis", "bicycle", "sport", "game", "video game", "newspaper", "magazine"],
    "countries": ["country", "united states", "american", "canada", "canadian", "united kingdom", "british", "germany", "german", "france", "french", "spain", "spanish", "italy", "italian"],
    "movement": ["walk", "run", "go", "come", "sit", "jump", "bring", "give", "find", "close", "start", "stop", "finish", "build", "do", "turn", "introduce", "travel", "let", "choose", "help", "swim"],
    "transport": ["car", "motorcycle", "bus", "truck", "train", "taxi", "subway", "helicopter", "ship", "boat", "ticket", "van", "station", "airport", "train station", "place", "north", "south", "east", "west", "left", "far", "continent", "asia", "asian", "europe", "european", "africa", "african", "outside"],
    "adverbs": ["always", "never", "usually", "often", "sometimes", "now", "soon", "too", "here", "there", "again", "of course", "really"],
    "questions": ["why", "where", "when", "what", "who", "how", "else"],
    "prepositions": ["before", "after", "at", "in", "on", "below", "above", "across", "near", "between", "next to", "behind", "with", "to", "another", "this", "that", "both", "over", "under"]
}

# 100% UNIQUE sentences manually crafted for each sub-unit
# Each sentence is thematically appropriate and uses A1 vocabulary
UNIQUE_SENTENCES = {
    # Unit 01: Daily Routines
    "01_A1.1": "Every morning I wake up at seven o'clock and wash my face before breakfast.",
    "01_A1.2": "First I open my eyes and stretch my arms, then I get out of bed slowly.",
    "01_A1.3": "I spend my day at home reading books and watching television with my family.",

    # Unit 02: Family and Relationships
    "02_A1.1": "My family lives in a big house with a beautiful garden near the park.",
    "02_A1.2": "My best friend comes to my house to play games with my sister every weekend.",
    "02_A1.3": "My grandmother and grandfather have three children and five grandchildren in our family.",

    # Unit 03: Travel and Transportation
    "03_A1.1": "The bank is on Main Street next to the post office and the supermarket.",
    "03_A1.2": "I take the bus to the train station and buy a ticket to visit my grandmother.",
    "03_A1.3": "Turn left at the traffic light and walk straight to find the hospital near the park.",
    "03_A1.4": "My father drives his car to work, but I walk to school with my friend.",
    "03_A1.5": "We walk to the market and buy fresh fruit, vegetables, and bread for dinner.",

    # Unit 04: Hobbies and Interests
    "04_A1.1": "In my free time I like to play the guitar and listen to music at home.",
    "04_A1.2": "On Saturday morning I play soccer, and on Sunday I visit my grandmother.",
    "04_A1.3": "I have a red ball, a blue doll, and many games in my toy box.",
    "04_A1.4": "My hobby is hiking in the mountains, and I swim at the beach in summer.",

    # Unit 05: Clothing and Fashion
    "05_A1.1": "I buy a new blue shirt and black pants at the clothing shop near my house.",
    "05_A1.2": "I wear a white shirt, blue jeans, and a red hat when I go to school.",
    "05_A1.3": "The pink dress is beautiful, and the yellow shirt looks good with green pants.",
    "05_A1.4": "I put on my shoes and jacket, then I wash my face before I leave home.",
    "05_A1.5": "In winter I wear a warm coat and boots, but in summer I wear light clothes.",
    "05_A1.6": "This sweater is expensive but beautiful, and these shoes are cheap and comfortable.",

    # Unit 06: Weather and Seasons
    "06_A1.1": "Today is sunny and hot, so I feel happy and want to go outside.",
    "06_A1.2": "In summer it is hot, so I wear light clothes and drink cold water.",
    "06_A1.3": "The sun is bright today, and white clouds are moving across the blue sky.",
    "06_A1.4": "Spring is green with flowers, summer is hot, fall has red leaves, and winter is white.",
    "06_A1.5": "Dark clouds mean rain is coming, and the cold wind blows from the north.",
    "06_A1.6": "Nice weather today, so we can go to the park and play together.",

    # Unit 07: Homes and Rooms
    "07_A1.1": "I live in a house with three bedrooms, two bathrooms, and a big garden.",
    "07_A1.2": "My room has a bed near the window, a desk, and a blue chair.",
    "07_A1.3": "My bed is soft and comfortable, and my clothes are in the closet.",
    "07_A1.4": "I cook food on the stove, and we eat dinner at the table in the kitchen.",

    # Unit 08: Food and Drink
    "08_A1.1": "My favorite food is pizza with cheese, but I also love chocolate cake.",
    "08_A1.2": "I eat eggs, toast with jam, and drink coffee for breakfast every morning.",
    "08_A1.3": "I like sweet food and fruit, but I do not like spicy vegetables.",
    "08_A1.4": "Put bread, cheese, and tomato on a plate, then cut the sandwich in half.",
    "08_A1.5": "I drink water and milk every day, and I eat salad for lunch.",
    "08_A1.6": "For lunch I eat a sandwich, soup, and an apple with my friend at school.",
    "08_A1.7": "First wash the vegetables, then cut the potato and cook the meat in a pan.",

    # Unit 09: Pets and Animals
    "09_A1.1": "The lion is big and strong, and elephants have long noses called trunks.",
    "09_A1.2": "My black cat sleeps on my bed, and I feed my dog every morning.",
    "09_A1.3": "Cows give us milk, sheep have white wool, and chickens lay eggs.",

    # Unit 10: Town and City
    "10_A1.1": "The bank is near the post office, and the hospital is behind the supermarket.",
    "10_A1.2": "The city has tall buildings, museums, hotels, and busy streets with many cars.",
    "10_A1.3": "We play in the park on green grass, and I sit on a bench under the trees.",
    "10_A1.4": "My town is small and quiet, and I know all the people who live here.",
    "10_A1.5": "Many people live and work in the city, and the buildings are very tall.",
    "10_A1.6": "I walk in town, but my mother takes the bus to work every day.",
    "10_A1.7": "Go straight ahead, turn right at the corner, and the shop is on your left.",
    "10_A1.8": "The park is behind the school, between two streets, near the river.",

    # Unit 11: Learning and Skills
    "11_A1": "I can speak English, and I study hard with my kind teacher every day.",

    # Unit 12: Objects and Descriptions
    "12_A1.1": "The ball is round and red, and this box is heavy because it is full.",
    "12_A1.2": "I have a blue bag, a black pen, and a small eraser in my desk.",
    "12_A1.3": "The book is on the table, and the notebook is under the desk near the window.",

    # Unit 13: School Life
    "13_A1.1": "I go to school at eight, class starts at nine, and lunch is at twelve.",
    "13_A1.2": "The board is on the wall, and chairs are near the desks in the classroom.",
    "13_A1.3": "I pack my school bag with books, pens, and my homework every morning.",
    "13_A1.4": "My classroom has twenty students, and the teacher writes on the board.",
    "13_A1.5": "I need a pen, pencil, and eraser for writing in my notebook at school.",

    # Unit 14: Introductions and Greetings
    "14_A1": "What is your name, where do you live, and how old are you this year?",

    # Unit 15: Numbers and Colors
    "15_A1.1": "I count from one to twenty, and my favorite number is fifteen.",
    "15_A1.2": "The sky is blue, grass is green, and the sun is yellow in summer.",
    "15_A1.3": "I have a red car, a blue dress, and yellow bananas in my kitchen.",
    "15_A1.4": "I am ten years old, my brother is seven, and my mother is forty.",
    "15_A1.5": "The apple costs one dollar, and the shirt is twenty dollars at the shop.",
    "15_A1.6": "I see three red cars, two blue pens, and five green apples on the table.",

    # Unit 16: Shopping and Money
    "16_A1.1": "I go shopping on Saturday and buy new clothes at the shop near my house.",
    "16_A1.2": "The supermarket is big, and I buy milk, bread, and fresh vegetables there.",
    "16_A1.3": "I need bread, milk, three apples, and two bottles of juice from the store.",

    # Unit 17: Time and Schedules
    "17_A1": "It is nine o'clock, school starts at eight, and lunch is at twelve every day."
}

# Sub-unit definitions
SUB_UNITS = [
    {"unit": "01", "sub_unit": "A1.1", "theme": "Morning Customs", "categories": ["time", "verbs", "home", "feelings"]},
    {"unit": "01", "sub_unit": "A1.2", "theme": "Wake-up Sequence", "categories": ["verbs", "time", "home", "body"]},
    {"unit": "01", "sub_unit": "A1.3", "theme": "Home Day", "categories": ["home", "furniture", "verbs", "time"]},
    {"unit": "02", "sub_unit": "A1.1", "theme": "My Family", "categories": ["family", "people", "numbers"]},
    {"unit": "02", "sub_unit": "A1.2", "theme": "Friends and Family", "categories": ["family", "people", "feelings"]},
    {"unit": "02", "sub_unit": "A1.3", "theme": "Family Tree", "categories": ["family", "people", "numbers"]},
    {"unit": "03", "sub_unit": "A1.1", "theme": "Town Directions", "categories": ["places", "transport", "prepositions"]},
    {"unit": "03", "sub_unit": "A1.2", "theme": "Travel Plans", "categories": ["transport", "places", "countries"]},
    {"unit": "03", "sub_unit": "A1.3", "theme": "Simple Directions", "categories": ["transport", "places", "prepositions"]},
    {"unit": "03", "sub_unit": "A1.4", "theme": "Daily Transportation", "categories": ["transport", "verbs", "places"]},
    {"unit": "03", "sub_unit": "A1.5", "theme": "Shopping Trip", "categories": ["transport", "places", "food"]},
    {"unit": "04", "sub_unit": "A1.1", "theme": "My Free Time", "categories": ["hobbies", "verbs", "time"]},
    {"unit": "04", "sub_unit": "A1.2", "theme": "What I Do on Weekends", "categories": ["hobbies", "time", "verbs"]},
    {"unit": "04", "sub_unit": "A1.3", "theme": "Toy Selection", "categories": ["kitchen_items", "feelings", "adjectives"]},
    {"unit": "04", "sub_unit": "A1.4", "theme": "My Hobbies on the Weekend", "categories": ["hobbies", "time", "verbs"]},
    {"unit": "05", "sub_unit": "A1.1", "theme": "Clothing Shop", "categories": ["clothes", "colors", "adjectives"]},
    {"unit": "05", "sub_unit": "A1.2", "theme": "My Clothing", "categories": ["clothes", "colors", "adjectives"]},
    {"unit": "05", "sub_unit": "A1.3", "theme": "Colorful Clothing", "categories": ["clothes", "colors", "adjectives"]},
    {"unit": "05", "sub_unit": "A1.4", "theme": "Getting Dressed", "categories": ["clothes", "verbs", "body"]},
    {"unit": "05", "sub_unit": "A1.5", "theme": "Seasonal Clothing", "categories": ["clothes", "weather", "time"]},
    {"unit": "05", "sub_unit": "A1.6", "theme": "Clothing Description", "categories": ["clothes", "colors", "adjectives"]},
    {"unit": "06", "sub_unit": "A1.1", "theme": "Today's Weather", "categories": ["weather", "time", "feelings"]},
    {"unit": "06", "sub_unit": "A1.2", "theme": "Seasonal Wear", "categories": ["weather", "clothes", "time"]},
    {"unit": "06", "sub_unit": "A1.3", "theme": "Climate Details", "categories": ["weather", "adjectives", "time"]},
    {"unit": "06", "sub_unit": "A1.4", "theme": "Seasons", "categories": ["weather", "time", "colors"]},
    {"unit": "06", "sub_unit": "A1.5", "theme": "Atmosphere Kinds", "categories": ["weather", "adjectives"]},
    {"unit": "06", "sub_unit": "A1.6", "theme": "Small Talk Sky", "categories": ["weather", "greetings", "feelings"]},
    {"unit": "07", "sub_unit": "A1.1", "theme": "My Home", "categories": ["home", "furniture", "family"]},
    {"unit": "07", "sub_unit": "A1.2", "theme": "My Room", "categories": ["home", "furniture", "prepositions"]},
    {"unit": "07", "sub_unit": "A1.3", "theme": "My Bedroom Details", "categories": ["home", "furniture", "body"]},
    {"unit": "07", "sub_unit": "A1.4", "theme": "Kitchen", "categories": ["home", "kitchen_items", "food"]},
    {"unit": "08", "sub_unit": "A1.1", "theme": "My Favorite Food", "categories": ["food", "feelings", "verbs"]},
    {"unit": "08", "sub_unit": "A1.2", "theme": "Breakfast Food", "categories": ["food", "time", "kitchen_items"]},
    {"unit": "08", "sub_unit": "A1.3", "theme": "Food Preferences", "categories": ["food", "feelings", "verbs"]},
    {"unit": "08", "sub_unit": "A1.4", "theme": "Making Sandwich", "categories": ["food", "kitchen_items", "verbs"]},
    {"unit": "08", "sub_unit": "A1.5", "theme": "Food and Drink", "categories": ["food", "kitchen_items", "verbs"]},
    {"unit": "08", "sub_unit": "A1.6", "theme": "Lunch Food", "categories": ["food", "time", "kitchen_items"]},
    {"unit": "08", "sub_unit": "A1.7", "theme": "Food Recipe", "categories": ["food", "kitchen_items", "verbs"]},
    {"unit": "09", "sub_unit": "A1.1", "theme": "Zoo Animals", "categories": ["animals", "colors", "adjectives"]},
    {"unit": "09", "sub_unit": "A1.2", "theme": "Pet Companion", "categories": ["animals", "feelings", "family"]},
    {"unit": "09", "sub_unit": "A1.3", "theme": "Animals", "categories": ["animals", "colors", "adjectives"]},
    {"unit": "10", "sub_unit": "A1.1", "theme": "Town Places", "categories": ["places", "transport", "prepositions"]},
    {"unit": "10", "sub_unit": "A1.2", "theme": "City Places", "categories": ["places", "transport", "adjectives"]},
    {"unit": "10", "sub_unit": "A1.3", "theme": "Park Visit", "categories": ["places", "weather", "hobbies"]},
    {"unit": "10", "sub_unit": "A1.4", "theme": "My Town", "categories": ["places", "family", "verbs"]},
    {"unit": "10", "sub_unit": "A1.5", "theme": "My City", "categories": ["places", "adjectives", "transport"]},
    {"unit": "10", "sub_unit": "A1.6", "theme": "Town Transportation", "categories": ["transport", "places", "verbs"]},
    {"unit": "10", "sub_unit": "A1.7", "theme": "Basic Directions", "categories": ["places", "prepositions", "transport"]},
    {"unit": "10", "sub_unit": "A1.8", "theme": "Park Location", "categories": ["places", "prepositions", "weather"]},
    {"unit": "11", "sub_unit": "A1", "theme": "My Skills", "categories": ["education", "verbs", "feelings"]},
    {"unit": "12", "sub_unit": "A1.1", "theme": "Object Description", "categories": ["kitchen_items", "adjectives", "colors"]},
    {"unit": "12", "sub_unit": "A1.2", "theme": "My Things", "categories": ["kitchen_items", "furniture", "adjectives"]},
    {"unit": "12", "sub_unit": "A1.3", "theme": "Book Location", "categories": ["education", "prepositions", "furniture"]},
    {"unit": "13", "sub_unit": "A1.1", "theme": "School Day", "categories": ["education", "time", "verbs"]},
    {"unit": "13", "sub_unit": "A1.2", "theme": "Classroom Objects", "categories": ["education", "furniture", "prepositions"]},
    {"unit": "13", "sub_unit": "A1.3", "theme": "School Bag", "categories": ["education", "kitchen_items", "verbs"]},
    {"unit": "13", "sub_unit": "A1.4", "theme": "My Classroom", "categories": ["education", "furniture", "people"]},
    {"unit": "13", "sub_unit": "A1.5", "theme": "School Objects", "categories": ["education", "adjectives", "prepositions"]},
    {"unit": "14", "sub_unit": "A1", "theme": "Simple Questions", "categories": ["greetings", "personal_info", "questions"]},
    {"unit": "15", "sub_unit": "A1.1", "theme": "Counting Numbers", "categories": ["numbers", "colors"]},
    {"unit": "15", "sub_unit": "A1.2", "theme": "Colors", "categories": ["colors", "adjectives"]},
    {"unit": "15", "sub_unit": "A1.3", "theme": "Colorful Objects", "categories": ["colors", "kitchen_items", "clothes"]},
    {"unit": "15", "sub_unit": "A1.4", "theme": "Numbers and Ages", "categories": ["numbers", "people", "personal_info"]},
    {"unit": "15", "sub_unit": "A1.5", "theme": "Numbers and Prices", "categories": ["numbers", "food", "adjectives"]},
    {"unit": "15", "sub_unit": "A1.6", "theme": "Numbers and Colors", "categories": ["numbers", "colors", "clothes"]},
    {"unit": "16", "sub_unit": "A1.1", "theme": "Going Shopping", "categories": ["places", "clothes", "food"]},
    {"unit": "16", "sub_unit": "A1.2", "theme": "Supermarket", "categories": ["places", "food", "kitchen_items"]},
    {"unit": "16", "sub_unit": "A1.3", "theme": "Shopping List", "categories": ["food", "kitchen_items", "numbers"]},
    {"unit": "17", "sub_unit": "A1", "theme": "Telling Time", "categories": ["time", "numbers", "verbs"]},
]


def generate_exercises():
    """Generate speaking exercises using unique pre-written sentences."""
    exercises = []

    for sub_unit in SUB_UNITS:
        key = f"{sub_unit['unit']}_{sub_unit['sub_unit']}"

        # Get the unique sentence for this sub-unit
        sentence = UNIQUE_SENTENCES.get(key, "I like to learn English every day.")

        exercise = {
            "unit": sub_unit["unit"],
            "sub_unit": sub_unit["sub_unit"],
            "theme": sub_unit["theme"],
            "level": "A1",
            "exercise_type": "speaking_oral_reading",
            "instructions": "Read the following sentence aloud. Practice your pronunciation.",
            "sentence": sentence,
            "vocabulary_categories": sub_unit["categories"]
        }
        exercises.append(exercise)

    return exercises


def main():
    """Main function to generate and save speaking exercises."""
    # Define paths
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "speaking"

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate exercises
    exercises = generate_exercises()

    # Save to JSON file
    output_file = output_dir / "speaking_exercises_a1.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exercises, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(exercises)} speaking exercises.")
    print(f"Output saved to: {output_file}")

    # Print sample of exercises to verify uniqueness
    print("\nSample exercises (showing variety):")
    sample_indices = [0, 5, 10, 15, 20, 30, 40, 50, 60, 68]
    for idx in sample_indices:
        if idx < len(exercises):
            ex = exercises[idx]
            word_count = len(ex['sentence'].split())
            print(f"\n{ex['unit']}-{ex['sub_unit']}: {ex['theme']}")
            print(f"  ({word_count} words): {ex['sentence']}")


if __name__ == "__main__":
    main()