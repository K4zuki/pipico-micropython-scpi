all: html

html:
	cd doc && make html && cd -

pdf:
	cd doc && make pdf && cd -

docx:
	cd doc && make docx && cd -

clean:
	cd doc && make clean && cd -

init:
	cd doc && make init && cd -

initdir:
	cd doc && make initdir && cd -

apidoc: docx

docker:
	docker build -t rpi-pico-build .

firmware:
	cd micropython && \
	docker run --rm -v $(PWD)/micropython:/root rpi-pico-build bash /root/firmware_builder_tmc.sh

firmware-cdc:
	cd micropython && \
	docker run --rm -v $(PWD)/micropython:/root rpi-pico-build bash /root/firmware_builder_cdc.sh
