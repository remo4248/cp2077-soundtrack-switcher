# Run this after adding or removing tracks, then start the game.
#
# For every cue folder holding a replace file, prepare.exe brings the track to the loudness of the
# game's own music and writes replace.prepared.wav next to it. The game then only plays that file:
# nothing is measured, converted or streamed while you play.
#
# It also writes sounds.json (what AudioXL reads) and Cues.reds (the list the in-game script uses).
$root = $PSScriptRoot
$prepare = Join-Path $root 'prepare.exe'
$target = -16          # LUFS: the middle of the game's own music, measured across all 279 cues
$skipped = @()
$prepared = 0

# cues.json is every cue this mod knows. Folder names drop the _START that most event names carry,
# so the folder name is matched back to the real event here - and folders from older versions, which
# still carry _START, keep working.
$cues = @{}
$cuesFile = Join-Path $root 'cues.json'
if (Test-Path $cuesFile) {
    # the value is the spelling the game uses, which is what has to reach sounds.json
    foreach ($c in (Get-Content $cuesFile -Raw | ConvertFrom-Json)) { $cues[$c] = $c }
}

# stops.json lists the game's own events that end each cue, so a replacement can end where the
# original would have instead of running on into the next scene.
$stops = @{}
$stopsFile = Join-Path $root 'stops.json'
if (Test-Path $stopsFile) {
    $parsed = Get-Content $stopsFile -Raw | ConvertFrom-Json
    foreach ($p in $parsed.PSObject.Properties) { $stops[$p.Name] = @($p.Value) }
}

