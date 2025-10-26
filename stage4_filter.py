#!/usr/bin/env python3
"""
Stage 4: Claude Filter - Load pre-filtered articles and filter with Claude.
Allows quick prompt engineering iteration without re-embedding.
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock


async def filter_with_claude(articles, prompt_version="v1"):
    """
    Filter articles using Claude Agent SDK.
    Uses same auth as `claude` CLI binary.
    """
    print(f"\n{'='*80}")
    print(f"STAGE 4: FILTERING WITH CLAUDE")
    print(f"{'='*80}\n")
    print(f"Prompt version: {prompt_version}")
    print(f"Articles to filter: {len(articles)}\n")

    # Prepare articles for Claude
    print(f"⏳ Bereite Artikel für Claude vor...")
    articles_text = []
    for i, article in enumerate(articles, 1):
        pub_str = article.get('published', 'Unbekanntes Datum')
        if pub_str and 'T' in pub_str:
            pub_str = pub_str.split('T')[0]  # Just date part

        articles_text.append(
            f"[{i}] {article['title']}\n"
            f"Quelle: {article['source']} | {pub_str}\n"
            f"Inhalt: {article['content'][:500]}...\n"
            f"Link: {article['link']}\n"
        )

    articles_input = "\n".join(articles_text)

    # Claude TLDR digest prompt
    # TODO: Make this configurable/versioned
    prompt = f"""Du erstellst einen wöchentlichen News-Digest für einen technisch interessierten Leser in Deutschland.

Fasse nur RELEVANTE Artikel zusammen und priorisiere sie in 3 Tiers:

**TIER 1 - MUST-KNOW** (Wichtige Welt- und Deutschland-News):
- Große politische Ereignisse, Kriege, Konflikte
- Wichtige deutsche Nachrichten auf BUNDESEBENE (nicht Parteipolitik!)
- Bedeutende internationale Entwicklungen

Format-Beispiel (ausführlich mit Details):
**[Ereignis in 1-2 Sätzen mit Details]** [Weitere Sätze mit Kontext und Details]. [Ggf. dritter Satz mit Auswirkungen]. *(Relevant weil: Begründung)* → [Link1] | [Link2]

Beispiel:
**Linksgerichtete Catherine Connolly gewinnt Präsidentschaftswahl in Irland mit Erdrutschsieg** Die EU-kritische, unabhängige Abgeordnete erhält 63% der Stimmen und wird 10. Staatsoberhaupt der Republik Irland. Der deutliche Sieg gilt als Dämpfer für die Mitte-Rechts-Regierung und erschüttert das politische Establishment. *(Relevant weil: Politischer Erdrutschsieg in EU-Mitgliedstaat mit Signalwirkung)* → [The Guardian] | [Tagesschau]

**TIER 2 - INTERESSANT** (Tech/KI, EU-Regulierung, Wirtschaft):
- Große Tech/KI-Entwicklungen und bedeutende Software-News
- **Bedeutende Tech-Releases**: Major Versionen wichtiger Frameworks (Next.js 16), neue AI-Modelle (DeepSeek-OCR), wichtige OSS-Projekte (Servo Browser Engine)
- **KI-Research & Entwicklungen**: Neue Modelle, Research-Durchbrüche, AI-Startups (z.B. Sam Altman Brain-Reading), KI-Probleme (Sycophancy, Brain Rot, Parasocial Risks)
- **Autonomous Driving & Mobility**: Waymo, Tesla FSD, autonome Fahrzeuge, wichtige Entwicklungen in Self-Driving
- **Robotics & Space**: Roboter-Entwicklungen, Raumfahrt, Raketentests, SpaceX, NASA, Mars-Missionen, Satelliten
- **EU-Regulierung & Tech-Regulation**: Digitaler Euro, Datenschutz, Chatkontrolle, Tech-Gesetze, Social Media Altersgrenze, Seekabel/Infrastruktur-Abhängigkeit
- **Wichtige Wirtschafts-News**: Rohstoffe (Seltene Erden, Gas-Speicher), Energie (E-Auto-Prämie, Strombörse), große Unternehmens-Entwicklungen (Nexperia-Krise, CEO-Wechsel)
- Größere Infrastruktur-Ausfälle (AWS, etc.)
- Technologische Durchbrüche
- KEINE einzelnen Sicherheitslücken oder Patches
- KEINE kleineren Updates/Bugfixes (Minor/Patch Versions)

