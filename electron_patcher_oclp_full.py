#!/usr/bin/env python3
"""
Electron/Chromium Patcher for OpenCore Legacy Patcher (OCLP) Systems
COMPREHENSIVE VERSION - Includes ALL known Electron/Chromium apps

Fixes rendering issues (red/pink screens, glitches, freezes) on Macs with legacy GPUs
(AMD GCN 1-3, Nvidia Kepler) running macOS Ventura+ with OCLP patches.

Usage:
    python3 electron_patcher_oclp_full.py --patch-executables --verbose
    python3 electron_patcher_oclp_full.py --restore --verbose
    python3 electron_patcher_oclp_full.py --list-apps

Based on fixes from:
    https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1145
"""

import argparse
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict


@dataclass
class AppConfig:
    """Configuration for app-specific fixes."""
    name: str
    local_state_paths: List[str] = field(default_factory=list)
    settings_file: Optional[str] = None
    settings_key: Optional[str] = None
    needs_executable_patch: bool = True  # Default to True for most apps
    bundle_id: Optional[str] = None
    app_paths: List[str] = field(default_factory=list)
    notes: str = ""


# =============================================================================
# COMPREHENSIVE LIST OF ALL KNOWN ELECTRON/CHROMIUM APPS
# =============================================================================

KNOWN_APPS: Dict[str, AppConfig] = {
    # =========================================================================
    # WEB BROWSERS
    # =========================================================================
    "Google Chrome": AppConfig(
        name="Google Chrome",
        local_state_paths=[
            "Application Support/Google/Chrome/Local State",
            "Application Support/Google/Chrome Beta/Local State",
            "Application Support/Google/Chrome Canary/Local State",
        ],
        bundle_id="com.google.Chrome",
        app_paths=[
            "/Applications/Google Chrome.app",
            "/Applications/Google Chrome Beta.app",
            "/Applications/Google Chrome Canary.app",
        ],
        notes="Chrome 125+ removed use-angle flag from UI"
    ),
    "Microsoft Edge": AppConfig(
        name="Microsoft Edge",
        local_state_paths=["Application Support/Microsoft Edge/Local State"],
        bundle_id="com.microsoft.edgemac",
        app_paths=["/Applications/Microsoft Edge.app"],
    ),
    "Brave Browser": AppConfig(
        name="Brave Browser",
        local_state_paths=["Application Support/BraveSoftware/Brave-Browser/Local State"],
        bundle_id="com.brave.Browser",
        app_paths=["/Applications/Brave Browser.app"],
    ),
    "Vivaldi": AppConfig(
        name="Vivaldi",
        local_state_paths=["Application Support/Vivaldi/Local State"],
        bundle_id="com.vivaldi.Vivaldi",
        app_paths=["/Applications/Vivaldi.app"],
    ),
    "Opera": AppConfig(
        name="Opera",
        local_state_paths=["Application Support/com.operasoftware.Opera/Local State"],
        bundle_id="com.operasoftware.Opera",
        app_paths=["/Applications/Opera.app"],
    ),
    "Opera GX": AppConfig(
        name="Opera GX",
        local_state_paths=["Application Support/com.operasoftware.OperaGX/Local State"],
        bundle_id="com.operasoftware.OperaGX",
        app_paths=["/Applications/Opera GX.app"],
    ),
    "Arc": AppConfig(
        name="Arc",
        local_state_paths=["Application Support/Arc/Local State"],
        bundle_id="company.thebrowser.Browser",
        app_paths=["/Applications/Arc.app"],
    ),
    "Chromium": AppConfig(
        name="Chromium",
        local_state_paths=["Application Support/Chromium/Local State"],
        bundle_id="org.chromium.Chromium",
        app_paths=["/Applications/Chromium.app"],
    ),
    "Sidekick": AppConfig(
        name="Sidekick",
        local_state_paths=["Application Support/Sidekick/Local State"],
        bundle_id="com.aspect.browser",
        app_paths=["/Applications/Sidekick.app"],
    ),
    "Wavebox": AppConfig(
        name="Wavebox",
        local_state_paths=["Application Support/Wavebox/Local State"],
        bundle_id="io.wavebox.wavebox",
        app_paths=["/Applications/Wavebox.app"],
    ),
    "Yandex Browser": AppConfig(
        name="Yandex Browser",
        local_state_paths=["Application Support/Yandex/YandexBrowser/Local State"],
        bundle_id="ru.yandex.desktop.yandex-browser",
        app_paths=["/Applications/Yandex.app"],
    ),
    "Orion": AppConfig(
        name="Orion",
        bundle_id="com.kagi.kagimacOS",
        app_paths=["/Applications/Orion.app"],
    ),
    "Min Browser": AppConfig(
        name="Min Browser",
        bundle_id="com.electron.min",
        app_paths=["/Applications/Min.app"],
    ),
    "Naver Whale": AppConfig(
        name="Naver Whale",
        local_state_paths=["Application Support/Naver/Whale/Local State"],
        bundle_id="com.naver.Whale",
        app_paths=["/Applications/Whale.app"],
    ),

    # =========================================================================
    # COMMUNICATION & MESSAGING
    # =========================================================================
    "Discord": AppConfig(
        name="Discord",
        local_state_paths=["Application Support/discord/Local State"],
        bundle_id="com.hnc.Discord",
        app_paths=["/Applications/Discord.app"],
    ),
    "Discord PTB": AppConfig(
        name="Discord PTB",
        local_state_paths=["Application Support/discordptb/Local State"],
        bundle_id="com.hnc.DiscordPTB",
        app_paths=["/Applications/Discord PTB.app"],
    ),
    "Discord Canary": AppConfig(
        name="Discord Canary",
        local_state_paths=["Application Support/discordcanary/Local State"],
        bundle_id="com.hnc.DiscordCanary",
        app_paths=["/Applications/Discord Canary.app"],
    ),
    "Vesktop": AppConfig(
        name="Vesktop",
        bundle_id="dev.vencord.vesktop",
        app_paths=["/Applications/Vesktop.app"],
    ),
    "Slack": AppConfig(
        name="Slack",
        local_state_paths=["Application Support/Slack/Local State"],
        settings_file="~/Library/Application Support/Slack/local-settings.json",
        settings_key="useHwAcceleration",
        bundle_id="com.tinyspeck.slackmacgap",
        app_paths=["/Applications/Slack.app"],
    ),
    "Microsoft Teams": AppConfig(
        name="Microsoft Teams",
        local_state_paths=[
            "Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/EBWebView/Local State",
            "Application Support/Microsoft/Teams/Local State",
        ],
        bundle_id="com.microsoft.teams2",
        app_paths=["/Applications/Microsoft Teams.app", "/Applications/Microsoft Teams (work or school).app"],
    ),
    "Microsoft Teams Classic": AppConfig(
        name="Microsoft Teams Classic",
        local_state_paths=["Application Support/Microsoft/Teams/Local State"],
        bundle_id="com.microsoft.teams",
        app_paths=["/Applications/Microsoft Teams classic.app"],
    ),
    "Zoom": AppConfig(
        name="Zoom",
        bundle_id="us.zoom.xos",
        app_paths=["/Applications/zoom.us.app"],
        notes="Zoom uses native rendering but may have issues"
    ),
    "Skype": AppConfig(
        name="Skype",
        local_state_paths=["Application Support/Skype/Local State"],
        bundle_id="com.skype.skype",
        app_paths=["/Applications/Skype.app"],
    ),
    "Signal": AppConfig(
        name="Signal",
        local_state_paths=["Application Support/Signal/Local State"],
        bundle_id="org.whispersystems.signal-desktop",
        app_paths=["/Applications/Signal.app"],
        notes="Signal ignores Local State"
    ),
    "Telegram Desktop": AppConfig(
        name="Telegram Desktop",
        bundle_id="org.telegram.desktop",
        app_paths=["/Applications/Telegram Desktop.app", "/Applications/Telegram.app"],
    ),
    # WhatsApp removed - it's a native macOS app, not Electron
    "Messenger": AppConfig(
        name="Messenger",
        bundle_id="com.facebook.archon",
        app_paths=["/Applications/Messenger.app"],
    ),
    "Ferdium": AppConfig(
        name="Ferdium",
        local_state_paths=["Application Support/Ferdium/Local State"],
        bundle_id="org.ferdium.ferdium-app",
        app_paths=["/Applications/Ferdium.app"],
    ),
    "Franz": AppConfig(
        name="Franz",
        local_state_paths=["Application Support/Franz/Local State"],
        bundle_id="com.meetfranz.Franz",
        app_paths=["/Applications/Franz.app"],
    ),
    "Rambox": AppConfig(
        name="Rambox",
        local_state_paths=["Application Support/Rambox/Local State"],
        bundle_id="com.rambox.Rambox",
        app_paths=["/Applications/Rambox.app"],
    ),
    "Element": AppConfig(
        name="Element",
        local_state_paths=["Application Support/Element/Local State"],
        bundle_id="im.riot.app",
        app_paths=["/Applications/Element.app"],
    ),
    "Wire": AppConfig(
        name="Wire",
        bundle_id="com.wearezeta.zclient.mac",
        app_paths=["/Applications/Wire.app"],
    ),
    "Mattermost": AppConfig(
        name="Mattermost",
        local_state_paths=["Application Support/Mattermost/Local State"],
        bundle_id="Mattermost.Desktop",
        app_paths=["/Applications/Mattermost.app"],
    ),
    "Rocket.Chat": AppConfig(
        name="Rocket.Chat",
        local_state_paths=["Application Support/Rocket.Chat/Local State"],
        bundle_id="chat.rocket",
        app_paths=["/Applications/Rocket.Chat.app"],
    ),
    "Zulip": AppConfig(
        name="Zulip",
        bundle_id="org.zulip.zulip-electron",
        app_paths=["/Applications/Zulip.app"],
    ),
    "Guilded": AppConfig(
        name="Guilded",
        local_state_paths=["Application Support/Guilded/Local State"],
        bundle_id="com.guilded.Guilded",
        app_paths=["/Applications/Guilded.app"],
    ),
    "Beeper": AppConfig(
        name="Beeper",
        local_state_paths=["Application Support/Beeper/Local State"],
        bundle_id="com.beeper.beeper-desktop",
        app_paths=["/Applications/Beeper.app"],
    ),
    "Session": AppConfig(
        name="Session",
        local_state_paths=["Application Support/Session/Local State"],
        bundle_id="com.loki-project.messenger-desktop",
        app_paths=["/Applications/Session.app"],
    ),
    "Keybase": AppConfig(
        name="Keybase",
        bundle_id="keybase.Electron",
        app_paths=["/Applications/Keybase.app"],
    ),
    "Webex": AppConfig(
        name="Webex",
        bundle_id="Cisco-Systems.Spark",
        app_paths=["/Applications/Webex.app"],
    ),
    "RingCentral": AppConfig(
        name="RingCentral",
        bundle_id="com.ringcentral.glip",
        app_paths=["/Applications/RingCentral.app"],
    ),
    "Loom": AppConfig(
        name="Loom",
        bundle_id="com.loom.desktop",
        app_paths=["/Applications/Loom.app"],
    ),

    # =========================================================================
    # DEVELOPMENT TOOLS
    # =========================================================================
    "Visual Studio Code": AppConfig(
        name="Visual Studio Code",
        local_state_paths=["Application Support/Code/Local State"],
        bundle_id="com.microsoft.VSCode",
        app_paths=["/Applications/Visual Studio Code.app"],
        notes="VSCode ignores Local State"
    ),
    "VSCode Insiders": AppConfig(
        name="VSCode Insiders",
        local_state_paths=["Application Support/Code - Insiders/Local State"],
        bundle_id="com.microsoft.VSCodeInsiders",
        app_paths=["/Applications/Visual Studio Code - Insiders.app"],
    ),
    "VSCodium": AppConfig(
        name="VSCodium",
        local_state_paths=["Application Support/VSCodium/Local State"],
        bundle_id="com.vscodium",
        app_paths=["/Applications/VSCodium.app"],
    ),
    "Cursor": AppConfig(
        name="Cursor",
        local_state_paths=["Application Support/Cursor/Local State"],
        bundle_id="com.todesktop.230313mzl4w4u92",
        app_paths=["/Applications/Cursor.app"],
    ),
    "Windsurf": AppConfig(
        name="Windsurf",
        local_state_paths=["Application Support/Windsurf/Local State"],
        bundle_id="com.codeium.windsurf",
        app_paths=["/Applications/Windsurf.app"],
    ),
    "Zed": AppConfig(
        name="Zed",
        bundle_id="dev.zed.Zed",
        app_paths=["/Applications/Zed.app"],
        notes="Zed may use native rendering"
    ),
    "Atom": AppConfig(
        name="Atom",
        local_state_paths=["Application Support/Atom/Local State"],
        bundle_id="com.github.atom",
        app_paths=["/Applications/Atom.app"],
    ),
    "Sublime Text": AppConfig(
        name="Sublime Text",
        bundle_id="com.sublimetext.4",
        app_paths=["/Applications/Sublime Text.app"],
        needs_executable_patch=False,
        notes="Sublime Text is native, not Electron"
    ),
    "Postman": AppConfig(
        name="Postman",
        local_state_paths=["Application Support/Postman/Local State"],
        bundle_id="com.postmanlabs.mac",
        app_paths=["/Applications/Postman.app"],
    ),
    "Insomnia": AppConfig(
        name="Insomnia",
        local_state_paths=["Application Support/Insomnia/Local State"],
        bundle_id="com.insomnia.app",
        app_paths=["/Applications/Insomnia.app"],
    ),
    "Hoppscotch": AppConfig(
        name="Hoppscotch",
        bundle_id="io.hoppscotch.desktop",
        app_paths=["/Applications/Hoppscotch.app"],
    ),
    "Docker Desktop": AppConfig(
        name="Docker Desktop",
        local_state_paths=["Application Support/Docker Desktop/Local State"],
        settings_file="~/Library/Group Containers/group.com.docker/settings-store.json",
        settings_key="disableHardwareAcceleration",
        bundle_id="com.docker.docker",
        app_paths=["/Applications/Docker.app"],
        notes="Also patches settings to disable HW acceleration"
    ),
    "GitHub Desktop": AppConfig(
        name="GitHub Desktop",
        local_state_paths=["Application Support/GitHub Desktop/Local State"],
        bundle_id="com.github.GitHubClient",
        app_paths=["/Applications/GitHub Desktop.app"],
    ),
    "GitKraken": AppConfig(
        name="GitKraken",
        local_state_paths=["Application Support/GitKraken/Local State"],
        bundle_id="com.axosoft.gitkraken",
        app_paths=["/Applications/GitKraken.app"],
    ),
    "Sourcetree": AppConfig(
        name="Sourcetree",
        bundle_id="com.torusknot.SourceTreeNotMAS",
        app_paths=["/Applications/Sourcetree.app"],
    ),
    "Fork": AppConfig(
        name="Fork",
        bundle_id="com.DanPristupov.Fork",
        app_paths=["/Applications/Fork.app"],
    ),
    "Tower": AppConfig(
        name="Tower",
        bundle_id="com.fournova.Tower3",
        app_paths=["/Applications/Tower.app"],
    ),
    "Lens": AppConfig(
        name="Lens",
        local_state_paths=["Application Support/Lens/Local State"],
        bundle_id="com.mirantis.lens",
        app_paths=["/Applications/Lens.app"],
    ),
    "MongoDB Compass": AppConfig(
        name="MongoDB Compass",
        local_state_paths=["Application Support/MongoDB Compass/Local State"],
        bundle_id="com.mongodb.compass",
        app_paths=["/Applications/MongoDB Compass.app"],
    ),
    "Robo 3T": AppConfig(
        name="Robo 3T",
        bundle_id="com.3t.Robo-3T",
        app_paths=["/Applications/Robo 3T.app"],
    ),
    "Studio 3T": AppConfig(
        name="Studio 3T",
        bundle_id="com.3t.studio3t",
        app_paths=["/Applications/Studio 3T.app"],
    ),
    "DBeaver": AppConfig(
        name="DBeaver",
        bundle_id="org.jkiss.dbeaver.core.product",
        app_paths=["/Applications/DBeaver.app"],
        needs_executable_patch=False,
        notes="DBeaver is Java-based, not Electron"
    ),
    "TablePlus": AppConfig(
        name="TablePlus",
        bundle_id="com.tableplus.TablePlus",
        app_paths=["/Applications/TablePlus.app"],
        needs_executable_patch=False,
        notes="TablePlus is native"
    ),
    "Beekeeper Studio": AppConfig(
        name="Beekeeper Studio",
        local_state_paths=["Application Support/Beekeeper Studio/Local State"],
        bundle_id="io.beekeeperstudio.app",
        app_paths=["/Applications/Beekeeper Studio.app"],
    ),
    "Sequel Pro": AppConfig(
        name="Sequel Pro",
        bundle_id="com.sequelpro.SequelPro",
        app_paths=["/Applications/Sequel Pro.app"],
        needs_executable_patch=False,
    ),
    "pgAdmin 4": AppConfig(
        name="pgAdmin 4",
        bundle_id="org.pgadmin.pgadmin4",
        app_paths=["/Applications/pgAdmin 4.app"],
    ),
    "Redis Insight": AppConfig(
        name="Redis Insight",
        local_state_paths=["Application Support/Redis Insight/Local State"],
        bundle_id="com.redislabs.app",
        app_paths=["/Applications/Redis Insight.app"],
    ),
    "Proxyman": AppConfig(
        name="Proxyman",
        bundle_id="com.proxyman.NSProxy",
        app_paths=["/Applications/Proxyman.app"],
    ),
    "Charles": AppConfig(
        name="Charles",
        bundle_id="com.xk72.Charles",
        app_paths=["/Applications/Charles.app"],
        needs_executable_patch=False,
        notes="Charles is Java-based"
    ),
    "Responsively": AppConfig(
        name="Responsively",
        local_state_paths=["Application Support/Responsively/Local State"],
        bundle_id="dev.nicklucche.responsively",
        app_paths=["/Applications/Responsively App.app"],
    ),
    "Figma": AppConfig(
        name="Figma",
        local_state_paths=["Application Support/Figma/Local State"],
        bundle_id="com.figma.Desktop",
        app_paths=["/Applications/Figma.app"],
    ),
    "Framer": AppConfig(
        name="Framer",
        bundle_id="com.framer.desktop",
        app_paths=["/Applications/Framer.app"],
    ),
    "Sketch": AppConfig(
        name="Sketch",
        bundle_id="com.bohemiancoding.sketch3",
        app_paths=["/Applications/Sketch.app"],
        needs_executable_patch=False,
        notes="Sketch is native"
    ),
    "InVision Studio": AppConfig(
        name="InVision Studio",
        bundle_id="com.invisionapp.studio",
        app_paths=["/Applications/InVision Studio.app"],
    ),
    "Principle": AppConfig(
        name="Principle",
        bundle_id="com.principleformac.principle",
        app_paths=["/Applications/Principle.app"],
        needs_executable_patch=False,
    ),
    "Zeplin": AppConfig(
        name="Zeplin",
        bundle_id="io.zeplin.osx",
        app_paths=["/Applications/Zeplin.app"],
    ),
    "Abstract": AppConfig(
        name="Abstract",
        bundle_id="com.elasticprojects.abstract",
        app_paths=["/Applications/Abstract.app"],
    ),
    "Storybook": AppConfig(
        name="Storybook",
        bundle_id="com.storybook.app",
        app_paths=["/Applications/Storybook.app"],
    ),
    "RunJS": AppConfig(
        name="RunJS",
        bundle_id="runjs.runjs",
        app_paths=["/Applications/RunJS.app"],
    ),
    "Warp": AppConfig(
        name="Warp",
        bundle_id="dev.warp.Warp-Stable",
        app_paths=["/Applications/Warp.app"],
        notes="Warp uses Rust/native with GPU acceleration"
    ),
    "Hyper": AppConfig(
        name="Hyper",
        local_state_paths=["Application Support/Hyper/Local State"],
        bundle_id="co.zeit.hyper",
        app_paths=["/Applications/Hyper.app"],
    ),
    "Tabby": AppConfig(
        name="Tabby",
        local_state_paths=["Application Support/Tabby/Local State"],
        bundle_id="org.tabby",
        app_paths=["/Applications/Tabby.app"],
    ),
    "iTerm2": AppConfig(
        name="iTerm2",
        bundle_id="com.googlecode.iterm2",
        app_paths=["/Applications/iTerm.app"],
        needs_executable_patch=False,
        notes="iTerm2 is native"
    ),
    "Kitty": AppConfig(
        name="Kitty",
        bundle_id="net.kovidgoyal.kitty",
        app_paths=["/Applications/kitty.app"],
        needs_executable_patch=False,
    ),
    "Alacritty": AppConfig(
        name="Alacritty",
        bundle_id="org.alacritty",
        app_paths=["/Applications/Alacritty.app"],
        needs_executable_patch=False,
    ),

    # =========================================================================
    # NOTE TAKING & PRODUCTIVITY
    # =========================================================================
    "Notion": AppConfig(
        name="Notion",
        local_state_paths=["Application Support/Notion/Local State"],
        bundle_id="notion.id",
        app_paths=["/Applications/Notion.app"],
    ),
    "Notion Calendar": AppConfig(
        name="Notion Calendar",
        bundle_id="com.cron.electron",
        app_paths=["/Applications/Notion Calendar.app"],
    ),
    "Obsidian": AppConfig(
        name="Obsidian",
        local_state_paths=["Application Support/obsidian/Local State"],
        bundle_id="md.obsidian",
        app_paths=["/Applications/Obsidian.app"],
        notes="Also disable HW accel in Settings > Appearance"
    ),
    "Logseq": AppConfig(
        name="Logseq",
        local_state_paths=["Application Support/Logseq/Local State"],
        bundle_id="com.electron.logseq",
        app_paths=["/Applications/Logseq.app"],
    ),
    "Roam Research": AppConfig(
        name="Roam Research",
        bundle_id="com.roamresearch.app",
        app_paths=["/Applications/Roam Research.app"],
    ),
    "Craft": AppConfig(
        name="Craft",
        bundle_id="com.lukilabs.lukiapp",
        app_paths=["/Applications/Craft.app"],
    ),
    "Coda": AppConfig(
        name="Coda",
        bundle_id="io.coda.app",
        app_paths=["/Applications/Coda.app"],
    ),
    "Evernote": AppConfig(
        name="Evernote",
        local_state_paths=["Application Support/Evernote/Local State"],
        bundle_id="com.evernote.Evernote",
        app_paths=["/Applications/Evernote.app"],
    ),
    "Standard Notes": AppConfig(
        name="Standard Notes",
        local_state_paths=["Application Support/Standard Notes/Local State"],
        bundle_id="org.standardnotes.standardnotes",
        app_paths=["/Applications/Standard Notes.app"],
    ),
    "Simplenote": AppConfig(
        name="Simplenote",
        bundle_id="com.automattic.simplenote",
        app_paths=["/Applications/Simplenote.app"],
    ),
    "Joplin": AppConfig(
        name="Joplin",
        local_state_paths=["Application Support/Joplin/Local State"],
        bundle_id="net.cozic.joplin-desktop",
        app_paths=["/Applications/Joplin.app"],
    ),
    "Bear": AppConfig(
        name="Bear",
        bundle_id="net.shinyfrog.bear",
        app_paths=["/Applications/Bear.app"],
        needs_executable_patch=False,
        notes="Bear is native"
    ),
    "Ulysses": AppConfig(
        name="Ulysses",
        bundle_id="com.ulyssesapp.mac",
        app_paths=["/Applications/Ulysses.app"],
        needs_executable_patch=False,
    ),
    "iA Writer": AppConfig(
        name="iA Writer",
        bundle_id="pro.writer.mac",
        app_paths=["/Applications/iA Writer.app"],
        needs_executable_patch=False,
    ),
    "Typora": AppConfig(
        name="Typora",
        local_state_paths=["Application Support/Typora/Local State"],
        bundle_id="abnerworks.Typora",
        app_paths=["/Applications/Typora.app"],
    ),
    "Mark Text": AppConfig(
        name="Mark Text",
        local_state_paths=["Application Support/Mark Text/Local State"],
        bundle_id="com.github.marktext.marktext",
        app_paths=["/Applications/Mark Text.app"],
    ),
    "Todoist": AppConfig(
        name="Todoist",
        local_state_paths=["Application Support/Todoist/Local State"],
        bundle_id="com.todoist.mac.Todoist",
        app_paths=["/Applications/Todoist.app"],
    ),
    "TickTick": AppConfig(
        name="TickTick",
        bundle_id="com.TickTick.task.mac",
        app_paths=["/Applications/TickTick.app"],
    ),
    "Things 3": AppConfig(
        name="Things 3",
        bundle_id="com.culturedcode.ThingsMac",
        app_paths=["/Applications/Things3.app"],
        needs_executable_patch=False,
    ),
    "OmniFocus": AppConfig(
        name="OmniFocus",
        bundle_id="com.omnigroup.OmniFocus3",
        app_paths=["/Applications/OmniFocus 3.app"],
        needs_executable_patch=False,
    ),
    "Asana": AppConfig(
        name="Asana",
        local_state_paths=["Application Support/Asana/Local State"],
        bundle_id="com.asana.desktop",
        app_paths=["/Applications/Asana.app"],
    ),
    "Monday.com": AppConfig(
        name="Monday.com",
        bundle_id="com.monday.monday-desktop-app",
        app_paths=["/Applications/monday.com.app"],
    ),
    "Linear": AppConfig(
        name="Linear",
        local_state_paths=["Application Support/Linear/Local State"],
        bundle_id="com.linear.app",
        app_paths=["/Applications/Linear.app"],
    ),
    "Height": AppConfig(
        name="Height",
        bundle_id="com.height.app",
        app_paths=["/Applications/Height.app"],
    ),
    "Trello": AppConfig(
        name="Trello",
        bundle_id="com.trello.desktop",
        app_paths=["/Applications/Trello.app"],
    ),
    "ClickUp": AppConfig(
        name="ClickUp",
        local_state_paths=["Application Support/ClickUp/Local State"],
        bundle_id="com.clickup.desktop-app",
        app_paths=["/Applications/ClickUp.app"],
    ),
    "Milanote": AppConfig(
        name="Milanote",
        bundle_id="com.milanote.app",
        app_paths=["/Applications/Milanote.app"],
    ),
    "Miro": AppConfig(
        name="Miro",
        local_state_paths=["Application Support/Miro/Local State"],
        bundle_id="com.electron.miro",
        app_paths=["/Applications/Miro.app"],
    ),
    "Whimsical": AppConfig(
        name="Whimsical",
        bundle_id="com.whimsical.desktop",
        app_paths=["/Applications/Whimsical.app"],
    ),
    "Airtable": AppConfig(
        name="Airtable",
        local_state_paths=["Application Support/Airtable/Local State"],
        bundle_id="com.airtable.desktop",
        app_paths=["/Applications/Airtable.app"],
    ),
    "Cron": AppConfig(
        name="Cron",
        bundle_id="com.cron.electron",
        app_paths=["/Applications/Cron.app"],
    ),
    "Fantastical": AppConfig(
        name="Fantastical",
        bundle_id="com.flexibits.fantastical2.mac",
        app_paths=["/Applications/Fantastical.app"],
        needs_executable_patch=False,
    ),
    "Calendly": AppConfig(
        name="Calendly",
        bundle_id="com.calendly.electron",
        app_paths=["/Applications/Calendly.app"],
    ),

    # =========================================================================
    # MUSIC & MEDIA
    # =========================================================================
    # NOTE: Spotify has helper apps that break with executable patching.
    # Use a launcher app instead: create "Spotify OCLP.app" that runs:
    # exec /Applications/Spotify.app/Contents/MacOS/Spotify --use-angle=gl "$@"
    "Spotify": AppConfig(
        name="Spotify",
        local_state_paths=["Caches/com.spotify.client/Local State"],
        bundle_id="com.spotify.client",
        app_paths=["/Applications/Spotify.app"],
        needs_executable_patch=False,  # Has helper apps that break with renaming
    ),
    "Tidal": AppConfig(
        name="Tidal",
        local_state_paths=["Application Support/TIDAL/Local State"],
        bundle_id="com.tidal.desktop",
        app_paths=["/Applications/TIDAL.app"],
    ),
    "Deezer": AppConfig(
        name="Deezer",
        bundle_id="com.deezer.deezer-desktop",
        app_paths=["/Applications/Deezer.app"],
    ),
    "Amazon Music": AppConfig(
        name="Amazon Music",
        bundle_id="com.amazon.music",
        app_paths=["/Applications/Amazon Music.app"],
    ),
    "YouTube Music": AppConfig(
        name="YouTube Music",
        bundle_id="com.github.nickvision-apps.cavalier",
        app_paths=["/Applications/YouTube Music.app"],
    ),
    "SoundCloud": AppConfig(
        name="SoundCloud",
        bundle_id="com.soundcloud.desktop",
        app_paths=["/Applications/SoundCloud.app"],
    ),
    "Plexamp": AppConfig(
        name="Plexamp",
        local_state_paths=["Application Support/Plexamp/Local State"],
        bundle_id="com.plexamp.plex",
        app_paths=["/Applications/Plexamp.app"],
    ),
    "Plex": AppConfig(
        name="Plex",
        local_state_paths=["Application Support/Plex/Local State"],
        bundle_id="tv.plex.desktop",
        app_paths=["/Applications/Plex.app"],
    ),
    "VLC": AppConfig(
        name="VLC",
        bundle_id="org.videolan.vlc",
        app_paths=["/Applications/VLC.app"],
        needs_executable_patch=False,
        notes="VLC is native"
    ),
    "IINA": AppConfig(
        name="IINA",
        bundle_id="com.colliderli.iina",
        app_paths=["/Applications/IINA.app"],
        needs_executable_patch=False,
    ),
    "Audacity": AppConfig(
        name="Audacity",
        bundle_id="org.audacityteam.audacity",
        app_paths=["/Applications/Audacity.app"],
        needs_executable_patch=False,
    ),
    "OBS Studio": AppConfig(
        name="OBS Studio",
        bundle_id="com.obsproject.obs-studio",
        app_paths=["/Applications/OBS.app"],
        needs_executable_patch=False,
    ),
    "Streamlabs Desktop": AppConfig(
        name="Streamlabs Desktop",
        bundle_id="com.streamlabs.slobs",
        app_paths=["/Applications/Streamlabs Desktop.app"],
    ),

    # =========================================================================
    # PASSWORD MANAGERS & SECURITY
    # =========================================================================
    "1Password": AppConfig(
        name="1Password",
        settings_file="~/Library/Group Containers/2BUA8C4S2C.com.1password/Library/Application Support/1Password/Data/settings/settings.json",
        settings_key="app.useHardwareAcceleration",
        bundle_id="com.1password.1password",
        app_paths=["/Applications/1Password.app"],
        needs_executable_patch=False,
        notes="Disable 'Use Hardware Acceleration' in Settings > Advanced"
    ),
    "Bitwarden": AppConfig(
        name="Bitwarden",
        local_state_paths=["Application Support/Bitwarden/Local State"],
        bundle_id="com.bitwarden.desktop",
        app_paths=["/Applications/Bitwarden.app"],
    ),
    "Dashlane": AppConfig(
        name="Dashlane",
        bundle_id="com.dashlane.dashlanephonefinal",
        app_paths=["/Applications/Dashlane.app"],
    ),
    "LastPass": AppConfig(
        name="LastPass",
        bundle_id="com.lastpass.lpapp.mac.lastpass",
        app_paths=["/Applications/LastPass.app"],
    ),
    "KeePassXC": AppConfig(
        name="KeePassXC",
        bundle_id="org.keepassxc.keepassxc",
        app_paths=["/Applications/KeePassXC.app"],
        needs_executable_patch=False,
    ),
    "Enpass": AppConfig(
        name="Enpass",
        bundle_id="in.sinew.Enpass-Desktop",
        app_paths=["/Applications/Enpass.app"],
    ),
    "NordPass": AppConfig(
        name="NordPass",
        bundle_id="com.nordpass.macos.NordPass",
        app_paths=["/Applications/NordPass.app"],
    ),
    "NordVPN": AppConfig(
        name="NordVPN",
        bundle_id="com.nordvpn.mac",
        app_paths=["/Applications/NordVPN.app"],
    ),
    "ExpressVPN": AppConfig(
        name="ExpressVPN",
        bundle_id="com.expressvpn.expressvpn",
        app_paths=["/Applications/ExpressVPN.app"],
    ),
    "Mullvad VPN": AppConfig(
        name="Mullvad VPN",
        bundle_id="net.mullvad.vpn",
        app_paths=["/Applications/Mullvad VPN.app"],
    ),
    "ProtonVPN": AppConfig(
        name="ProtonVPN",
        bundle_id="ch.protonvpn.mac",
        app_paths=["/Applications/ProtonVPN.app"],
    ),

    # =========================================================================
    # OFFICE & DOCUMENTS
    # =========================================================================
    "Microsoft Word": AppConfig(
        name="Microsoft Word",
        bundle_id="com.microsoft.Word",
        app_paths=["/Applications/Microsoft Word.app"],
        needs_executable_patch=False,
        notes="MS Office uses native rendering"
    ),
    "Microsoft Excel": AppConfig(
        name="Microsoft Excel",
        bundle_id="com.microsoft.Excel",
        app_paths=["/Applications/Microsoft Excel.app"],
        needs_executable_patch=False,
    ),
    "Microsoft PowerPoint": AppConfig(
        name="Microsoft PowerPoint",
        bundle_id="com.microsoft.Powerpoint",
        app_paths=["/Applications/Microsoft PowerPoint.app"],
        needs_executable_patch=False,
    ),
    "Microsoft Outlook": AppConfig(
        name="Microsoft Outlook",
        bundle_id="com.microsoft.Outlook",
        app_paths=["/Applications/Microsoft Outlook.app"],
        needs_executable_patch=False,
    ),
    "LibreOffice": AppConfig(
        name="LibreOffice",
        bundle_id="org.libreoffice.script",
        app_paths=["/Applications/LibreOffice.app"],
        needs_executable_patch=False,
    ),
    "Google Docs Editors": AppConfig(
        name="Google Docs Editors",
        bundle_id="com.google.GoogleDocuments",
        app_paths=["/Applications/Google Docs Editors.app"],
    ),
    "Canva": AppConfig(
        name="Canva",
        bundle_id="com.canva.CanvaDesktop",
        app_paths=["/Applications/Canva.app"],
    ),

    # =========================================================================
    # FILE MANAGEMENT & UTILITIES
    # =========================================================================
    "Dropbox": AppConfig(
        name="Dropbox",
        bundle_id="com.getdropbox.dropbox",
        app_paths=["/Applications/Dropbox.app"],
    ),
    "Google Drive": AppConfig(
        name="Google Drive",
        bundle_id="com.google.drivefs",
        app_paths=["/Applications/Google Drive.app"],
    ),
    "OneDrive": AppConfig(
        name="OneDrive",
        bundle_id="com.microsoft.OneDrive",
        app_paths=["/Applications/OneDrive.app"],
    ),
    "Box Drive": AppConfig(
        name="Box Drive",
        bundle_id="com.box.desktop",
        app_paths=["/Applications/Box.app"],
    ),
    "Tresorit": AppConfig(
        name="Tresorit",
        bundle_id="com.tresorit.Tresorit",
        app_paths=["/Applications/Tresorit.app"],
    ),
    "Cryptomator": AppConfig(
        name="Cryptomator",
        bundle_id="org.cryptomator",
        app_paths=["/Applications/Cryptomator.app"],
    ),
    "Transmit": AppConfig(
        name="Transmit",
        bundle_id="com.panic.Transmit",
        app_paths=["/Applications/Transmit.app"],
        needs_executable_patch=False,
    ),
    "Cyberduck": AppConfig(
        name="Cyberduck",
        bundle_id="ch.sudo.cyberduck",
        app_paths=["/Applications/Cyberduck.app"],
    ),
    "FileZilla": AppConfig(
        name="FileZilla",
        bundle_id="org.filezilla-project.filezilla",
        app_paths=["/Applications/FileZilla.app"],
        needs_executable_patch=False,
    ),
    "ForkLift": AppConfig(
        name="ForkLift",
        bundle_id="com.binarynights.ForkLift-3",
        app_paths=["/Applications/ForkLift.app"],
        needs_executable_patch=False,
    ),
    "Path Finder": AppConfig(
        name="Path Finder",
        bundle_id="com.cocoatech.PathFinder",
        app_paths=["/Applications/Path Finder.app"],
        needs_executable_patch=False,
    ),
    "Commander One": AppConfig(
        name="Commander One",
        bundle_id="com.eltima.cmd1",
        app_paths=["/Applications/Commander One.app"],
        needs_executable_patch=False,
    ),
    "Keka": AppConfig(
        name="Keka",
        bundle_id="com.aone.keka",
        app_paths=["/Applications/Keka.app"],
        needs_executable_patch=False,
    ),
    "The Unarchiver": AppConfig(
        name="The Unarchiver",
        bundle_id="com.macpaw.site.theunarchiver",
        app_paths=["/Applications/The Unarchiver.app"],
        needs_executable_patch=False,
    ),
    "AppCleaner": AppConfig(
        name="AppCleaner",
        bundle_id="com.freemacsoft.AppCleaner",
        app_paths=["/Applications/AppCleaner.app"],
        needs_executable_patch=False,
    ),
    "CleanMyMac X": AppConfig(
        name="CleanMyMac X",
        bundle_id="com.macpaw.CleanMyMac4",
        app_paths=["/Applications/CleanMyMac X.app"],
        needs_executable_patch=False,
    ),

    # =========================================================================
    # GRAPHICS & DESIGN
    # =========================================================================
    "Adobe Creative Cloud": AppConfig(
        name="Adobe Creative Cloud",
        bundle_id="com.adobe.acc.installer",
        app_paths=["/Applications/Adobe Creative Cloud/Adobe Creative Cloud.app"],
    ),
    "Affinity Photo": AppConfig(
        name="Affinity Photo",
        bundle_id="com.seriflabs.affinityphoto",
        app_paths=["/Applications/Affinity Photo 2.app", "/Applications/Affinity Photo.app"],
        needs_executable_patch=False,
    ),
    "Affinity Designer": AppConfig(
        name="Affinity Designer",
        bundle_id="com.seriflabs.affinitydesigner",
        app_paths=["/Applications/Affinity Designer 2.app", "/Applications/Affinity Designer.app"],
        needs_executable_patch=False,
    ),
    "Pixelmator Pro": AppConfig(
        name="Pixelmator Pro",
        bundle_id="com.pixelmatorteam.pixelmator.x",
        app_paths=["/Applications/Pixelmator Pro.app"],
        needs_executable_patch=False,
    ),
    "GIMP": AppConfig(
        name="GIMP",
        bundle_id="org.gimp.gimp-2.10",
        app_paths=["/Applications/GIMP-2.10.app", "/Applications/GIMP.app"],
        needs_executable_patch=False,
    ),
    "Inkscape": AppConfig(
        name="Inkscape",
        bundle_id="org.inkscape.Inkscape",
        app_paths=["/Applications/Inkscape.app"],
        needs_executable_patch=False,
    ),
    "Blender": AppConfig(
        name="Blender",
        bundle_id="org.blenderfoundation.blender",
        app_paths=["/Applications/Blender.app"],
        needs_executable_patch=False,
    ),
    "DaVinci Resolve": AppConfig(
        name="DaVinci Resolve",
        bundle_id="com.blackmagic-design.DaVinciResolve",
        app_paths=["/Applications/DaVinci Resolve/DaVinci Resolve.app"],
        needs_executable_patch=False,
    ),
    "Final Cut Pro": AppConfig(
        name="Final Cut Pro",
        bundle_id="com.apple.FinalCut",
        app_paths=["/Applications/Final Cut Pro.app"],
        needs_executable_patch=False,
    ),
    "Logic Pro": AppConfig(
        name="Logic Pro",
        bundle_id="com.apple.logic10",
        app_paths=["/Applications/Logic Pro.app"],
        needs_executable_patch=False,
    ),

    # =========================================================================
    # SOCIAL & ENTERTAINMENT
    # =========================================================================
    "Twitter": AppConfig(
        name="Twitter",
        bundle_id="com.twitter.twitter-mac",
        app_paths=["/Applications/Twitter.app"],
    ),
    "TweetDeck": AppConfig(
        name="TweetDeck",
        bundle_id="com.twitter.TweetDeck",
        app_paths=["/Applications/TweetDeck.app"],
    ),
    "Reddit": AppConfig(
        name="Reddit",
        bundle_id="com.reddit.reddit",
        app_paths=["/Applications/Reddit.app"],
    ),
    "Steam": AppConfig(
        name="Steam",
        bundle_id="com.valvesoftware.steam",
        app_paths=["/Applications/Steam.app"],
    ),
    "Epic Games Launcher": AppConfig(
        name="Epic Games Launcher",
        bundle_id="com.epicgames.EpicGamesLauncher",
        app_paths=["/Applications/Epic Games Launcher.app"],
    ),
    "GOG Galaxy": AppConfig(
        name="GOG Galaxy",
        bundle_id="com.gog.galaxy",
        app_paths=["/Applications/GOG Galaxy.app"],
    ),
    "Battle.net": AppConfig(
        name="Battle.net",
        bundle_id="net.battle.Bootstrap",
        app_paths=["/Applications/Battle.net.app"],
    ),
    "Twitch": AppConfig(
        name="Twitch",
        bundle_id="tv.twitch.studio",
        app_paths=["/Applications/Twitch.app"],
    ),

    # =========================================================================
    # MISCELLANEOUS
    # =========================================================================
    "Setapp": AppConfig(
        name="Setapp",
        bundle_id="com.setapp.DesktopClient",
        app_paths=["/Applications/Setapp.app"],
    ),
    "Alfred": AppConfig(
        name="Alfred",
        bundle_id="com.runningwithcrayons.Alfred",
        app_paths=["/Applications/Alfred 5.app", "/Applications/Alfred.app"],
        needs_executable_patch=False,
    ),
    "Raycast": AppConfig(
        name="Raycast",
        bundle_id="com.raycast.macos",
        app_paths=["/Applications/Raycast.app"],
    ),
    "Bartender": AppConfig(
        name="Bartender",
        bundle_id="com.surteesstudios.Bartender",
        app_paths=["/Applications/Bartender 4.app"],
        needs_executable_patch=False,
    ),
    "BetterTouchTool": AppConfig(
        name="BetterTouchTool",
        bundle_id="com.hegenberg.BetterTouchTool",
        app_paths=["/Applications/BetterTouchTool.app"],
        needs_executable_patch=False,
    ),
    "Karabiner-Elements": AppConfig(
        name="Karabiner-Elements",
        bundle_id="org.pqrs.Karabiner-Elements",
        app_paths=["/Applications/Karabiner-Elements.app"],
        needs_executable_patch=False,
    ),
    "Rectangle": AppConfig(
        name="Rectangle",
        bundle_id="com.knollsoft.Rectangle",
        app_paths=["/Applications/Rectangle.app"],
        needs_executable_patch=False,
    ),
    "Magnet": AppConfig(
        name="Magnet",
        bundle_id="id.noteifyapp.app-free",
        app_paths=["/Applications/Magnet.app"],
        needs_executable_patch=False,
    ),
    "Amphetamine": AppConfig(
        name="Amphetamine",
        bundle_id="com.if.Amphetamine",
        app_paths=["/Applications/Amphetamine.app"],
        needs_executable_patch=False,
    ),
    "Clipboard Manager": AppConfig(
        name="Clipboard Manager",
        bundle_id="com.copyq.copyq",
        app_paths=["/Applications/CopyQ.app"],
    ),
    "Paste": AppConfig(
        name="Paste",
        bundle_id="com.wiheads.paste",
        app_paths=["/Applications/Paste.app"],
        needs_executable_patch=False,
    ),
    "Maccy": AppConfig(
        name="Maccy",
        bundle_id="org.p0deje.Maccy",
        app_paths=["/Applications/Maccy.app"],
        needs_executable_patch=False,
    ),
    "Grammarly": AppConfig(
        name="Grammarly",
        bundle_id="com.grammarly.ProjectLlama",
        app_paths=["/Applications/Grammarly Desktop.app"],
    ),
    "LanguageTool": AppConfig(
        name="LanguageTool",
        bundle_id="org.languagetool.app",
        app_paths=["/Applications/LanguageTool.app"],
    ),
    "DeepL": AppConfig(
        name="DeepL",
        bundle_id="com.linguee.DeepLCopyTranslator",
        app_paths=["/Applications/DeepL.app"],
    ),
    "Krisp": AppConfig(
        name="Krisp",
        bundle_id="ai.krisp.krispMac",
        app_paths=["/Applications/Krisp.app"],
    ),
    "CleanShot X": AppConfig(
        name="CleanShot X",
        bundle_id="pl.maketheweb.cleanshotx",
        app_paths=["/Applications/CleanShot X.app"],
        needs_executable_patch=False,
    ),
    "Shottr": AppConfig(
        name="Shottr",
        bundle_id="cc.ffitch.shottr",
        app_paths=["/Applications/Shottr.app"],
        needs_executable_patch=False,
    ),
    "Snagit": AppConfig(
        name="Snagit",
        bundle_id="com.techsmith.snagit",
        app_paths=["/Applications/Snagit 2024.app", "/Applications/Snagit.app"],
    ),
    "ScreenFlow": AppConfig(
        name="ScreenFlow",
        bundle_id="net.telestream.screenflow10",
        app_paths=["/Applications/ScreenFlow.app"],
        needs_executable_patch=False,
    ),
    "Hand Mirror": AppConfig(
        name="Hand Mirror",
        bundle_id="com.rafkyokian.handmirror",
        app_paths=["/Applications/Hand Mirror.app"],
        needs_executable_patch=False,
    ),
    "PDF Expert": AppConfig(
        name="PDF Expert",
        bundle_id="com.readdle.PDFExpert-Mac",
        app_paths=["/Applications/PDF Expert.app"],
        needs_executable_patch=False,
    ),
    "PDF Pen": AppConfig(
        name="PDF Pen",
        bundle_id="com.smileonmymac.PDFpenPro3",
        app_paths=["/Applications/PDFpenPro.app"],
        needs_executable_patch=False,
    ),
    "Acrobat Reader": AppConfig(
        name="Acrobat Reader",
        bundle_id="com.adobe.Reader",
        app_paths=["/Applications/Adobe Acrobat Reader.app"],
        needs_executable_patch=False,
    ),
    "Kindle": AppConfig(
        name="Kindle",
        bundle_id="com.amazon.Kindle",
        app_paths=["/Applications/Kindle.app"],
    ),
    "calibre": AppConfig(
        name="calibre",
        bundle_id="net.kovidgoyal.calibre",
        app_paths=["/Applications/calibre.app"],
        needs_executable_patch=False,
    ),
    "Pocket": AppConfig(
        name="Pocket",
        bundle_id="com.readitlater.PocketMac",
        app_paths=["/Applications/Pocket.app"],
    ),
    "Reeder": AppConfig(
        name="Reeder",
        bundle_id="com.reederapp.5.macOS",
        app_paths=["/Applications/Reeder 5.app", "/Applications/Reeder.app"],
        needs_executable_patch=False,
    ),
    "NetNewsWire": AppConfig(
        name="NetNewsWire",
        bundle_id="com.ranchero.NetNewsWire-Evergreen",
        app_paths=["/Applications/NetNewsWire.app"],
        needs_executable_patch=False,
    ),
    "Raindrop.io": AppConfig(
        name="Raindrop.io",
        bundle_id="io.raindrop.macapp",
        app_paths=["/Applications/Raindrop.io.app"],
    ),
    "balenaEtcher": AppConfig(
        name="balenaEtcher",
        local_state_paths=["Application Support/balena-etcher/Local State"],
        bundle_id="io.balena.etcher",
        app_paths=["/Applications/balenaEtcher.app"],
    ),
    "Raspberry Pi Imager": AppConfig(
        name="Raspberry Pi Imager",
        bundle_id="org.raspberrypi.imagingutility",
        app_paths=["/Applications/Raspberry Pi Imager.app"],
    ),
    "VirtualBuddy": AppConfig(
        name="VirtualBuddy",
        bundle_id="codes.rambo.VirtualBuddy",
        app_paths=["/Applications/VirtualBuddy.app"],
        needs_executable_patch=False,
    ),
    "UTM": AppConfig(
        name="UTM",
        bundle_id="com.utmapp.UTM",
        app_paths=["/Applications/UTM.app"],
        needs_executable_patch=False,
    ),
    "Parallels Desktop": AppConfig(
        name="Parallels Desktop",
        bundle_id="com.parallels.desktop.console",
        app_paths=["/Applications/Parallels Desktop.app"],
        needs_executable_patch=False,
    ),
    "VMware Fusion": AppConfig(
        name="VMware Fusion",
        bundle_id="com.vmware.fusion",
        app_paths=["/Applications/VMware Fusion.app"],
        needs_executable_patch=False,
    ),
    "VirtualBox": AppConfig(
        name="VirtualBox",
        bundle_id="org.virtualbox.app.VirtualBox",
        app_paths=["/Applications/VirtualBox.app"],
        needs_executable_patch=False,
    ),
}

