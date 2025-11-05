#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <random>
#include <mutex>
#include <atomic>
#include <cmath>

// Global variables for synchronization
std::mutex mtx;
std::atomic<int> shared_counter(0);
std::vector<std::thread> threads;

// CPU-intensive computation
void cpu_intensive_task(int thread_id, int iterations) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<double> dis(0.0, 1.0);
    
    double sum = 0.0;
    for (int i = 0; i < iterations; i++) {
        // Perform some mathematical calculations
        double x = dis(gen);
        double y = dis(gen);
        sum += std::sin(x) * std::cos(y) + std::sqrt(x * y);
        
        // Occasionally sleep to create context switches
        if (i % 1000 == 0) {
            std::this_thread::sleep_for(std::chrono::microseconds(100));
            
            // Use mutex to create contention and context switches
            std::lock_guard<std::mutex> lock(mtx);
            shared_counter++;
            
            if (thread_id == 0 && i % 10000 == 0) {
                std::cout << "Thread " << thread_id << ": Iteration " << i 
                         << ", Shared counter: " << shared_counter.load() << std::endl;
            }
        }
    }
    
    std::lock_guard<std::mutex> lock(mtx);
    std::cout << "Thread " << thread_id << " completed. Final sum: " << sum << std::endl;
}

// Memory-intensive task
void memory_intensive_task() {
    std::vector<std::vector<double>> memory_chunks;
    const int chunk_size = 100000; // 100k doubles = ~800KB per chunk
    
    std::cout << "Starting memory-intensive operations..." << std::endl;
    
    // Allocate and deallocate memory in cycles
    for (int cycle = 0; cycle < 10; cycle++) {
        // Allocate memory
        for (int i = 0; i < 50; i++) {
            std::vector<double> chunk(chunk_size, 1.0);
            memory_chunks.push_back(chunk);
        }
        
        std::cout << "Cycle " << cycle << ": Allocated " << memory_chunks.size() 
                 << " chunks (~" << (memory_chunks.size() * chunk_size * sizeof(double) / 1024 / 1024) 
                 << " MB)" << std::endl;
        
        // Modify memory to ensure it's actually used
        for (auto& chunk : memory_chunks) {
            for (size_t i = 0; i < chunk.size(); i += 1000) {
                chunk[i] = std::sin(i);
            }
        }
        
        // Sleep to allow metrics collection
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        
        // Deallocate some memory
        if (cycle % 2 == 1) {
            memory_chunks.erase(memory_chunks.begin() + memory_chunks.size() / 2, 
                               memory_chunks.end());
            std::cout << "Freed some memory. Remaining chunks: " << memory_chunks.size() << std::endl;
        }
    }
    
    std::cout << "Memory-intensive task completed." << std::endl;
}

int main() {
    std::cout << "=== PerfWatch Test Program ===" << std::endl;
    std::cout << "This program demonstrates:" << std::endl;
    std::cout << "  - CPU usage (intensive calculations)" << std::endl;
    std::cout << "  - Memory allocation/deallocation" << std::endl;
    std::cout << "  - Multiple threads (context switches)" << std::endl;
    std::cout << "  - Thread synchronization (mutex contention)" << std::endl;
    std::cout << std::endl;
    
    const int num_threads = 4;
    
    std::cout << "Starting " << num_threads << " CPU-intensive threads..." << std::endl;
    std::cout << "Program will run for approximately 60 seconds..." << std::endl;
    std::cout << std::endl;
    
    auto start_time = std::chrono::steady_clock::now();
    auto target_duration = std::chrono::seconds(60);
    auto end_time = start_time + target_duration;
    
    // Start CPU-intensive threads with continuous work
    for (int i = 0; i < num_threads; i++) {
        threads.emplace_back([i, end_time]() {
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_real_distribution<double> dis(0.0, 1.0);
            
            double sum = 0.0;
            int iteration = 0;
            
            while (std::chrono::steady_clock::now() < end_time) {
                // Perform intensive calculations
                double x = dis(gen);
                double y = dis(gen);
                sum += std::sin(x) * std::cos(y) + std::sqrt(x * y);
                
                iteration++;
                
                // Occasionally sleep to create context switches
                if (iteration % 1000 == 0) {
                    std::this_thread::sleep_for(std::chrono::microseconds(100));
                    
                    // Use mutex to create contention
                    std::lock_guard<std::mutex> lock(mtx);
                    shared_counter++;
                }
            }
            
            std::lock_guard<std::mutex> lock(mtx);
            std::cout << "Thread " << i << " completed. Iterations: " << iteration << ", Sum: " << sum << std::endl;
        });
    }
    
    // Start memory-intensive task in separate thread
    std::thread memory_thread([end_time]() {
        std::vector<std::vector<double>> memory_chunks;
        const int chunk_size = 100000;
        
        std::cout << "Starting memory-intensive operations..." << std::endl;
        
        int cycle = 0;
        while (std::chrono::steady_clock::now() < end_time) {
            // Allocate memory
            for (int i = 0; i < 20; i++) {
                std::vector<double> chunk(chunk_size, 1.0);
                memory_chunks.push_back(chunk);
            }
            
            // Modify memory
            for (auto& chunk : memory_chunks) {
                for (size_t i = 0; i < chunk.size(); i += 1000) {
                    chunk[i] = std::sin(i);
                }
            }
            
            std::cout << "Cycle " << cycle << ": Using ~" 
                     << (memory_chunks.size() * chunk_size * sizeof(double) / 1024 / 1024) 
                     << " MB" << std::endl;
            
            // Deallocate some memory every other cycle
            if (cycle % 2 == 1 && memory_chunks.size() > 10) {
                memory_chunks.erase(memory_chunks.begin() + memory_chunks.size() / 2, 
                                   memory_chunks.end());
            }
            
            cycle++;
            std::this_thread::sleep_for(std::chrono::milliseconds(2000));
        }
        
        std::cout << "Memory-intensive task completed." << std::endl;
    });
    
    // Wait for all threads to complete
    std::cout << "Running for 60 seconds..." << std::endl;
    for (auto& t : threads) {
        t.join();
    }
    memory_thread.join();
    
    auto final_time = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(
        final_time - start_time).count();
    
    std::cout << std::endl;
    std::cout << "=== Program Completed ===" << std::endl;
    std::cout << "Total execution time: " << duration << " seconds" << std::endl;
    std::cout << "Final shared counter value: " << shared_counter.load() << std::endl;
    
    // Keep program running a bit longer for final metrics collection
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    return 0;
}

