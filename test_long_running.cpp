#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <cmath>

int main() {
    std::cout << "=== Long-Running Performance Test ===" << std::endl;
    std::cout << "This program will run for 60 seconds..." << std::endl;
    std::cout << "Watch the metrics update in real-time!" << std::endl;
    std::cout << std::endl;
    
    // Allocate some memory
    std::vector<std::vector<double>> memory_chunks;
    const int chunk_size = 50000; // 50k doubles per chunk
    
    std::cout << "Allocating memory..." << std::endl;
    for (int i = 0; i < 20; i++) {
        std::vector<double> chunk(chunk_size, 1.0);
        memory_chunks.push_back(chunk);
    }
    std::cout << "Memory allocated: ~" << (memory_chunks.size() * chunk_size * sizeof(double) / 1024 / 1024) << " MB" << std::endl;
    std::cout << std::endl;
    
    // CPU-intensive task
    std::cout << "Starting CPU-intensive calculations..." << std::endl;
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::seconds(60);
    
    int iteration = 0;
    while (std::chrono::steady_clock::now() < end_time) {
        // Perform intensive calculations
        double sum = 0.0;
        for (int i = 0; i < 1000000; i++) {
            double x = i * 0.0001;
            sum += std::sin(x) * std::cos(x) + std::sqrt(x);
        }
        
        // Modify memory
        if (iteration % 10 == 0) {
            for (auto& chunk : memory_chunks) {
                for (size_t j = 0; j < chunk.size(); j += 1000) {
                    chunk[j] = std::sin(j);
                }
            }
        }
        
        iteration++;
        
        // Print progress every 5 seconds
        auto current_time = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time).count();
        if (iteration % 20 == 0) {
            std::cout << "Progress: " << elapsed << " seconds elapsed, iteration: " << iteration << std::endl;
        }
        
        // Small sleep to prevent CPU from maxing out completely
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    
    auto final_time = std::chrono::steady_clock::now();
    auto total_elapsed = std::chrono::duration_cast<std::chrono::seconds>(final_time - start_time).count();
    
    std::cout << std::endl;
    std::cout << "=== Program Completed ===" << std::endl;
    std::cout << "Total time: " << total_elapsed << " seconds" << std::endl;
    std::cout << "Total iterations: " << iteration << std::endl;
    std::cout << "Press Enter to exit..." << std::endl;
    
    // Keep program running a bit longer
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    return 0;
}

