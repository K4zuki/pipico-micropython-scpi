all: html

html:
	cd docs && make html

pdf:
	cd docs && make pdf

docx:
	cd docs && make docx

clean:
	cd docs && make clean

init:
	cd docs && make init

initdir:
	cd docs && make initdir
