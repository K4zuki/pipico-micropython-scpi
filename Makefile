ifeq ($(OS),Windows_NT)
HOME = C:/Users/$(USERNAME)
endif
PIPBASE= $(shell get-pip-base)
PANSTYLES= $(PIPBASE)/var
MISC= $(PANSTYLES)/pandoc_misc
MISC_SYS = $(MISC)/system
MISC_USER = $(MISC)/user
include $(MISC_SYS)/Makefile.in
PROJECT= `pwd`

## userland: uncomment and replace
#MDDIR := markdown
#DATADIR := data
#TARGETDIR := Out
#IMAGEDIR := images
#CONFIG := config.yaml
#INPUT := TITLE.md
#DOCXFRONTPAGE := frontpage.md
#TARGET := TARGET-$(DATE)-$(HASH)
#REVERSE_INPUT := reverse-input.docx
#REFERENCE := $(MISC)/ref.docx
##
include $(MISC_SYS)/Makefile