Format-Beispiel (wie TIER 1 mit "Relevant weil"):
**[Titel]** - [Zusammenfassung in 2-4 Sätzen mit technischen Details und Kontext]. [Weitere Details zur Bedeutung]. *(Relevant weil: Begründung warum das wichtig/interessant ist)* → [Link]

Beispiel:
**AWS-Ausfall: Einzelner Fehler legte Millionen Services weltweit lahm** - Ein Single Point of Failure führte zu einem 15,5-stündigen AWS-Ausfall Anfang der Woche, der laut DownDetector über 17 Millionen Störungsmeldungen bei 3.500 Organisationen auslöste. Amazon hat nun einen vollständigen Post-Mortem-Bericht veröffentlicht, der zeigt, wie ein einzelner Fehler durch das gesamte Netzwerk kaskadierte. *(Relevant weil: Zeigt Anfälligkeit globaler Cloud-Infrastruktur für Single Points of Failure)* → [Heise]

**TIER 3 - NICE-TO-KNOW** (nach Kategorien):

**Klima & Umwelt:**
- COP-Summits, Klimamigration (z.B. Tuvalu → Australien), Umweltzerstörung
- Artensterben, Nationalparks (z.B. Koala), Korallenbleiche
- Naturkatastrophen mit größeren Auswirkungen
- Wichtige Umweltpolitik-Entwicklungen
- Raumfahrt-Umwelt-Impact (z.B. Starlink-Abstürze)

Format-Beispiel (informativer Einzeiler):
- [Beschreibung mit wichtigsten Details in 1 Satz] → [Link]

Beispiel:
- Starlink-Satelliten: Bereits 1-2 Abstürze pro Tag, bald fünf erwartet – könnte Ozonschicht beeinflussen → [Heise]

**Tech-Releases & Tools:**
- Wichtige neue Software-Versionen und Tools
- Große Consumer-Hardware-Releases (MacBooks, iPhones, große Produktankündigungen)
- Neue Frameworks, Bibliotheken, Open-Source-Projekte
- KEINE Frickel-Hardware (Raspberry Pi, Arduino, E-Reader, Einplatinencomputer)
Format: Einzeiler pro Artikel + Link

**Wissenschaft & Forschung:**
- Nobelpreise, bedeutende wissenschaftliche Durchbrüche
- Interessante Forschungsergebnisse
Format: Einzeiler pro Artikel + Link

**Sonstiges Bemerkenswertes:**
- Kleinere aber interessante Ereignisse die nicht in andere Kategorien passen
Format: Einzeiler pro Artikel + Link

---

## BEISPIELE zur Orientierung:

**✅ TIER 2 - INTERESSANT:**
- "Waymo testet Robotaxis in winterlichen Bedingungen" → Autonomous Driving (Tests SIND relevant!)
- "Is Waymo ready for winter?" → Autonomous Driving (Testphase ist spannend!)
- "Apple KI-Modell erkennt Softwarefehler mit 98% Genauigkeit" → KI-Research
- "LLM Sycophancy Problem quantifiziert" → KI-Research (Research Papers SIND News!)
- "Training mit Junk Data führt zu LLM Brain Rot" → KI-Research (Research Papers SIND News!)
- "Microsoft Mico verstärkt parasocial Risks" → KI-Research (KI-Probleme sind relevant!)
- "EU beschuldigt Meta DSA-Verletzung" → EU-Regulierung (EU vs Big Tech IMMER relevant!)
- "Google verliert Supreme Court Fall zu Play Store Änderungen" → Tech-Regulierung
- "Tesla Mad Max Mode unter Bundesaufsicht" → Tech-Regulierung + Autonomous Driving
- "China verschärft Exportkontrollen für Seltene Erden" → Wirtschaft/Rohstoffe
- "NASA droht SpaceX mit Vertragsentzug wegen Verzögerungen" → Robotics & Space
- "EU-Staaten fordern Mindestalter für Social Media" → EU-Regulierung

**✅ TIER 3 - NICE-TO-KNOW:**
- "Vitest 4.0 mit Visual Regression Testing" → Tech-Releases
- "COP30 Klimagipfel in Brasilien" → Klima & Umwelt
- "Physiknobelpreis für Quantencomputing-Pioniere" → Wissenschaft

