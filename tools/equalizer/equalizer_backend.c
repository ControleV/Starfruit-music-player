#include <stdint.h>

__declspec(dllexport)
void apply_equalizer(float* samples, int num_samples, float* gains, int num_bands){
    // Apply simple gain in each band (mock)

    for (int i = 0; i < num_samples; ++i) {
        int band = i % num_bands;
        samples[i] *= gains[band];
    }
}
