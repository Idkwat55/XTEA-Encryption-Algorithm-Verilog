 :v.PHONY: clean default run crun

default:
	@echo "No Target specificed"

clean: 
	rm ./binexec

compile: c_model.c 
	gcc -o binexec $^

run: binexec 
	./binexec

crun: compile run
