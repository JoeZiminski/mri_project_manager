# Python can be written in the IDE and run using the green button in the top right of the PyCharm IDE, with the output
# visable in the 'Run' section found at the bottom of the PyCharm IDE. Alternatively, code can be  dynamically executed
# in the Python Console found at the button of the PyCharm IDE. To run this code in the Python Console, you can copy
# it in

# METHODS
# In python 'functions' are also called 'methods'. These are the same thing. They take an input and return
# an output. In python methods are initialised by writing 'def', followed by the function name, and then
# function inputs within brackets. Below the function is called 'add_one' and it takes the input called 'number'.

# Methods are the building blocks of code and should be kept as small as possible with their functionality well defined,
# with a descriptive name.
# Note that python variable passing is a little confusing at first, and if a variable is 'mutable' it will be edited in
# place when passed to a function. Discussion of this is beyond the scope of this introductory guide but see
# https://realpython.com/python-pass-by-reference/ for more detail

def add_one(number):     # define the function name and argument
    number += 1          # manipulate the input
    return number        # return the mainpulated input


# CLASSES
# A class is an object that brings together groups of variables and methods. In the example below, the class is called
# MyFirstClass. The keyword 'self' is used for the class to referer to itself and contain its variables and methods.
# The class below has a variable attached called 'Number'. There is also the method 'add_one' exactly as above. This
# will add 1 to any number passed to it, but apart from that will not act on any of the classes variables. As such
# it is a 'static method'. however, it is still stored on the class.

# Finally the method 'add_one_to_class_number' is a method that is attached to the class and acts on class variables.
# Calling this method will add one to the class variable, as seen in the example below.

class MyFirstClass:
    def __init__(self):    # Python syntax to initialise the class and define the 'self' keyword. This method is also called the class 'construtor' as it will initalise all class attributes

        self.number = 1    # class variable called 'number', initialised with the value 1

    @staticmethod          # This 'add_one' method exactly as above. This will not change any class variable if called
    def add_one(number):   # However his method is attached to the class (see example use below)
        number += 1
        return number

    def add_one_to_class_number(self):  # This method is both attached to the class an will edit the class variable. The keyword
        self.number += 1                # 'self' is passed to give access to the method to all class attributes (e.g. self.number)
                                        # No argument needs to be passed, as it acts on the class variable through the 'self' keyword

# Example Use
my_first_class = MyFirstClass()         # This call with the brackets initialises the class calling the class constructer
print(my_first_class.add_one(5))        # This will print 6, adding 1 to 5. The method is attached to the class and is accessed through the dot notiation . but does not change any class attributes
print(my_first_class.number)            # Print the number attribute of the class. This was initialised as 1 so will print one
my_first_class.add_one_to_class_number()  # This method updates the class attribute, adding 1 to it. We do not see any output as nothing is printed but the change occurs behind the scene
print(my_first_class.number)              # Now print the class attriut again - it will print 2, as the function call add_one_to_class_number() added 1 to the class attribute 'number'

# CLASS INHERETENCE
# Classes are extremely versitile and to save code, one class can 'inheret' it's attributes and methods from another class.
# here, MySecondClass inherts all methods from MyFirstClass. You will see in the example section that we can call methods
# associated with MyFirstClass through MySecondClass even though these methods are not explicitly defined in MySecondClass.

class MySecondClass(MyFirstClass):    # define the class, putting the class to inheret from in the brackets.
    def __init__(self):               # call the class construter as above
        super(MySecondClass, self)    # initialise the class super, pythons syntax for making the class inheret from it's parents class
                                      # If you wanted to call the super-classes construter as well, the syntax is super(MySecondClass, self).__init__()
        self.number = 5               # here we override the super class self.number = 1 with the value 5


my_second_class = MySecondClass()     # initialise the second class
print(my_second_class.number)         # this will print 5, as we initialised the class above with number = 5
my_second_class.add_one_to_class_number()    # even though we did not define this function on MySecondClass, it has been inherented from MyFirstClass
print(my_second_class.number)         # this will print 6, as the function is working on the class attribute number