**❌ IGNORIEREN:**
- "Adobe Commerce Sicherheitslücke entdeckt" → Security (alle ignorieren)
- "Windows 11 Update behebt Bugs" → Minor Update (alle ignorieren)
- "Raspberry Pi OS wechselt auf Debian" → Frickel-Hardware (ignorieren)
- "Söder warnt vor AfD-Zusammenarbeit" → Parteipolitik (ignorieren)
- "Bayern gewinnt Bundesliga-Spiel" → Sport (ignorieren)

WICHTIG - Was KOMPLETT IGNORIEREN:
- Meinungsartikel, Kommentare, Analysen
- ALLE Sicherheitslücken, Vulnerabilities, Exploits, Patches (egal wie kritisch!)
- Kleinere Software-Updates (Minor/Patch Versions, Bugfixes)
- Framework/Library-Schwachstellen
- **Deutsche PARTEIPOLITIK** (Söder, Merz, CSU, Brantner, Wahlkampf) - ABER: Wirtschafts- und Energiepolitik ist RELEVANT!
- Sehr lokale News (einzelne Städte, Kommunen)
- Promi-News, Sport, Kriminalfälle
- Unwichtige Randthemen

WICHTIG - Was NICHT ignorieren (trotz ähnlicher Namen):
- **ALLE KI/AI-News sind RELEVANT**: Research Papers (Sycophancy, Brain Rot, neue Modelle), AI-Startups, KI-Probleme (parasocial risks), Apple KI-Modell, JEDE neue KI-Entwicklung
- **Autonomous Driving ist IMMER RELEVANT**: Waymo Tests (Winter, neue Märkte), Tesla FSD, Self-Driving Entwicklungen - gerade Testphasen sind spannend!
- **EU vs Big Tech ist IMMER RELEVANT**: Meta DSA-Verletzung, Google Play Store, Apple App Store, JEDE EU-Regulierung gegen Tech-Konzerne
- **Robotics & Space ist RELEVANT**: Roboter-Entwicklungen, Raketentests, SpaceX/NASA Missionen, Mars-Rover, Satelliten-Entwicklungen
- **Tech-Regulierung/große Gerichtsurteile sind RELEVANT**: Google Play Store Supreme Court, Tesla under scrutiny, große Tech-Klagen mit Auswirkungen
- **Deutsche Wirtschafts-/Energiepolitik ist RELEVANT**: E-Auto-Prämie, Gas-Speicher, Strombörse, Unternehmens-Krisen
- **Umwelt-Einzelthemen sind RELEVANT**: Klimamigration, Artensterben, Korallenbleiche, auch ohne Summit

Ausnahmen für INTERESSANT (Security):
- NUR massive Infrastruktur-Ausfälle (AWS, Azure, etc.)
- NUR wenn es AKTIV angegriffen wird UND Millionen betroffen (wie WSUS)

WICHTIG - Duplikate:
- Gleiche Story von verschiedenen Quellen nur 1x nennen
- Nur die Version mit den meisten Details nehmen

WICHTIG - Sprache & Stil:
- Deutsch, aber nutze etablierte Anglizismen wo sie natürlicher klingen
- Beispiele: "Sycophancy" statt "Schmeichelei", "Scraping" statt "Abgreifen"
- Tech-Begriffe: AI/KI ok, Cloud, Framework, Update, Patch etc. bleiben Englisch
- Kein zwanghaftes Eindeutschen von Fachbegriffen

Formatiere als Markdown:

# MUST-KNOW
- **[Ereignis in 1-2 Sätzen]** *(Relevant weil: Begründung)* → [Link]
- **[Ereignis in 1-2 Sätzen]** *(Relevant weil: Begründung)* → [Link]
...

# INTERESSANT

**Titel**: [Absatz mit Details] → [Link]

**Titel**: [Absatz mit Details] → [Link]
...

# NICE-TO-KNOW

## Klima & Umwelt
- [Einzeiler] → [Link]
- [Einzeiler] → [Link]

## Tech-Releases & Tools
- [Einzeiler] → [Link]
- [Einzeiler] → [Link]

## Wissenschaft & Forschung
- [Einzeiler] → [Link]

## Sonstiges
- [Einzeiler] → [Link]

