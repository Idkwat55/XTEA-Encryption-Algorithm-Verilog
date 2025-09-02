.PHONY: clean default run crun

default:
	@echo "No Target specificed. Choose clean, compile, run or crun for all"

clean: 
	rm ./binexec

compile: c_model.c 
	gcc -o binexec $^

run: binexec 
	./binexec

crun: compile run
