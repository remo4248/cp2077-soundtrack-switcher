// prepare.exe - brings a replacement track to the loudness of the game's own music, before the game
// ever runs. rescan.bat calls it once per file; the game then just plays the result.
//
//   prepare.exe <input.mp3|ogg|flac|wav> <output.wav> [--target -16] [--peak -1] [--offset 0]
//
// Decodes the file, measures its integrated loudness (EBU R128, the two-pass perceptual measure),
// applies the gain that brings it to the target, and runs a lookahead limiter so a boosted track
// cannot clip. Writes 16-bit PCM WAV, which is what AudioXL memory-maps - no streaming, no work at
// load. Decoding is dr_libs and stb_vorbis, loudness is libebur128; none of it is hand-rolled.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#define DR_WAV_IMPLEMENTATION
#define DR_MP3_IMPLEMENTATION
#define DR_FLAC_IMPLEMENTATION
#include "dr_flac.h"
#include "dr_mp3.h"
#include "dr_wav.h"

#define STB_VORBIS_HEADER_ONLY
#include "stb_vorbis.c"
#undef STB_VORBIS_HEADER_ONLY

extern "C" {
#include "ebur128.h"
}

namespace {

struct Audio {
    std::vector<float> samples;   // interleaved
    unsigned channels = 0;
    unsigned rate = 0;
    size_t frames() const { return channels ? samples.size() / channels : 0; }
};

std::string Extension(const std::string& aPath) {
    const size_t dot = aPath.find_last_of('.');
    std::string ext = dot == std::string::npos ? "" : aPath.substr(dot);
    for (char& c : ext) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return ext;
}

bool Decode(const std::string& aPath, Audio& aOut, std::string& aWhy) {
    const std::string ext = Extension(aPath);
    if (ext == ".wav") {
        unsigned channels = 0, rate = 0;
        drwav_uint64 frames = 0;
        float* pcm = drwav_open_file_and_read_pcm_frames_f32(aPath.c_str(), &channels, &rate, &frames, nullptr);
        if (!pcm) { aWhy = "cannot decode WAV"; return false; }
        aOut.samples.assign(pcm, pcm + frames * channels);
        aOut.channels = channels;
        aOut.rate = rate;
        drwav_free(pcm, nullptr);
    } else if (ext == ".mp3") {
        drmp3_config cfg{};
        drmp3_uint64 frames = 0;
        float* pcm = drmp3_open_file_and_read_pcm_frames_f32(aPath.c_str(), &cfg, &frames, nullptr);
        if (!pcm) { aWhy = "cannot decode MP3"; return false; }
        aOut.samples.assign(pcm, pcm + frames * cfg.channels);
        aOut.channels = cfg.channels;
        aOut.rate = cfg.sampleRate;
        drmp3_free(pcm, nullptr);
    } else if (ext == ".flac") {
        unsigned channels = 0, rate = 0;
        drflac_uint64 frames = 0;
        float* pcm = drflac_open_file_and_read_pcm_frames_f32(aPath.c_str(), &channels, &rate, &frames, nullptr);
        if (!pcm) { aWhy = "cannot decode FLAC"; return false; }
        aOut.samples.assign(pcm, pcm + frames * channels);
        aOut.channels = channels;
        aOut.rate = rate;
        drflac_free(pcm, nullptr);
    } else if (ext == ".ogg") {
        int channels = 0, rate = 0;
        short* pcm = nullptr;
        const int frames = stb_vorbis_decode_filename(aPath.c_str(), &channels, &rate, &pcm);
        if (frames <= 0 || !pcm) { aWhy = "cannot decode OGG"; return false; }
        aOut.samples.resize(static_cast<size_t>(frames) * channels);
        for (size_t i = 0; i < aOut.samples.size(); ++i) aOut.samples[i] = pcm[i] / 32768.0f;
        aOut.channels = static_cast<unsigned>(channels);
        aOut.rate = static_cast<unsigned>(rate);
        free(pcm);
    } else {
        aWhy = "unsupported file type '" + ext + "' (wav, mp3, ogg, flac)";
        return false;
    }
    if (aOut.channels == 0 || aOut.rate == 0 || aOut.frames() == 0) { aWhy = "no audio in the file"; return false; }
    return true;
}

// Integrated loudness in LUFS, or 1.0 when it cannot be measured (silence, or too short to gate).
double Loudness(const Audio& aAudio) {
    ebur128_state* state = ebur128_init(aAudio.channels, aAudio.rate, EBUR128_MODE_I);
    if (!state) return 1.0;
    double lufs = 1.0;
    if (ebur128_add_frames_float(state, aAudio.samples.data(), aAudio.frames()) == EBUR128_SUCCESS) {
        if (ebur128_loudness_global(state, &lufs) != EBUR128_SUCCESS) lufs = 1.0;
    }
    ebur128_destroy(&state);
    return lufs;
}

// Lookahead limiter: holds the signal back before a peak arrives rather than clipping it, so a
// track that needed a big boost still sounds like itself.
void Limit(Audio& aAudio, float aCeiling) {
    const size_t lookahead = std::max<size_t>(1, aAudio.rate / 200);         // 5 ms
    const float release = 1.0f / static_cast<float>(std::max<size_t>(1, aAudio.rate / 20));   // 50 ms
    const size_t frames = aAudio.frames();
    const unsigned ch = aAudio.channels;

    std::vector<float> needed(frames, 1.0f);
    for (size_t f = 0; f < frames; ++f) {
        float peak = 0.0f;
        for (unsigned c = 0; c < ch; ++c) peak = std::max(peak, std::fabs(aAudio.samples[f * ch + c]));
        if (peak > aCeiling) needed[f] = aCeiling / peak;
    }
    // Pull each reduction back over the lookahead window so it arrives before the peak does.
    std::vector<float> target(frames, 1.0f);
    for (size_t f = 0; f < frames; ++f) {
        if (needed[f] >= 1.0f) continue;
        const size_t from = f > lookahead ? f - lookahead : 0;
        for (size_t k = from; k <= f; ++k) target[k] = std::min(target[k], needed[f]);
    }
    float gain = 1.0f;
    for (size_t f = 0; f < frames; ++f) {
        gain = target[f] < gain ? target[f] : std::min(1.0f, gain + release);
        for (unsigned c = 0; c < ch; ++c) {
            float& s = aAudio.samples[f * ch + c];
            s = std::clamp(s * gain, -1.0f, 1.0f);
        }
    }
}

bool WriteWav(const std::string& aPath, const Audio& aAudio, std::string& aWhy) {
    drwav_data_format fmt{};
    fmt.container = drwav_container_riff;
    fmt.format = DR_WAVE_FORMAT_PCM;
    fmt.channels = aAudio.channels;
    fmt.sampleRate = aAudio.rate;
    fmt.bitsPerSample = 16;
    drwav wav;
    if (!drwav_init_file_write(&wav, aPath.c_str(), &fmt, nullptr)) { aWhy = "cannot write " + aPath; return false; }
    std::vector<drwav_int16> pcm(aAudio.samples.size());
    for (size_t i = 0; i < pcm.size(); ++i) {
        const float s = std::clamp(aAudio.samples[i], -1.0f, 1.0f);
        pcm[i] = static_cast<drwav_int16>(std::lround(s * 32767.0f));
    }
    const drwav_uint64 written = drwav_write_pcm_frames(&wav, aAudio.frames(), pcm.data());
    drwav_uninit(&wav);
    if (written != aAudio.frames()) { aWhy = "short write to " + aPath; return false; }
    return true;
}

double Option(int argc, char** argv, const char* aName, double aFallback) {
    for (int i = 1; i + 1 < argc; ++i) {
        if (std::strcmp(argv[i], aName) == 0) return std::atof(argv[i + 1]);
    }
    return aFallback;
}

}   // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::printf("usage: prepare <input> <output.wav> [--target -16] [--peak -1] [--offset 0]\n");
        return 2;
    }
    const std::string in = argv[1], out = argv[2];
    const double target = Option(argc, argv, "--target", -16.0) + Option(argc, argv, "--offset", 0.0);
    const double ceilingDb = Option(argc, argv, "--peak", -1.0);

    Audio audio;
    std::string why;
    if (!Decode(in, audio, why)) {
        std::printf("FAILED %s: %s\n", in.c_str(), why.c_str());
        return 1;
    }
    const double measured = Loudness(audio);
    double gainDb = 0.0;
    if (measured < 0.0) {
        gainDb = std::clamp(target - measured, -30.0, 30.0);
        const float gain = static_cast<float>(std::pow(10.0, gainDb / 20.0));
        for (float& s : audio.samples) s *= gain;
    }
    Limit(audio, static_cast<float>(std::pow(10.0, ceilingDb / 20.0)));
    if (!WriteWav(out, audio, why)) {
        std::printf("FAILED %s: %s\n", in.c_str(), why.c_str());
        return 1;
    }
    if (measured < 0.0) {
        std::printf("%.1f LUFS -> %.1f, %+.1f dB\n", measured, target, gainDb);
    } else {
        std::printf("too quiet to measure, left as it is\n");
    }
    return 0;
}