---

# DISCARDED (zum Checken auf False Positives)

Gruppiere verworfene Artikel nach Themen/Grund und erkläre kurz warum:

## [Grund-Kategorie] (z.B. "Deutsche Parteipolitik", "Security/Patches", "Sport", etc.)
**Warum verworfen:** [Kurze Erklärung]
- [Titel 1]
- [Titel 2]
- [Titel 3]

## [Nächste Grund-Kategorie]
**Warum verworfen:** [Kurze Erklärung]
- [Titel]
...

Artikel zum Zusammenfassen:

{articles_input}

Antworte NUR mit Markdown wie oben beschrieben."""

    # Call Claude
    try:
        import time

        print(f"🔌 Verbinde zu Claude...")
        start = time.time()

        client = ClaudeSDKClient()
        await client.connect()

        connect_time = time.time() - start
        print(f"✅ Verbunden in {connect_time:.1f}s")

        # Send query
        print(f"📤 Sende {len(articles)} Artikel an Claude zum Filtern...")
        query_start = time.time()
        await client.query(prompt)

        # Receive response
        print(f"📥 Empfange Antwort von Claude...")
        response_text = ""
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(".", end="", flush=True)

        query_time = time.time() - query_start
        print(f"\n✅ Antwort empfangen in {query_time:.1f}s")

        print(f"🔌 Trenne Verbindung...")
        await client.disconnect()

        # Clean up markdown response
        digest_text = response_text.strip()
        if digest_text.startswith('```markdown'):
            digest_text = digest_text[11:]
        if digest_text.startswith('```'):
            digest_text = digest_text[3:]
        if digest_text.endswith('```'):
            digest_text = digest_text[:-3]

        digest_text = digest_text.strip()

        # Remove blank lines between bullet points in NICE-TO-KNOW section
        # This makes bullet lists more compact
        import re
        # Pattern: Find lines that are "- [text]" followed by blank line(s) followed by another "- [text]"
        # Replace with just the two bullet lines (no blank line between)
        digest_text = re.sub(r'(^- .+)(\n\n+)(^- )', r'\1\n\3', digest_text, flags=re.MULTILINE)

        print(f"\n✅ Digest erstellt ({len(digest_text)} Zeichen)\n")
        return digest_text

    except Exception as e:
        print(f"\n❌ Fehler beim Aufruf von Claude: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_digest_output(digest_text, input_file, prompt_version="v1"):
    """Save digest as markdown file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    input_name = Path(input_file).stem

    # Save as markdown
    md_filename = f"data/filtered/digest_{timestamp}_v{prompt_version}.md"

    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Weekly News Digest\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {input_file}\n\n")
        f.write("---\n\n")
        f.write(digest_text)

    return md_filename


def print_digest(digest_text):
    """Print formatted digest to console."""
    print(f"\n{'='*80}")
    print(f"NEWS DIGEST")
    print(f"{'='*80}\n")

    if not digest_text:
        print("Kein Digest erstellt.")
        return

    print(digest_text)


async def main():
    """Main execution."""
    # Get input file
    if len(sys.argv) < 2:
        # Find latest embedded dump
        dumps = sorted(Path('data/embedded').glob('*.json'))
        if not dumps:
            print("❌ Keine embedded dumps in data/embedded/ gefunden")
            print("   Führe zuerst stage3_embed_filter.py aus")
            return
        input_file = str(dumps[-1])
        print(f"Nutze neuesten embedded dump: {input_file}")
    else:
        input_file = sys.argv[1]

    # Load articles
    print(f"\nLade Artikel aus: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    date_range = data.get('date_range', {})
    date_start = date_range.get('start', 'unknown')
    date_end = date_range.get('end', 'unknown')
    print(f"Geladen: {len(articles)} Artikel von {date_start} bis {date_end}\n")

    # Create digest with Claude
    prompt_version = sys.argv[2] if len(sys.argv) > 2 else "1"
    digest = await filter_with_claude(articles, prompt_version)

    if not digest:
        print("❌ Kein Digest erstellt. Abbruch.")
        return

    # Save output
    output_file = save_digest_output(digest, input_file, prompt_version)
    print(f"💾 Digest gespeichert: {output_file}\n")

    # Print digest
    print_digest(digest)


if __name__ == '__main__':
    asyncio.run(main())
