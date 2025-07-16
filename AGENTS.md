# Personality
AI Agents working in this repository should refer to themselves as an agent named 'AutomationX'.

# Project Overview


# Testing Conventions
The 'automojo-testplus' package repository utilizes two different test frameworks for testing 'testbase' and 'testplus'.  The 'testbase' test framework is used for single host testing or tests where only the machine running the tests is required.  For tests that involve more conplex configuration involving multiple networked resources, the 'testplus' framework is used.

Test are organized at the lowest level by resource configuration.  For example, all the single host tests are in the folder 'source/testroots/automojo/tests/singlehost'.  All of the tests that involve a simple cluster of machines would be located in 'source/testroots/automojo/tests/simplecluster'.  Note the directory that changed.

AI based testing does not have access to a simple cluster yet.  To verify code, run only the 'singlehost' tests tests with:

```
    source .venv/bin/activate
    
    testbase --root source/testroots/automojo --includes=automojo.tests.singlehost --output=<desired output folder>
```

When running tests you should create an output folder in order to be able to capture all the test run artifacts in an isolated folder.

# Code Naming Conventions
The code naming conventions of this repository follows the [Automation Mojo Python Naming Conventions](userguide/10-02-naming-conventions.rst)


# Code Structure
The code structure of this repository follows the [Automation Mojo Python Code Structure Standards](userguide/10-01-code-organization.rst)


# Coding Standards
The code in this repository is meant to be utilized by testing tools and test frameworks.  Therefore, the code must prioritize:

*  debuggability over performance
*  readability over conciseness

For all the code in this repository, follow the coding standards specified at [Coding Standards](userguide/10-00-coding-standards.rst)


# Environment Setup
When checking out the code for this repository in order to test changes, agents must:

* run the 'repository-setup/rehome-repository' script.  It creates a needed '.env' file.
* run the 'development/setup-envrionment' script in order to create the virtual environment.

# Project Specific Rules


# Pull Request Guidelines


# Packaging
Currently, this package is utilized using a reference to the github repository.  It is currently not published.
