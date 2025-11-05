#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <fstream>
#include <random>
#include <string>
#include <filesystem>
#include <mutex>
#include <atomic>
#include <memory>

// Global variables for synchronization
std::mutex mtx;
std::atomic<int> shared_counter(0);
std::vector<std::thread> threads;
std::vector<std::unique_ptr<std::ofstream>> open_files;  // Keep files open to show handles
std::mutex file_mutex;

// I/O-intensive task: Read and write files
void io_intensive_task(int thread_id, int duration_seconds) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> size_dist(1024 * 100, 1024 * 1024);  // 100KB to 1MB chunks
    std::uniform_int_distribution<int> char_dist(0, 255);
    
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::seconds(duration_seconds);
    
    int file_counter = 0;
    const std::string base_dir = "perfwatch_test_files";
    std::filesystem::create_directories(base_dir);
    
    std::cout << "Thread " << thread_id << ": Starting I/O operations..." << std::endl;
    
    while (std::chrono::steady_clock::now() < end_time) {
        // Create unique filename
        std::string filename = base_dir + "/test_file_" + std::to_string(thread_id) + 
                               "_" + std::to_string(file_counter) + ".dat";
        
        // Write phase: Write a large chunk of data
        {
            std::ofstream outfile(filename, std::ios::binary);
            if (outfile.is_open()) {
                int chunk_size = size_dist(gen);
                std::vector<char> data(chunk_size);
                
                // Fill with random data
                for (int i = 0; i < chunk_size; i++) {
                    data[i] = static_cast<char>(char_dist(gen));
                }
                
                outfile.write(data.data(), chunk_size);
                outfile.close();
            }
        }
        
        // Read phase: Read the file back
        {
            std::ifstream infile(filename, std::ios::binary);
            if (infile.is_open()) {
                infile.seekg(0, std::ios::end);
                size_t file_size = infile.tellg();
                infile.seekg(0, std::ios::beg);
                
                std::vector<char> buffer(file_size);
                infile.read(buffer.data(), file_size);
                infile.close();
            }
        }
        
        // Keep some files open to show file handle usage
        if (file_counter % 10 == 0) {
            std::lock_guard<std::mutex> lock(file_mutex);
            if (open_files.size() < 20) {  // Keep up to 20 files open
                auto file_ptr = std::make_unique<std::ofstream>(
                    filename, std::ios::app | std::ios::binary);
                if (file_ptr->is_open()) {
                    open_files.push_back(std::move(file_ptr));
                }
            }
        }
        
        // Periodically close some files to show handle changes
        if (file_counter % 25 == 0 && file_counter > 0) {
            std::lock_guard<std::mutex> lock(file_mutex);
            if (!open_files.empty()) {
                open_files.erase(open_files.begin());
            }
        }
        
        file_counter++;
        
        // Small delay to prevent overwhelming the system
        if (file_counter % 5 == 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    
    std::lock_guard<std::mutex> lock(mtx);
    std::cout << "Thread " << thread_id << ": Completed I/O operations. Files processed: " 
              << file_counter << std::endl;
}

// Memory-intensive task that causes page faults
void memory_pagefault_task(int duration_seconds) {
    std::cout << "Starting memory-intensive task to induce page faults..." << std::endl;
    
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::seconds(duration_seconds);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<size_t> index_dist(0, 1000000);
    
    // Allocate a large amount of memory (potentially exceeding physical RAM)
    // This will cause page faults when accessing memory that's swapped to disk
    const size_t large_memory_size = 500 * 1024 * 1024;  // 500 MB
    std::vector<std::vector<int>> memory_chunks;
    
    int cycle = 0;
    while (std::chrono::steady_clock::now() < end_time) {
        // Allocate large chunks
        for (int i = 0; i < 20; i++) {
            std::vector<int> chunk(large_memory_size / sizeof(int) / 20, 0);
            memory_chunks.push_back(std::move(chunk));
        }
        
        // Randomly access memory to cause page faults
        // Accessing memory that's not in physical RAM will trigger page faults
        for (int i = 0; i < 1000; i++) {
            if (!memory_chunks.empty()) {
                size_t chunk_idx = index_dist(gen) % memory_chunks.size();
                size_t elem_idx = index_dist(gen) % memory_chunks[chunk_idx].size();
                memory_chunks[chunk_idx][elem_idx] = i;  // Write to memory
            }
        }
        
        // Periodically deallocate some memory to create memory pressure
        if (cycle % 3 == 0 && memory_chunks.size() > 10) {
            memory_chunks.erase(memory_chunks.begin() + memory_chunks.size() / 2, 
                              memory_chunks.end());
        }
        
        cycle++;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        if (cycle % 10 == 0) {
            size_t total_memory = 0;
            for (const auto& chunk : memory_chunks) {
                total_memory += chunk.size() * sizeof(int);
            }
            std::cout << "Memory cycle " << cycle << ": Using ~" 
                     << (total_memory / 1024 / 1024) << " MB" << std::endl;
        }
    }
    
    std::cout << "Memory-intensive task completed." << std::endl;
}

int main() {
    std::cout << "=== I/O and Resource Test Program ===" << std::endl;
    std::cout << "This program demonstrates:" << std::endl;
    std::cout << "  - File I/O operations (read/write MB and operations)" << std::endl;
    std::cout << "  - Page faults (by allocating large memory)" << std::endl;
    std::cout << "  - Open file handles (by keeping files open)" << std::endl;
    std::cout << std::endl;
    
    const int duration_seconds = 60;
    const int num_io_threads = 4;
    
    std::cout << "Starting " << num_io_threads << " I/O-intensive threads..." << std::endl;
    std::cout << "Program will run for approximately " << duration_seconds << " seconds..." << std::endl;
    std::cout << std::endl;
    
    auto start_time = std::chrono::steady_clock::now();
    
    // Start I/O-intensive threads
    for (int i = 0; i < num_io_threads; i++) {
        threads.emplace_back(io_intensive_task, i, duration_seconds);
    }
    
    // Start memory-intensive task in separate thread
    std::thread memory_thread(memory_pagefault_task, duration_seconds);
    
    // Wait for all threads to complete
    std::cout << "Running for " << duration_seconds << " seconds..." << std::endl;
    for (auto& t : threads) {
        t.join();
    }
    memory_thread.join();
    
    // Close any remaining open files
    {
        std::lock_guard<std::mutex> lock(file_mutex);
        open_files.clear();
    }
    
    auto final_time = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(
        final_time - start_time).count();
    
    std::cout << std::endl;
    std::cout << "=== Program Completed ===" << std::endl;
    std::cout << "Total execution time: " << duration << " seconds" << std::endl;
    
    // Cleanup: Remove test files (optional)
    std::cout << "Cleaning up test files..." << std::endl;
    try {
        std::filesystem::remove_all("perfwatch_test_files");
    } catch (const std::exception& e) {
        std::cout << "Note: Some test files may remain: " << e.what() << std::endl;
    }
    
    // Keep program running a bit longer for final metrics collection
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    return 0;
}

