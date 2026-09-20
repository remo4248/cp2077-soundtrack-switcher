// SoundtrackSwitcher: keeps two replaced music cues from playing over each other.
//
// AudioXL swaps a cue's music for the player's own file, but nothing stops the previous cue's file
// when the next one starts, so they overlap. This plugin watches the cues listed in AudioXL's
// manifest and, whenever more than one is playing, stops all but the one that started last.
//
// It hooks nothing. Everything here goes through AudioXL's own script API (Position / Stop), which
// reports on a row whoever started it - so the cue can be started by the quest, by an audio scene,
// or by anything else, and this still sees it.
#include <windows.h>

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#define RED4EXT_HEADER_ONLY
#include <RED4ext/RED4ext.hpp>

namespace
{
constexpr double kPollSeconds = 0.25;   // how often the playing cues are checked

std::filesystem::path g_dir;            // red4ext\plugins\SoundtrackSwitcher
std::vector<RED4ext::CName> g_cues;     // the cues the player replaced
bool g_running = false;
double g_nextPoll = 0.0;
uint64_t g_polls = 0;

void Log(const std::string& aLine)
{
    std::ofstream out(g_dir / "SoundtrackSwitcher.log", std::ios::app);
    out << aLine << '\n';
}

double Now()
{
    return static_cast<double>(GetTickCount64()) / 1000.0;
}

// Every "name": "..." in AudioXL's manifest for our mod. Crude on purpose: the file is written by
// our own rescan script, and pulling in a JSON parser for one field is not worth it.
void LoadManifest()
{
    const auto path = g_dir.parent_path() / "AudioXL" / "sounds" / "SoundtrackSwitcher" / "sounds.json";
    std::ifstream in(path);
    std::string text((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    for (size_t at = text.find("\"name\""); at != std::string::npos; at = text.find("\"name\"", at + 1))
    {
        const size_t colon = text.find(':', at);
        if (colon == std::string::npos) break;
        const size_t open = text.find('"', colon);
        if (open == std::string::npos) break;
        const size_t close = text.find('"', open + 1);
        if (close == std::string::npos) break;
        g_cues.push_back(RED4ext::CName(text.substr(open + 1, close - open - 1).c_str()));
    }
    Log("manifest " + path.string() + ": " + std::to_string(g_cues.size()) + " replaced cue(s)");
}

// AudioXL's natives are static functions on a native class, which neither the instance nor the
// global lookup finds.
RED4ext::CClassStaticFunction* AudioXLFunc(const char* aName)
{
    auto* cls = RED4ext::CRTTISystem::Get()->GetClass("AudioXLNative");
    if (!cls) return nullptr;
    for (auto* candidate : cls->staticFuncs)
    {
        if (candidate->shortName == RED4ext::CName(aName)) return candidate;
    }
    return nullptr;
}

// A static function has no instance. Passing a plain nullptr picks the CClass* overload instead,
// which looks up a game system for a null type and crashes, so the instance is spelled out here.
bool CallStatic(RED4ext::CClassStaticFunction* aFunc, void* aOut, RED4ext::StackArgs_t& aArgs)
{
    void* noInstance = nullptr;
    return aFunc && RED4ext::ExecuteFunction(noInstance, aFunc, aOut, aArgs);
}

float Position(RED4ext::CName aCue)   // seconds into the row, 0 when it is not playing
{
    static auto* func = AudioXLFunc("Position");
    float seconds = 0.0f;
    RED4ext::StackArgs_t args;
    args.emplace_back(nullptr, &aCue);
    CallStatic(func, &seconds, args);
    return seconds;
}

void Stop(RED4ext::CName aCue)
{
    static auto* func = AudioXLFunc("Stop");
    bool stopped = false;
    float fadeOut = 0.0f;
    RED4ext::StackArgs_t args;
    args.emplace_back(nullptr, &aCue);
    args.emplace_back(nullptr, &fadeOut);
    CallStatic(func, &stopped, args);
}

// The cue that started last is the one with the least time played.
void KeepNewestOnly()
{
    RED4ext::CName newest;
    float newestPos = 0.0f;
    std::vector<std::pair<RED4ext::CName, float>> playing;
    for (RED4ext::CName cue : g_cues)
    {
        const float pos = Position(cue);
        if (pos <= 0.0f) continue;
        playing.emplace_back(cue, pos);
        if (!newest || pos < newestPos)
        {
            newest = cue;
            newestPos = pos;
        }
    }
    if (playing.size() < 2) return;

    for (const auto& [cue, pos] : playing)
    {
        if (cue == newest) continue;
        Stop(cue);
        char buf[64];
        std::snprintf(buf, sizeof(buf), " (%.1fs in)", pos);
        Log("stopped " + std::string(cue.ToString()) + buf + ", newest is " + newest.ToString());
    }
}

// How long a poll actually costs, so the poll rate can be judged on numbers rather than guesswork.
double g_worstPollMs = 0.0;
double g_nextReport = 0.0;

bool OnRunningUpdate(RED4ext::CGameApplication*)
{
    if (g_running && !g_cues.empty() && Now() >= g_nextPoll)
    {
        g_nextPoll = Now() + kPollSeconds;
        if (++g_polls == 1) Log("first poll");

        LARGE_INTEGER freq{}, start{}, end{};
        QueryPerformanceFrequency(&freq);
        QueryPerformanceCounter(&start);
        KeepNewestOnly();
        QueryPerformanceCounter(&end);

        const double ms = 1000.0 * static_cast<double>(end.QuadPart - start.QuadPart) / freq.QuadPart;
        g_worstPollMs = ms > g_worstPollMs ? ms : g_worstPollMs;
        if (Now() >= g_nextReport)
        {
            if (g_nextReport > 0.0)
            {
                char buf[128];
                std::snprintf(buf, sizeof(buf), "worst poll %.3f ms for %zu cue(s)", g_worstPollMs, g_cues.size());
                Log(buf);
            }
            g_nextReport = Now() + 30.0;
            g_worstPollMs = 0.0;
        }
    }
    return true;
}

bool OnRunningEnter(RED4ext::CGameApplication*)
{
    if (!g_cues.empty() && !AudioXLFunc("Position"))
    {
        g_cues.clear();   // no AudioXL, nothing to watch
        Log("AudioXLNative.Position not found; not watching for overlaps");
    }
    g_running = true;
    g_polls = 0;
    Log("session started, watching " + std::to_string(g_cues.size()) + " cue(s)");
    return true;
}

bool OnRunningExit(RED4ext::CGameApplication*)
{
    g_running = false;
    Log("session ended after " + std::to_string(g_polls) + " poll(s)");
    return true;
}
} // namespace

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle aHandle, RED4ext::v1::EMainReason aReason,
                                        const RED4ext::v1::Sdk* aSdk)
{
    if (aReason == RED4ext::v1::EMainReason::Load)
    {
        wchar_t path[MAX_PATH]{};
        GetModuleFileNameW(reinterpret_cast<HMODULE>(aHandle), path, MAX_PATH);
        g_dir = std::filesystem::path(path).parent_path();
        std::filesystem::remove(g_dir / "SoundtrackSwitcher.log");
        Log("loading");

        LoadManifest();
        RED4ext::v1::GameState running{&OnRunningEnter, &OnRunningUpdate, &OnRunningExit};
        aSdk->gameStates->Add(aHandle, RED4ext::EGameStateType::Running, &running);
    }
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* aInfo)
{
    aInfo->name = L"SoundtrackSwitcher";
    aInfo->author = L"omermusamanci";
    aInfo->version = RED4EXT_V1_SEMVER(0, 2, 0);
    aInfo->runtime = RED4EXT_V1_RUNTIME_VERSION_INDEPENDENT;
    aInfo->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
