"""Render REAL excerpts from SenulMapa/hermes-native (verbatim lines, trimmed) as images for the reel.
No fake UI: each card is text copied from the repo file named in its filename."""
import os
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(D, "..", "..", "fonts")
f = ImageFont.truetype(os.path.join(F, "jetbrains-mono-latin-400-normal.woff"), 30)
fb = ImageFont.truetype(os.path.join(F, "jetbrains-mono-latin-600-normal.woff"), 30)
BG, FG, MUT, ACC = (12, 15, 18), (225, 228, 232), (110, 122, 128), (124, 119, 255)
CARDS = {
 "build.yml.png": [("# .github/workflows/build.yml", "c"), ("jobs:", ""), ("  build:", ""), ("    runs-on: macos-15", "h"), ("", ""),
   ("  - run: xcodegen generate", ""), ("  - run: ci/run-tests.sh", ""), ("  - run: |", ""), ("      xcodebuild archive \\", "h"),
   ("        -scheme HermesNative \\", ""), ("        -destination \\", ""), ("          'generic/platform=iOS' \\", ""),
   ("        CODE_SIGNING_ALLOWED=NO", "h"), ("", ""), ("  - uses: action-gh-release", ""), ("      files: HermesNative.ipa", "h")],
 "make-ipa.sh.png": [("# ci/make-ipa.sh", "c"), ("# AltStore re-signs on device", "c"), ("# with the user's free Apple ID,", "c"),
   ("# so we ship unsigned.", "c"), ("", ""), ("mkdir -p \"$WORK/Payload\"", ""), ("cp -R \"$APP\" \"$WORK/Payload/\"", ""), ("", ""),
   ("# Strip any signature so the", "c"), ("# artifact is unambiguously", "c"), ("# unsigned.", "c"),
   ("rm -rf \"$WORK/Payload/\"*.app/\\", "h"), ("  _CodeSignature", "h"), ("", ""), ("zip -qry HermesNative.ipa \\", ""), ("  Payload", "")],
 "project.yml.png": [("# project.yml", "c"), ("# XcodeGen spec: generates the", "c"), ("# .xcodeproj on the macOS CI", "c"),
   ("# runner. Authored on Linux;", "c"), ("# never hand-edit a pbxproj.", "c"), ("", ""), ("name: HermesNative", "h"), ("deploymentTarget:", ""),
   ("  iOS: \"26.0\"", "h"), ("packages:", ""), ("  HermesGlass:", ""), ("  HermesAPI:", ""), ("  HermesTerminal:", ""), ("", ""),
   ("CODE_SIGNING_ALLOWED: \"NO\"", "h")],
 "HostKeyValidator.swift.png": [("// Trust-on-first-use host-key", "c"), ("// pinning. Never blindly", "c"), ("// accepts a changed key.", "c"), ("", ""),
   ("let fingerprint = Data(", ""), ("  SHA256.hash(data: Data(", ""), ("    openSSHString.utf8)))", ""), ("", ""),
   ("if let known = HostKeyStore", ""), ("    .fingerprint(for: host) {", ""), ("  if known == fingerprint {", ""),
   ("    promise.succeed(())", ""), ("  } else {", ""), ("    promise.fail(", "h"), ("      HostKeyMismatch(host))", "h"), ("  }", "")],
 "source.json.png": [("// source.json  (AltStore feed)", "c"), ("{", ""), ("  \"name\": \"Hermes\",", "h"), ("  \"developerName\":", ""),
   ("      \"Senul Mapa\",", ""), ("  \"versions\": [{", ""), ("    \"version\": \"0.1.23\",", "h"), ("    \"downloadURL\":", ""),
   ("      \".../v0.1.23/", ""), ("        HermesNative.ipa\",", "h"), ("    \"minOSVersion\": \"26.0\"", ""), ("  }]", ""), ("}", ""), ("", ""),
   ("// every push to main = a new", "c"), ("// in-app update via AltStore", "c")],
}
for name, lines in CARDS.items():
    im = Image.new("RGB", (860, 1200), BG); d = ImageDraw.Draw(im); y = 60
    for txt, kind in lines:
        if kind == "h": d.rectangle((36, y - 6, 44, y + 36), fill=ACC)
        d.text((64, y), txt, font=fb if kind == "h" else f, fill=MUT if kind == "c" else (ACC if kind == "h" else FG)); y += 66
    im.save(os.path.join(D, name)); print(name)
