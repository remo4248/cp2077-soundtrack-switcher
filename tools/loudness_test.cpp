// Runs Loudness::MeanDbfs over real files, outside the game, so the measurement can be checked
// without a launch. Build: see loudness_test.bat. Usage: loudness_test.exe <file.wav> [...]
#include <cstdio>
#include <vector>

#include "Loudness.hpp"

int main(int argc, char** argv) {
    for (int i = 1; i < argc; ++i) {
        FILE* f = std::fopen(argv[i], "rb");
        if (!f) {
            std::printf("cannot open %s\n", argv[i]);
            continue;
        }
        std::fseek(f, 0, SEEK_END);
        const long size = std::ftell(f);
        std::fseek(f, 0, SEEK_SET);
        std::vector<unsigned char> data(static_cast<size_t>(size));
        const size_t read = std::fread(data.data(), 1, data.size(), f);
        std::fclose(f);

        const float db = AudioXLNS::Loudness::MeanDbfs(data.data(), read);
        std::printf("%10zu bytes  %8.1f dBFS   %s\n", read, db, argv[i]);
        if (db < 0.0f) {
            std::printf("            gain to -13.4: %.2f   to -8.6: %.2f\n",
                        AudioXLNS::Loudness::GainFor(-13.4f, db), AudioXLNS::Loudness::GainFor(-8.6f, db));
        }
    }
    return 0;
}
