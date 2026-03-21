#include <algorithm>
#include <chrono>
#include <cuda_runtime.h>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>

__global__ void find_nearest_B(const float3 *__restrict__ A,
                               const float3 *__restrict__ B, int *nearest_idx,
                               int N, int M) {
  int idx = blockDim.x * blockIdx.x + threadIdx.x;
  if (idx >= N)
    return;

  float3 a = A[idx];
  float min_dist = 1e30f;
  int min_j = -1;

  for (int j = 0; j < M; ++j) {
    float dx = a.x - B[j].x;
    float dy = a.y - B[j].y;
    float dz = a.z - B[j].z;
    float dist = dx * dx + dy * dy + dz * dz;

    if (dist < min_dist) {
      min_dist = dist;
      min_j = j;
    }
  }

  nearest_idx[idx] = min_j;
}

std::vector<float3> load_coords_from_file(const std::string &filename) {
  std::vector<float3> coords;
  std::ifstream file(filename);
  if (!file) {
    std::cerr << "Unable to open file: " << filename << std::endl;
    return coords;
  }

  std::string line;
  while (std::getline(file, line)) {
    std::istringstream iss(line);
    float x, y, z;
    if (iss >> x >> y >> z) {
      coords.push_back(make_float3(x, y, z));
    }
  }

  return coords;
}

void save_results_sorted(const std::string &filename,
                         const std::vector<float3> &h_A,
                         const std::vector<float3> &h_B,
                         const std::vector<int> &indices) {
  struct Entry {
    float ax, az;
    float bx, bz;
    float dist;
  };

  std::vector<Entry> entries;

  for (size_t i = 0; i < indices.size(); ++i) {
    float3 a = h_A[i];
    float3 b = h_B[indices[i]];

    float dx = a.x - b.x;
    float dy = a.y - b.y;
    float dz = a.z - b.z;
    float dist = sqrtf(dx * dx + dy * dy + dz * dz);

    entries.push_back({a.x, a.z, b.x, b.z, dist});
  }

  std::sort(entries.begin(), entries.end(),
            [](const Entry &e1, const Entry &e2) { return e1.dist < e2.dist; });

  std::ofstream file(filename);
  for (const auto &e : entries) {
    file << e.ax << " " << e.az << "  " << e.bx << " " << e.bz << "  " << e.dist
         << std::endl;
  }
}

int main() {
  auto t_start = std::chrono::high_resolution_clock::now();

  std::vector<float3> h_A = load_coords_from_file("data/cities.txt");
  std::vector<float3> h_B = load_coords_from_file("data/strongholds.txt");

  int N = h_A.size();
  int M = h_B.size();

  if (N == 0 || M == 0) {
    std::cerr << "Coords empty." << std::endl;
    return 1;
  }

  float3 *d_A;
  float3 *d_B;
  int *d_nearest_idx;
  cudaMalloc(&d_A, sizeof(float3) * N);
  cudaMalloc(&d_B, sizeof(float3) * M);
  cudaMalloc(&d_nearest_idx, sizeof(int) * N);

  cudaMemcpy(d_A, h_A.data(), sizeof(float3) * N, cudaMemcpyHostToDevice);
  cudaMemcpy(d_B, h_B.data(), sizeof(float3) * M, cudaMemcpyHostToDevice);

  int threads = 256;
  int blocks = (N + threads - 1) / threads;

  cudaEvent_t start, stop;
  cudaEventCreate(&start);
  cudaEventCreate(&stop);
  cudaEventRecord(start);

  find_nearest_B<<<blocks, threads>>>(d_A, d_B, d_nearest_idx, N, M);

  cudaEventRecord(stop);
  cudaEventSynchronize(stop);
  float milliseconds = 0;
  cudaEventElapsedTime(&milliseconds, start, stop);
  std::cout << "CUDA kernel time: " << milliseconds << " ms" << std::endl;

  std::vector<int> h_nearest_idx(N);
  cudaMemcpy(h_nearest_idx.data(), d_nearest_idx, sizeof(int) * N,
             cudaMemcpyDeviceToHost);

  save_results_sorted("output.txt", h_A, h_B, h_nearest_idx);

  cudaFree(d_A);
  cudaFree(d_B);
  cudaFree(d_nearest_idx);

  auto t_end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> elapsed = t_end - t_start;
  std::cout << "Total time: " << elapsed.count() * 1000.0 << " ms" << std::endl;

  std::cout << "Saved to output.txt." << std::endl;

  return 0;
}
