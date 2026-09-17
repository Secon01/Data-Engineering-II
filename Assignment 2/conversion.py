#!/usr/bin/env python3
import time

"""
    The implementation is used to demonstrate an intensive "conversion" function on elements
"""

# Fill in your author information
___author___ = "Sotiris Oikonomou"
___email____ = "sotiris.d.economou@gmail.com"

# Input string to be processed word by word
INPUT_STRING = "I want to be capatilized"

# Number of words to process sequentially; bottleneck when words are in the order of millions
ITERATION = 5

def conversion(substring, operation):
    """A conversion function which takes a string as an input and outputs a converted string

    Args:
        substring (String)
        operation (function): This is an operation on the given input

    Returns:
        [String]: Converted String
    """
    # Apply the provided operation to the substring and return the result
    return function(substring)


def function(string):
    """ A function that performs some operation on a string. You can change the operation accordingly

    Args:
        string (String): input string on which some operation is applied

    Returns:
        [String]: string in upper case
    """
    return string.upper()


if __name__ == "__main__":

    # Guard against ITERATION exceeding the actual word count in the input string
    if ITERATION > len(INPUT_STRING.split()):
        print ("Iteration cannot be greater than the number of words in a string")
        print ("Terminating the benchmark")
        exit()

    print ("Original String: {}".format(INPUT_STRING))
    resultant_string = ""

    # Split the input string into individual words for sequential processing
    split_string = INPUT_STRING.split(" ")

    # Process each word one at a time — sequential bottleneck for large-scale data
    for i in range(0, ITERATION):
        upper_case_string = conversion(split_string[i], function)
        resultant_string += upper_case_string + ' '

    print ("Resultant String: {}".format(resultant_string))
