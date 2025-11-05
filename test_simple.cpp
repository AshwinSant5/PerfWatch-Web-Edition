#include <iostream>
#include <thread>
#include <chrono>
#include <vector>

// Simple test program - good for quick testing
int main() {
    std::cout << "Simple PerfWatch Test Program" << std::endl;
    std::cout << "This program runs for ~10 seconds with CPU and memory usage." << std::endl;
    std::cout << std::endl;
    
    // Allocate some memory
    std::vector<int> data;
    for (int i = 0; i < 1000000; i++) {
        data.push_back(i);
    }
    std::cout << "Allocated " << (data.size() * sizeof(int) / 1024) << " KB of memory" << std::endl;
    
    // CPU-intensive loop
    std::cout << "Starting CPU-intensive calculations..." << std::endl;
    double sum = 0.0;
    for (int i = 0; i < 100000000; i++) {
        sum += std::sin(i) * std::cos(i);
        
        // Print progress every 10 million iterations
        if (i % 10000000 == 0) {
            std::cout << "Progress: " << (i / 1000000) << " million iterations" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    
    std::cout << "Calculation complete. Sum: " << sum << std::endl;
    std::cout << "Program finished." << std::endl;
    
    return 0;
}

