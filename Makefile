all: html

html:
	cd doc && make html && cd -

pdf:
	cd doc && make pdf && cd -

docx:
	cd doc && make docx && cd -

clean:
	cd doc && make clean && cd -
	cd micropython/doc && make clean

init:
	cd doc && make init && cd -
	cd micropython/doc && make init

initdir:
	cd doc && make initdir && cd -
	cd micropython/doc && make initdir

apidoc: apidoc-docx

apidoc-html:
	cd micropython/doc && make html && cd -

apidoc-pdf:
	cd micropython/doc && make pdf && cd -

apidoc-docx:
	cd micropython/doc && make docx && cd -