$rows = foreach ($dir in Get-ChildItem -LiteralPath $root -Directory -Recurse -Filter 'mus_*') {
    # Any audio file in the folder is the replacement - nothing has to be renamed. original.* is the
    # game's own music, put there by the previews download, and *.prepared.wav is this script's own
    # output, so neither counts. A name ending in .loop, like "My Song.loop.mp3", repeats until the
    # game moves on to another cue; anything else plays once.
    $found = @(Get-ChildItem -LiteralPath $dir.FullName -File | Where-Object {
        $_.Extension -in '.mp3', '.ogg', '.flac', '.wav' -and
        $_.BaseName -ne 'original' -and $_.BaseName -notlike '*.prepared' } | Sort-Object Name)
    $file = $found | Select-Object -First 1
    if (-not $file) { continue }
    if ($found.Count -gt 1) {
        $ignored = ($found | Select-Object -Skip 1 | ForEach-Object Name) -join ', '
        Write-Host "  $($dir.Name): using $($file.Name), ignoring $ignored" -ForegroundColor Yellow
    }

    # The name is written verbatim into a game script below, and redscript compiles every script mod
    # together - so one malformed name would break the whole script build, not just this mod. Only
    # plain event names get through; anything else is skipped and reported.
    $name = ($dir.Name -split ' ')[0]
    if ($name -cnotmatch '^mus_[A-Za-z0-9_]+$') { $skipped += $dir.Name; continue }
    # PowerShell matches hashtable keys without regard to case, but the game hashes an event name
    # exactly as written - and 14 cues really do end in lowercase _start - so the name written out
    # is always the one from cues.json, never one built by appending here.
    if ($cues.Count) {
        if ($cues.ContainsKey($name)) { $name = $cues[$name] }
        elseif ($cues.ContainsKey($name + '_START')) { $name = $cues[$name + '_START'] }
        else { $skipped += "$($dir.Name) (no such cue)"; continue }
    }

    # Named after the track, so swapping in a different file never leaves the old prepared one
    # behind to be played instead. The leftovers are ours and regenerable, so they go.
    # AudioXL opens its files through narrow-string paths, so the name it is given stays ASCII
    # whatever the track is called.
    $ready = Join-Path $dir.FullName (($file.BaseName -replace '[^A-Za-z0-9 ._-]', '_') + '.prepared.wav')
    Get-ChildItem -LiteralPath $dir.FullName -File -Filter '*.prepared.wav' |
        Where-Object { $_.Name -ne (Split-Path $ready -Leaf) } | Remove-Item -Force
    $stale = (-not (Test-Path -LiteralPath $ready)) -or ((Get-Item -LiteralPath $ready).LastWriteTime -lt $file.LastWriteTime)
    # volume.txt holding e.g. -3 or +2 nudges this one cue, for when the measurement is not what the
    # scene wants by ear.
    $offset = 0
    $tweak = Join-Path $dir.FullName 'volume.txt'
    if (Test-Path -LiteralPath $tweak) {
        $parsedOffset = 0.0
        if ([double]::TryParse((Get-Content -LiteralPath $tweak -Raw).Trim(), [ref]$parsedOffset)) {
            $offset = $parsedOffset
            if ((-not (Test-Path -LiteralPath $ready)) -or ((Get-Item -LiteralPath $tweak).LastWriteTime -gt (Get-Item -LiteralPath $ready).LastWriteTime)) {
                $stale = $true
            }
        }
    }
    if ($stale) {
        if (-not (Test-Path $prepare)) {
            Write-Host "  no prepare.exe, so $($file.Name) is used as it is - add the loudness tool download next to rescan.bat to match levels" -ForegroundColor Yellow
        } else {
            $result = & $prepare $file.FullName $ready --target $target --offset $offset
            Write-Host "  $name  $result"
            $prepared++
        }
    }
    $play = if (Test-Path -LiteralPath $ready) { $ready } else { $file.FullName }

    [ordered]@{ name = $name; type = 'axl_music_2d'; loop = ($file.BaseName -like '*.loop'); fadeOut = 2.0
                stopOn = @($stops[$name] | Where-Object { $_ })   # a cue with no stop event gets none
                file = $play.Substring($root.Length + 1).Replace('\', '/') }
}
$rows = @($rows)
$json = ConvertTo-Json -InputObject ([ordered]@{ sounds = $rows }) -Depth 4
[IO.File]::WriteAllText((Join-Path $root 'sounds.json'), $json, (New-Object Text.UTF8Encoding $false))

# The same list for the script that stops an older cue when a new one starts. Five levels up from
# here is this mod's root: SoundtrackSwitcher\sounds\AudioXL\plugins\red4ext\<mod root>.
$modRoot = (Get-Item $root).Parent.Parent.Parent.Parent.Parent.FullName
$cues = New-Object Text.StringBuilder
[void]$cues.AppendLine('// Written by rescan.bat: the cues that currently have a replacement file.')
[void]$cues.AppendLine('module SoundtrackSwitcher')
[void]$cues.AppendLine('')
[void]$cues.AppendLine('public class SoundtrackSwitcherCues {')
[void]$cues.AppendLine('  public static func List() -> array<CName> {')
[void]$cues.AppendLine('    let cues: array<CName>;')
foreach ($r in $rows) { [void]$cues.AppendLine("    ArrayPush(cues, n`"$($r.name)`");") }
[void]$cues.AppendLine('    return cues;')
[void]$cues.AppendLine('  }')
[void]$cues.AppendLine('}')
$cuesDir = Join-Path $modRoot 'r6\scripts\SoundtrackSwitcher'
if (-not (Test-Path $cuesDir)) { New-Item -ItemType Directory -Force $cuesDir | Out-Null }
[IO.File]::WriteAllText((Join-Path $cuesDir 'Cues.reds'), $cues.ToString(), (New-Object Text.UTF8Encoding $false))

Write-Host ''
foreach ($r in $rows) {
    Write-Host ("  $($r.name)" + $(if ($r.loop) { '  [looping]' }) +
                $(if (-not $r.stopOn.Count) { '  [no stop event: ends only when another cue starts]' }))
}
foreach ($s in $skipped) { Write-Host "  SKIPPED (not a plain cue name): $s" -ForegroundColor Yellow }
Write-Host "$($rows.Count) replacement(s), $prepared prepared this run. Start the game to hear them."
