cmake_language(DEFER CALL target_sources MonteCarloMultiGPU PRIVATE "/tmp/m5-0cbd0788-708b-4a08-9878-b4e271633874/out/profile/timing.o")
cmake_language(DEFER CALL target_link_libraries MonteCarloMultiGPU PRIVATE pthread)
cmake_language(DEFER CALL target_link_options MonteCarloMultiGPU PRIVATE  -Wl,--wrap=cudaLaunchKernel -Wl,--wrap=cudaMemcpyAsync -Wl,--wrap=cudaMemcpy -Wl,--wrap=cudaMalloc -Wl,--wrap=cudaFree -Wl,--wrap=cudaDeviceReset)
