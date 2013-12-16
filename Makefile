all: tests

.PHONY: tests

tests:
	nosetests tests
