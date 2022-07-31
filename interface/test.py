"""
The decimal numeral system is composed of ten digits, which we represent as "0123456789" (the digits in a system are written from lowest to highest). Imagine you have discovered an alien BCI, whose data is some number of digits in an alien language, which may or may not be the same as those used in decimal. For example, if the alien numeral system were represented as "oF8", then the numbers one through ten would be (F, 8, Fo, FF, F8, 8o, 8F, 88, Foo, FoF). We would like to be able to work with numbers in arbitrary alien systems. More generally, we want to be able to convert an arbitrary number that’s written in one alien system into a second alien system.

The first line of input gives the number of cases, T is less than or equal to 100. T test cases follow. Each case is a line formatted as

alien_number source_language target_language
Each language will be represented by a list of its digits, ordered from lowest to highest value. No digit will be repeated in any representation, all digits in the alien number will be present in the source language, and the first digit of the alien number will not be the lowest valued digit of the source language (in other words, the alien numbers have no leading zeroes). Each digit will either be a number 0-9, an uppercase or lowercase letter, or one of the following symbols !"#$%&'()*+,-./:;<>?@[\]^_`{|}~

You may assume that the number in decimal is positive and at most 1000000000. All languages will have at most 94 digits.

"""

def alien_number(alien_number, source_language, target_language):
    """
    Convert alien number to decimal
    """
    # Convert alien number to decimal
    decimal_number = 0
    for digit in alien_number:
        if digit in source_language:
            decimal_number = decimal_number * len(source_language) + source_language.index(digit)
        else:
            return "ERROR"
    # Convert decimal number to target language
    target_number = ""
    while decimal_number > 0:
        target_number = target_language[decimal_number % len(target_language)] + target_number
        decimal_number = decimal_number // len(target_language)
    return target_number

print(alien_number("CODE", "O!CDE?", "A?JM!."))