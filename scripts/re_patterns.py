import re

# should chinese punctuation be spaced?
punctuation_string = "?!.\u060c\u061F"
quoted_pattern_maybe_space = re.compile(r'\"\s?([^"]*?)\s?\"')
english_regex = re.compile(r"([a-zA-Z\-][a-zA-Z_\-'s\.:]*[_0-9]?||\b[a-z0-9]*\b|\d+|'s)")
english_person_names = re.compile(r"\b(\w+\s\w(?!\s\.))\b")

quoted_pattern_no_space = re.compile(r'\"([^"]*?)\"')
quoted_pattern_with_space = re.compile(r'\"\s([^"]*?)\s\"')
quoted_number_pattern = re.compile(r'\"\s(\d{1,2})\s\"')
duration_date_time_number_pattern = re.compile(r'(DURATION_\d|DATE_\d|TIME_\d|NUMBER_\d)', re.IGNORECASE)
# duration_or_date_pattern_lowercase = re.compile(r'duration_\d|date_\d')
multiple_space_pattern = re.compile(r'\s{2,}')


entity_pattern = re.compile(r'([A-Z][A-Z_]*_[0-9]+|GENERIC_ENTITY_[a-zA-z\.:\d]+)')
id_number_pattern = re.compile(r'([0-9]+)')
number_pattern = re.compile(r'\b([0-9]+)\b')

quoted_pattern_maybe_space_or_number = re.compile(r'\"\s?([^"]*?)\s?\"|(?<!\[\s)([0-9]+)')