# Backup suffix for original executables
BACKUP_SUFFIX = ".oclp-original"
WRAPPER_MARKER = "# OCLP-WRAPPER-SCRIPT"


class ElectronPatcher:
    """Main patcher class for Electron/Chromium apps on OCLP systems."""

    DESIRED_KEY = "use-angle"
    DESIRED_VALUE = "1"  # OpenGL

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.home = Path.home()
        self.library = self.home / "Library"
        self.results = {}

    def log(self, msg: str, force: bool = False):
        if self.verbose or force:
            print(msg)

    def find_app_path(self, config: AppConfig) -> Optional[Path]:
        for app_path in config.app_paths:
            p = Path(app_path)
            if p.exists():
                return p

        if config.bundle_id:
            try:
                result = subprocess.run(
                    ["mdfind", "kMDItemCFBundleIdentifier == '{}'".format(config.bundle_id)],
                    capture_output=True, text=True, timeout=10
                )
                app_paths = [p for p in result.stdout.strip().split("\n") if p.endswith(".app")]
                if app_paths:
                    return Path(app_paths[0])
            except Exception:
                pass

        return None

    def get_executable_from_app(self, app_path: Path) -> Optional[Path]:
        if not app_path:
            return None
            
        info_plist = app_path / "Contents" / "Info.plist"
        if not info_plist.exists():
            return None

        try:
            with open(info_plist, "rb") as f:
                plist = plistlib.load(f)

            executable_name = plist.get("CFBundleExecutable")
            if executable_name:
                return app_path / "Contents" / "MacOS" / executable_name
        except Exception as e:
            self.log(f"  [ERROR] Failed to read Info.plist: {e}")

        return None

    def is_app_running(self, config: AppConfig) -> bool:
        if not config.bundle_id:
            return False

        try:
            result = subprocess.run(
                ["pgrep", "-f", config.bundle_id],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["pgrep", "-f", config.name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def is_already_patched(self, executable_path: Path) -> bool:
        if not executable_path or not executable_path.exists():
            return False

        try:
            content = executable_path.read_text()
            return WRAPPER_MARKER in content
        except Exception:
            return False

    def create_wrapper_script(self, original_path: Path, backup_path: Path) -> str:
        return '''#!/bin/bash
{}
# This wrapper was created by electron_patcher_oclp_full.py
# Original executable backed up to: {}
# To restore: mv "{}" "{}"

# Path to the original executable (backup)
ORIGINAL_EXEC="{}"

# Launch with OpenGL ANGLE backend
exec "$ORIGINAL_EXEC" --use-angle=gl "$@"
'''.format(WRAPPER_MARKER, backup_path.name, backup_path, original_path, str(backup_path))

    def patch_executable(self, config: AppConfig) -> bool:
        app_path = self.find_app_path(config)
        if not app_path:
            self.log(f"  [SKIP] App not found: {config.name}")
            return False

        executable_path = self.get_executable_from_app(app_path)
        if not executable_path:
            self.log(f"  [ERROR] Could not find executable in {app_path}")
            return False

        backup_path = executable_path.with_suffix(executable_path.suffix + BACKUP_SUFFIX)

        if self.is_already_patched(executable_path):
            self.log(f"  [OK] Already patched: {executable_path}")
            return False

        if backup_path.exists() and not self.is_already_patched(executable_path):
            self.log(f"  [WARN] Backup exists but executable isn't patched. Restoring first...")
            if not self.dry_run:
                shutil.copy2(backup_path, executable_path)

        if self.is_app_running(config):
            self.log(f"  [ERROR] {config.name} is running. Please quit it first.", force=True)
            return False

        self.log(f"  [PATCH] {executable_path}")

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would backup to: {backup_path}")
            self.log(f"  [DRY-RUN] Would create wrapper script")
            return True

        try:
            if not backup_path.exists():
                shutil.copy2(executable_path, backup_path)
                self.log(f"  [BACKUP] Created: {backup_path}")

            wrapper_script = self.create_wrapper_script(executable_path, backup_path)
            executable_path.write_text(wrapper_script)

            executable_path.chmod(executable_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            # Re-sign the app
            if app_path:
                self.log(f"  [SIGN] Re-signing {app_path}...")
                try:
                    subprocess.run(
                        ["xattr", "-cr", str(app_path)],
                        capture_output=True, check=False
                    )
                    result = subprocess.run(
                        ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        self.log(f"  [SIGN] Successfully re-signed")
                    else:
                        self.log(f"  [WARN] Code signing failed: {result.stderr}")
                        self.log(f"  [WARN] Try: sudo codesign --force --deep --sign - \"{app_path}\"", force=True)
                except Exception as e:
                    self.log(f"  [WARN] Could not re-sign: {e}")

            self.log(f"  [SUCCESS] Patched {config.name}")
            return True

        except PermissionError:
            self.log(f"  [ERROR] Permission denied. Try: sudo python3 {sys.argv[0]} ...", force=True)
            return False
        except Exception as e:
            self.log(f"  [ERROR] Failed to patch: {e}", force=True)
            return False

    def restore_executable(self, config: AppConfig) -> bool:
        app_path = self.find_app_path(config)
        if not app_path:
            self.log(f"  [SKIP] App not found: {config.name}")
            return False

        executable_path = self.get_executable_from_app(app_path)
        if not executable_path:
            self.log(f"  [ERROR] Could not find executable in {app_path}")
            return False

        backup_path = executable_path.with_suffix(executable_path.suffix + BACKUP_SUFFIX)

        if not backup_path.exists():
            self.log(f"  [SKIP] No backup found for {config.name}")
            return False

        if self.is_app_running(config):
            self.log(f"  [ERROR] {config.name} is running. Please quit it first.", force=True)
            return False

        self.log(f"  [RESTORE] {executable_path}")

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would restore from: {backup_path}")
            return True

        try:
            shutil.copy2(backup_path, executable_path)
            backup_path.unlink()
            
            # Re-sign after restore
            if app_path:
                subprocess.run(["xattr", "-cr", str(app_path)], capture_output=True, check=False)
                subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app_path)], 
                             capture_output=True, check=False)
            
            self.log(f"  [SUCCESS] Restored {config.name}")
            return True
        except Exception as e:
            self.log(f"  [ERROR] Failed to restore: {e}", force=True)
            return False

    def patch_local_state(self, state_file: Path, app_name: str) -> bool:
        if not state_file.exists():
            self.log(f"  [SKIP] Local State not found: {state_file}")
            return False

        try:
            state_data = json.loads(state_file.read_text())
        except Exception as e:
            self.log(f"  [ERROR] Failed to parse {state_file}: {e}")
            return False

        browser = state_data.setdefault("browser", {})
        experiments = browser.setdefault("enabled_labs_experiments", [])

        if not isinstance(experiments, list):
            experiments = []
            browser["enabled_labs_experiments"] = experiments

        replacement = "{}@{}".format(self.DESIRED_KEY, self.DESIRED_VALUE)
        changed = False
        found_correct = False

        for i, entry in enumerate(experiments):
            if not isinstance(entry, str) or "@" not in entry:
                continue
            parts = entry.split("@")
            key = parts[0]
            rest = parts[1:] if len(parts) > 1 else []
            if key != self.DESIRED_KEY:
                continue
            current_value = rest[0] if rest else ""
            if current_value == self.DESIRED_VALUE:
                found_correct = True
                self.log(f"  [OK] {replacement} already set")
            else:
                experiments[i] = replacement
                changed = True
                self.log(f"  [UPDATE] {self.DESIRED_KEY}@{current_value} -> {replacement}")

        if not found_correct and replacement not in experiments:
            experiments.append(replacement)
            changed = True
            self.log(f"  [ADD] {replacement}")

        if not changed:
            return False

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would write to {state_file}")
            return True

        try:
            state_file.write_text(json.dumps(state_data, indent=4))
            self.log(f"  [WRITE] Updated {state_file}")
            return True
        except Exception as e:
            self.log(f"  [ERROR] Failed to write {state_file}: {e}")
            return False

    def patch_settings_file(self, config: AppConfig) -> bool:
        if not config.settings_file or not config.settings_key:
            return False

        settings_path = Path(config.settings_file).expanduser()

        if not settings_path.exists():
            self.log(f"  [SKIP] Settings file not found: {settings_path}")
            # Try to create it for Docker Desktop
            if "docker" in config.name.lower():
                try:
                    settings_path.parent.mkdir(parents=True, exist_ok=True)
                    settings_path.write_text("{}")
                    self.log(f"  [CREATE] Created empty settings file")
                except Exception:
                    return False
            else:
                return False

        try:
            content = settings_path.read_text().strip()
            if not content:
                content = "{}"
            settings_data = json.loads(content)
        except Exception as e:
            self.log(f"  [ERROR] Failed to parse {settings_path}: {e}")
            return False

        keys = config.settings_key.split(".")
        target = settings_data

        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        final_key = keys[-1]

        if "disable" in final_key.lower():
            desired_value = True
        else:
            desired_value = False

        current_value = target.get(final_key)

        if current_value == desired_value:
            self.log(f"  [OK] {config.settings_key} already set to {desired_value}")
            return False

        target[final_key] = desired_value

        if self.dry_run:
            self.log(f"  [DRY-RUN] Would set {config.settings_key}={desired_value}")
            return True

        try:
            settings_path.write_text(json.dumps(settings_data, indent=2))
            self.log(f"  [WRITE] Set {config.settings_key}={desired_value}")
            return True
        except Exception as e:
            self.log(f"  [ERROR] Failed to write {settings_path}: {e}")
            return False

    def patch_known_app(self, app_name: str, config: AppConfig, 
                        patch_executables: bool = False) -> str:
        # Check if app is installed first
        app_path = self.find_app_path(config)
        if not app_path:
            return "Not installed"

        print(f"\n{'='*60}")
        print(f"Patching: {app_name}")
        print(f"{'='*60}")

        if config.notes:
            print(f"  Note: {config.notes}")

        results = []

        # Try Local State patches
        for rel_path in config.local_state_paths:
            state_file = self.library / rel_path
            if self.patch_local_state(state_file, app_name):
                results.append("Local State patched")

        # Try settings file patch
        if config.settings_file:
            if self.patch_settings_file(config):
                results.append("Settings patched")

        # Patch executable if requested and needed
        if patch_executables and config.needs_executable_patch:
            exec_path = self.get_executable_from_app(app_path)
            if exec_path and self.is_already_patched(exec_path):
                results.append("Executable already patched")
            elif self.patch_executable(config):
                results.append("Executable patched")

        if not results:
            if config.needs_executable_patch and not patch_executables:
                return "⚠️  Needs --patch-executables flag"
            return "No changes needed"

        return ", ".join(results)

    def patch_all_known_apps(self, patch_executables: bool = False):
        for app_name, config in KNOWN_APPS.items():
            result = self.patch_known_app(app_name, config, patch_executables)
            if result != "Not installed":
                self.results[app_name] = result

    def restore_all_apps(self):
        for app_name, config in KNOWN_APPS.items():
            if config.needs_executable_patch:
                app_path = self.find_app_path(config)
                if not app_path:
                    continue
                    
                exec_path = self.get_executable_from_app(app_path)
                backup_path = exec_path.with_suffix(exec_path.suffix + BACKUP_SUFFIX) if exec_path else None
                
                if not backup_path or not backup_path.exists():
                    continue
                    
                print(f"\n{'='*60}")
                print(f"Restoring: {app_name}")
                print(f"{'='*60}")
                if self.restore_executable(config):
                    self.results[app_name] = "Restored"
                else:
                    self.results[app_name] = "Failed to restore"

    def list_detected_apps(self):
        print(f"\n{'='*60}")
        print("Detected Chromium/Electron Apps")
        print(f"{'='*60}\n")

        installed_count = 0
        patched_count = 0
        
        for app_name, config in sorted(KNOWN_APPS.items()):
            app_path = self.find_app_path(config)
            if not app_path:
                continue
                
            installed_count += 1

            patch_status = ""
            if config.needs_executable_patch:
                exec_path = self.get_executable_from_app(app_path)
                if exec_path and self.is_already_patched(exec_path):
                    patch_status = " ✅ [PATCHED]"
                    patched_count += 1
                else:
                    patch_status = " ❌ [NOT PATCHED]"
            else:
                patch_status = " ⚪ [Native app - no patch needed]"

            print(f"  {app_name}{patch_status}")
            if self.verbose:
                print(f"    Path: {app_path}")
                if config.notes:
                    print(f"    Note: {config.notes}")

        print(f"\n{'='*60}")
        print(f"Total installed: {installed_count}")
        print(f"Patched: {patched_count}")
        print(f"{'='*60}")

    def print_summary(self):
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")

        if self.dry_run:
            print("(DRY RUN - no changes were made)\n")

        if self.results:
            for app_name, result in sorted(self.results.items()):
                print(f"  {app_name}: {result}")
        else:
            print("  No apps were modified.")

        print(f"\n{'='*60}")
        print("Important Notes:")
        print(f"{'='*60}")
        print("""
1. If apps crash after patching, the code signing may have failed.
   Run manually for each app:
   sudo codesign --force --deep --sign - "/Applications/AppName.app"

2. To restore all apps to original state:
   python3 electron_patcher_oclp_full.py --restore

3. After app updates, you'll need to re-run this script.

4. For 1Password: Use the settings patch (no executable patch needed)
   Disable 'Hardware Acceleration' in 1Password Settings > Advanced

5. For Docker Desktop: The script patches settings-store.json
   to set disableHardwareAcceleration: true
""")


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Electron/Chromium patcher for OCLP systems",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be changed without modifying files")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--patch-executables", action="store_true",
                        help="Replace app executables with wrapper scripts")
    parser.add_argument("--restore", action="store_true",
                        help="Restore original executables from backups")
    parser.add_argument("--list-apps", action="store_true",
                        help="List detected Chromium/Electron apps")

    args = parser.parse_args()

    if sys.platform != "darwin":
        print("Error: This script is designed for macOS only.")
        return 1

    patcher = ElectronPatcher(dry_run=args.dry_run, verbose=args.verbose)

    if args.list_apps:
        patcher.list_detected_apps()
        return 0

    if args.restore:
        patcher.restore_all_apps()
        patcher.print_summary()
        return 0

    patcher.patch_all_known_apps(patch_executables=args.patch_executables)
    patcher.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
