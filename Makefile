TEMPLATES = html

TMPL_FILES = $(patsubst %,templates/%.tmpl,$(TEMPLATES))
TMPL_MODS = $(patsubst %,templates/%.py,$(TEMPLATES))

all: $(TMPL_MODS)

templates/%.py: templates/%.tmpl
	cheetah compile $<

