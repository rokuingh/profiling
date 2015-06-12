clean:
	rm -rf ESMPy* performance_testing.out

dust:
	rm -rf ESMPy*

run:
	./benchmark
	sed -i "s/REGRIDMETHOD=0/REGRIDMETHOD=1/" runESMPyRegrid
	./benchmark
	sed -i "s/REGRIDMETHOD=1/REGRIDMETHOD=2/" runESMPyRegrid
	./benchmark

