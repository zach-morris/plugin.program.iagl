import xbmc, xbmcgui, xbmcvfs, xbmcaddon, xbmcplugin, re, os, shutil, json
from pathlib import Path
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache, check_and_close_notification, choose_image, get_post_dl_commands,MEDIA_SPECIAL_PATH,check_if_dir_exists,check_userdata_directory
from resources.lib.main import iagl_addon
iagl_addon_wizard = iagl_addon()

EMAIL_RE = '.+[@]\w+[.]\w+'
START_SOUND = MEDIA_SPECIAL_PATH%{'filename':'wizard_start.wav'}
POS_SOUND = MEDIA_SPECIAL_PATH%{'filename':'coin.wav'}
NEG_SOUND = MEDIA_SPECIAL_PATH%{'filename':'kick.wav'}
DONE_SOUND = MEDIA_SPECIAL_PATH%{'filename':'wizard_done.wav'}
DONE_SOUND2 = MEDIA_SPECIAL_PATH%{'filename':'wizard_done2.wav'}
CHOICE_ICON = MEDIA_SPECIAL_PATH%{'filename':'wizard_default_choice.png'}
SLOW_ICON = MEDIA_SPECIAL_PATH%{'filename':'wizard_slow_choice.png'}
SKIP_ICON = MEDIA_SPECIAL_PATH%{'filename':'wizard_skip_choice.png'}
RETROPLAYER_ICON = MEDIA_SPECIAL_PATH%{'filename':'retroplayer.png'}
RETROARCH_ICON = MEDIA_SPECIAL_PATH%{'filename':'retroarch.png'}
IAGL_ICON = MEDIA_SPECIAL_PATH%{'filename':'icon.png'}
CUSTOM_DL_ICON = MEDIA_SPECIAL_PATH%{'filename':'wizard_custom_download.png'}


EXT_DEFAULTS = {'32X_ZachMorris':['RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'3DO_ZachMorris':['RetroArch The 3DO Company - 3DO (Opera)','RetroArch The 3DO Company - 3DO (4DO)','RetroArch Opera (3DO)','RetroArch 4DO (3DO)'],'Amiga_Bestof':['RetroArch Commodore - Amiga (PUAE)','RetroArch PUAE (Amiga)','RetroArch UAE4ARM (Amiga)'],'Amiga_CD32_ZachMorris':['RetroArch Commodore - Amiga (PUAE)','RetroArch PUAE (Amiga)','RetroArch UAE4ARM (Amiga)'],'Amiga_ZachMorris':['RetroArch Commodore - Amiga (PUAE)','RetroArch PUAE (Amiga)','RetroArch UAE4ARM (Amiga)'],'Amstrad_CPC_ZachMorris':['RetroArch Amstrad - CPC (Caprice32)','RetroArch Amstrad - CPC (CrocoDS)','RetroArch CAP32 (Amstrad CPC)','RetroArch CrocoDS (Amstrad CPC)'],'Atari_2600_Bestof_ZachMorris':['RetroArch Atari - 2600 (Stella)','RetroArch Atari - 2600 (Stella 2014)','RetroArch Stella (Atari 2600)','RetroArch Stella 2014 (Atari 2600)'],'Atari_2600_ZachMorris':['RetroArch Atari - 2600 (Stella)','RetroArch Atari - 2600 (Stella 2014)','RetroArch Stella (Atari 2600)','RetroArch Stella 2014 (Atari 2600)'],'Atari_5200_ZachMorris':['RetroArch Atari - 5200 (Atari800)','RetroArch Atari800 (Atari 800/Atari 5200)'],'Atari_7800_ZachMorris':['RetroArch Atari - 7800 (ProSystem)','RetroArch ProSystem (Atari 7800)'],'Atari_800_ZachMorris':['RetroArch Atari - 5200 (Atari800)','RetroArch Atari800 (Atari 800/Atari 5200)'],'Atari_Jaguar_ZachMorris':['RetroArch Atari - Jaguar (Virtual Jaguar)','RetroArch Virtual Jaguar (Jaguar)'],'Atari_Lynx_ZachMorris':['RetroArch Atari - Lynx (Beetle Lynx)','RetroArch Atari - Lynx (Handy)','RetroArch Mednafen Lynx (Lynx)','RetroArch Handy (Lynx)'],'Atari_ST_ZachMorris':['RetroArch Atari - ST/STE/TT/Falcon (Hatari)','RetroArch Hatari (Atari ST/STE/TT/Falcon)'],'Atomiswave_ZachMorris':['RetroArch Sega - Dreamcast/NAOMI (Flycast)','Retroarch FlyCast (Dreamcast/Naomi)','Retroarch FlyCast GLES2 (Dreamcast/Naomi)'],'C64_ZachMorris':['RetroArch Commodore - C64 (VICE x64, fast)','RetroArch Commodore - C64 (Frodo)','RetroArch VICE C64 (C64)','RetroArch Frodo (C64)'],'CDI_ZachMorris':['RetroArch Arcade (MAME - Current)','RetroArch Multi (MESS 2015)','RetroArch MAME (Arcade Latest)','RetroArch MESS 2014 (MESS 0.160)'],'FM_Towns_ZachMorris':['RetroArch Arcade (MAME - Current)','RetroArch Multi (MESS 2015)','RetroArch MAME (Arcade Latest)','RetroArch MESS 2014 (MESS 0.160)'],'CannonBall_ZachMorris':['RetroArch Cannonball','RetroArch CannonBall (Standalone Game)'],'Cavestory_Lefty420':['RetroArch Cave Story (NXEngine)','RetroArch CaveStory (NXEngine)'],'Colecovision_ZachMorris':['RetroArch MSX/SVI/ColecoVision/SG-1000 (blueMSX)','RetroArch Sega - MS/GG (SMS Plus GX)','RetroArch BlueMSX (MSX)','RetroArch SMS Plus GX (GG/SMS)'],'Dinothawr_Lefty420':['RetroArch Dinothawr','RetroArch Dinothawr (Standalone Game)'],'Doom_Lefty420':['RetroArch Doom (PrBoom)','RetroArch PrBoom (Doom)'],'EasyRPG_ZachMorris':['RetroArch RPG Maker 2000/2003 (EasyRPG)','RetroArch EasyRPG (RPG Maker 2000/2003)'],'FBN_ZachMorris':['RetroArch Arcade (FinalBurn Neo)','RetroArch FB Neo (Arcade Latest)'],'GBA_Bestof_ZachMorris':['RetroArch Nintendo - Game Boy Advance (mGBA)','RetroArch Nintendo - Game Boy Advance (Beetle GBA)','RetroArch mGBA (GBA)','RetroArch Mednafen GBA (GBA)'],'GBA_Hacks_ZachMorris':['RetroArch Nintendo - Game Boy Advance (mGBA)','RetroArch Nintendo - Game Boy Advance (Beetle GBA)','RetroArch mGBA (GBA)','RetroArch Mednafen GBA (GBA)'],'GBA_Translations_ZachMorris':['RetroArch Nintendo - Game Boy Advance (mGBA)','RetroArch Nintendo - Game Boy Advance (Beetle GBA)','RetroArch mGBA (GBA)','RetroArch Mednafen GBA (GBA)'],'GBA_ZachMorris':['RetroArch Nintendo - Game Boy Advance (mGBA)','RetroArch Nintendo - Game Boy Advance (Beetle GBA)','RetroArch mGBA (GBA)','RetroArch Mednafen GBA (GBA)'],'GBC_Bestof_ZachMorris':['RetroArch Nintendo - Game Boy / Color (Gambatte)','RetroArch Nintendo - Game Boy / Color (fixGB)','RetroArch Gambatte (GB/GBC)','RetroArch fixGB (GB/GBC)'],'GBC_ZachMorris':['RetroArch Nintendo - Game Boy / Color (Gambatte)','RetroArch Nintendo - Game Boy / Color (fixGB)','RetroArch Gambatte (GB/GBC)','RetroArch fixGB (GB/GBC)'],'GB_Classic_Bestof_ZachMorris':['RetroArch Nintendo - Game Boy / Color (Gambatte)','RetroArch Nintendo - Game Boy / Color (fixGB)','RetroArch Gambatte (GB/GBC)','RetroArch fixGB (GB/GBC)'],'GB_Classic_ZachMorris':['RetroArch Nintendo - Game Boy / Color (Gambatte)','RetroArch Nintendo - Game Boy / Color (fixGB)','RetroArch Gambatte (GB/GBC)','RetroArch fixGB (GB/GBC)'],'GameCube_Bestof_ZachMorris':['RetroArch Nintendo - GameCube / Wii (Dolphin)','RetroArch Dolphin (Wii/Gamecube)','Dolphin (GameCube)'],'GameCube_ZachMorris':['RetroArch Nintendo - GameCube / Wii (Dolphin)','RetroArch Dolphin (Wii/Gamecube)','Dolphin (GameCube)'],'Game_Gear_Bestof_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/GG/SG-1000 (Gearsystem)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch Gearsystem (GG/SMS)'],'Game_Gear_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/GG/SG-1000 (Gearsystem)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch Gearsystem (GG/SMS)'],'Game_and_Watch_ZachMorris':['RetroArch Handheld Electronic (GW)','RetroArch Game and Watch (Game and Watch)'],'Genesis_Bestof_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'Genesis_Hacks_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'Genesis_Translations_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'Genesis_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'Intellivision_ZachMorris':['RetroArch Mattel - Intellivision (FreeIntv)','RetroArch FreeIntv (Intellivision)'],'Karaoke_ZachMorris':['RetroArch PocketCDG','RetroArch PocketCDG (CDG Music)'],'Karaoke_ZachMorris_1':['RetroArch PocketCDG','RetroArch PocketCDG (CDG Music)'],'Karaoke_ZachMorris_2':['RetroArch PocketCDG','RetroArch PocketCDG (CDG Music)'],'Karaoke_ZachMorris_3':['RetroArch PocketCDG','RetroArch PocketCDG (CDG Music)'],'Lutro_ZachMorris':['RetroArch Lua Engine (Lutro)','RetroArch Lua Engine (Lutro)'],'MAME_2003_Bestof_ZachMorris':['RetroArch Arcade (MAME 2003-Plus)','RetroArch Arcade (MAME 2003)','RetroArch MAME 2003 Plus (Arcade 0.78)','RetroArch MAME 2003 (Arcade 0.78)'],'MAME_2003_Plus_ZachMorris':['RetroArch Arcade (MAME 2003-Plus)','RetroArch Arcade (MAME 2003)','RetroArch MAME 2003 Plus (Arcade 0.78)','RetroArch MAME 2003 (Arcade 0.78)'],'MAME_2003_ZachMorris':['RetroArch Arcade (MAME 2003-Plus)','RetroArch Arcade (MAME 2003)','RetroArch MAME 2003 Plus (Arcade 0.78)','RetroArch MAME 2003 (Arcade 0.78)'],'MAME_Bestof_ZachMorris':['RetroArch Arcade (MAME - Current)','RetroArch Arcade (MAME 2015)','RetroArch MAME (Arcade Latest)','RetroArch MAME 2015 (Arcade 0.160)'],'MAME_2015_ZachMorris':['RetroArch Arcade (MAME 2015)','RetroArch MAME 2015 (Arcade 0.160)','RetroArch Arcade (MAME - Current)','RetroArch MAME (Arcade Latest)'],'MAME_ZachMorris':['RetroArch Arcade (MAME - Current)','RetroArch Arcade (MAME 2015)','RetroArch MAME (Arcade Latest)','RetroArch MAME 2015 (Arcade 0.160)'],'MSDOS_ZachMorris':['RetroArch DOS (DOSBox)','RetroArch DOS (DOSBox-core)','RetroArch DOSBox (DOS)','RetroArch DOSBOX-PURE (DOS)'],'MSX1_ZachMorris':['RetroArch MSX/SVI/ColecoVision/SG-1000 (blueMSX)','RetroArch Microsoft - MSX (fMSX)','RetroArch BlueMSX (MSX)','RetroArch fMSX (MSX)'],'MSX2_ZachMorris':['RetroArch MSX/SVI/ColecoVision/SG-1000 (blueMSX)','RetroArch Microsoft - MSX (fMSX)','RetroArch BlueMSX (MSX)','RetroArch fMSX (MSX)'],'Magnavox_O2_ZachMorris':['RetroArch Magnavox - Odyssey2 / Phillips Videopac+ (O2EM)','RetroArch O2EM (Odyssey2/Videopac)'],'Master_System_Bestof_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/GG/SG-1000 (Gearsystem)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch Gearsystem (GG/SMS)'],'Master_System_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/GG/SG-1000 (Gearsystem)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch Gearsystem (GG/SMS)'],'N64_Bestof_ZachMorris':['RetroArch Nintendo - Nintendo 64 (Mupen64Plus-Next)','RetroArch Nintendo - Nintendo 64 (ParaLLEl N64)','RetroArch ParaLLEl (N64)','RetroArch Mupen64Plus (N64)'],'N64_ZachMorris':['RetroArch Nintendo - Nintendo 64 (Mupen64Plus-Next)','RetroArch Nintendo - Nintendo 64 (ParaLLEl N64)','RetroArch ParaLLEl (N64)','RetroArch Mupen64Plus (N64)'],'NDS_ZachMorris':['RetroArch Nintendo - DS (DeSmuME)','RetroArch Nintendo - DS (melonDS)','RetroArch DeSmuME (NDS)','RetroArch melonDS (Nintendo DS)'],'NES_Bestof_ZachMorris':['RetroArch Nintendo - NES / Famicom (bnes)','RetroArch Nintendo - NES / Famicom (FCEUmm)','RetroArch Nestopia (NES)','RetroArch QuickNES (NES)'],'NES_Hacks_ZachMorris':['RetroArch Nintendo - NES / Famicom (bnes)','RetroArch Nintendo - NES / Famicom (FCEUmm)','RetroArch Nestopia (NES)','RetroArch QuickNES (NES)'],'NES_Translations_ZachMorris':['RetroArch Nintendo - NES / Famicom (bnes)','RetroArch Nintendo - NES / Famicom (FCEUmm)','RetroArch Nestopia (NES)','RetroArch QuickNES (NES)'],'NES_ZachMorris':['RetroArch Nintendo - NES / Famicom (bnes)','RetroArch Nintendo - NES / Famicom (FCEUmm)','RetroArch Nestopia (NES)','RetroArch QuickNES (NES)'],'NGPC_ZachMorris':['RetroArch SNK - Neo Geo Pocket / Color (Beetle NeoPop)','RetroArch SNK - Neo Geo Pocket / Color (RACE)','RetroArch Mednafen NeoPop (NGP/NGPC)','RetroArch RACE (NGP/NGPC)'],'Naomi1_ZachMorris':['RetroArch Sega - Dreamcast/NAOMI (Flycast)','Retroarch FlyCast (Dreamcast/Naomi)'],'Neo_Geo_CD_ZachMorris':['RetroArch Arcade (FinalBurn Neo)','RetroArch SNK - Neo Geo CD (NeoCD)','RetroArch FB Neo (Arcade Latest)','RetroArch NeoCD (Neo Geo CD)'],'OpenLara_ZachMorris':['RetroArch Tomb Raider (OpenLara)','RetroArch OpenLara (Tomb Raider)'],'PCE_CD_ZachMorris':['RetroArch NEC - PC Engine / SuperGrafx / CD (Beetle PCE)','RetroArch NEC - PC Engine / CD (Beetle PCE FAST)','RetroArch Mednafen PCE FAST (PCE/TG16)','RetroArch Mednafen PCE (PCE/TG16)'],'PCE_SuperGrafx_ZachMorris':['RetroArch NEC - PC Engine SuperGrafx (Beetle SuperGrafx)','RetroArch NEC - PC Engine / SuperGrafx / CD (Beetle PCE)','RetroArch Mednafen SuperGrafx (PCE SuperGrafx)','RetroArch Mednafen PCE FAST (PCE/TG16)'],'PS1_Bestof_ZachMorris':['RetroArch Sony - PlayStation (Beetle PSX HW)','RetroArch Sony - PlayStation (Beetle PSX)','RetroArch Mednafen PSX HW (PS1)','RetroArch Mednafen PSX (PS1)'],'PS1_ZachMorris':['RetroArch Sony - PlayStation (Beetle PSX HW)','RetroArch Sony - PlayStation (Beetle PSX)','RetroArch Mednafen PSX HW (PS1)','RetroArch Mednafen PSX (PS1)'],'PSP_ZachMorris':['RetroArch Sony - PlayStation Portable (PPSSPP)','RetroArch PPSSPP (PSP)','PPSSPP (PlayStation Portable)'],'PSP_Minis_ZachMorris':['RetroArch Sony - PlayStation Portable (PPSSPP)','RetroArch PPSSPP (PSP)','PPSSPP (PlayStation Portable)'],'Pokemon_Mini_ZachMorris':['RetroArch Nintendo - Pokemon Mini (PokeMini)','RetroArch Pokemon Mini (PokeMini)'],'PowderToy_ZachMorris':['RetroArch The Powder Toy','RetroArch PowderToy (Standalone Game)'],'Quake_Lefty420':['RetroArch Quake (TyrQuake)','RetroArch TyrQuake (Quake)'],'REminiscence_ZachMorris':['RetroArch Flashback (REminiscence)','RetroArch REminiscence (Standalone Game)'],'RickDangerous_ZachMorris':['RetroArch Rick Dangerous (XRick)','RetroArch XRick (Rick Dangerous)'],'SCUMMVM_Bestof_ZachMorris':['RetroArch ScummVM','RetroArch ScummVM (Various)'],'SCUMMVM_ZachMorris':['RetroArch ScummVM','RetroArch ScummVM (Various)'],'SNES_Bestof_ZachMorris':['RetroArch Nintendo - SNES / SFC (bsnes)','RetroArch Nintendo - SNES / SFC (Snes9x - Current)','RetroArch SNES9x (SNES)','RetroArch SNES Higan (SNES)'],'SNES_Hacks_ZachMorris':['RetroArch Nintendo - SNES / SFC (bsnes)','RetroArch Nintendo - SNES / SFC (Snes9x - Current)','RetroArch SNES9x (SNES)','RetroArch SNES Higan (SNES)'],'SNES_Translations_ZachMorris':['RetroArch Nintendo - SNES / SFC (bsnes)','RetroArch Nintendo - SNES / SFC (Snes9x - Current)','RetroArch SNES9x (SNES)','RetroArch SNES Higan (SNES)'],'SNES_ZachMorris':['RetroArch Nintendo - SNES / SFC (bsnes)','RetroArch Nintendo - SNES / SFC (Snes9x - Current)','RetroArch SNES9x (SNES)','RetroArch SNES Higan (SNES)'],'Satellaview_ZachMorris':['RetroArch Nintendo - SNES / SFC (bsnes)','RetroArch Nintendo - SNES / SFC (Snes9x - Current)','RetroArch SNES9x (SNES)','RetroArch SNES Higan (SNES)'],'Sega_CD_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/MD/CD/32X (PicoDrive)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch PicoDrive (SMS/Gen/Sega CD/32X)'],'Sega_Dreamcast_ZachMorris':['RetroArch Sega - Dreamcast/NAOMI (Flycast)','Retroarch FlyCast (Dreamcast/Naomi)'],'Sega_SG1000_ZachMorris':['RetroArch Sega - MS/GG/MD/CD (Genesis Plus GX)','RetroArch Sega - MS/GG (SMS Plus GX)','RetroArch Genesis Plus GX (GG/SMS/Gen/PICO/SG-1000)','RetroArch SMS Plus GX (GG/SMS)'],'Sega_Saturn_ZachMorris':['RetroArch Sega - Saturn (Beetle Saturn)','RetroArch Sega - Saturn (Yabause)','RetroArch Mednafen Saturn (Saturn)','RetroArch Yabasanshiro (Saturn)'],'Supervision_ZachMorris':['RetroArch Watara - Supervision (Potator)','RetroArch Potator (Watara Supervision)'],'TG16_Bestof_ZachMorris':['RetroArch NEC - PC Engine / SuperGrafx / CD (Beetle PCE)','RetroArch NEC - PC Engine / CD (Beetle PCE FAST)','RetroArch Mednafen PCE FAST (PCE/TG16)','RetroArch Mednafen PCE (PCE/TG16)'],'TG16_ZachMorris':['RetroArch NEC - PC Engine / SuperGrafx / CD (Beetle PCE)','RetroArch NEC - PC Engine / CD (Beetle PCE FAST)','RetroArch Mednafen PCE FAST (PCE/TG16)','RetroArch Mednafen PCE (PCE/TG16)'],'TIC80_ZachMorris':['RetroArch TIC-80','RetroArch TIC80 (TIC-80)'],'Vectrex_ZachMorris':['RetroArch GCE - Vectrex (vecx)','RetroArch VECX (Vectrex)'],'VirtualBoy_ZachMorris':['RetroArch Nintendo - Virtual Boy (Beetle VB)','RetroArch Mednafen VB (VirtualBoy)'],'Wii_Bestof_ZachMorris':['RetroArch Nintendo - GameCube / Wii (Dolphin)','RetroArch Dolphin (Wii/Gamecube)','Dolphin (GameCube)'],'Wii_ZachMorris':['RetroArch Nintendo - GameCube / Wii (Dolphin)','RetroArch Dolphin (Wii/Gamecube)','Dolphin (GameCube)'],'Win31_ZachMorris':['RetroArch DOS (DOSBox)','RetroArch DOS (DOSBox-core)','RetroArch DOSBox (DOS)','RetroArch DOSBOX-PURE (DOS)'],'Wolfenstein_ZachMorris':['RetroArch Wolfenstein 3D (ECWolf)','RetroArch ECWolf (Wolfenstein 3D)'],'Wonderswan_Color_ZachMorris':['RetroArch Bandai - WonderSwan/Color (Beetle Cygne)','RetroArch Mednafen Cygne (WonderSwan/WonderSwan Color)'],'Wonderswan_ZachMorris':['RetroArch Bandai - WonderSwan/Color (Beetle Cygne)','RetroArch Mednafen Cygne (WonderSwan/WonderSwan Color)'],'ZX_Spectrum_ZachMorris':['RetroArch Sinclair - ZX Spectrum (Fuse)','RetroArch FUSE (Spectrum)'],'eXoDOS_ZachMorris':['RetroArch DOS (DOSBox)','RetroArch DOS (DOSBox-core)','RetroArch DOSBox (DOS)','RetroArch DOSBOX-PURE (DOS)'],'LowResNX_ZachMorris':['RetroArch LowRes NX','RetroArch LowRes NX (Various)'],'Win3xO_ZachMorris':['RetroArch DOS (DOSBox)','RetroArch DOS (DOSBox-core)','RetroArch DOSBox (DOS)','RetroArch DOSBOX-PURE (DOS)'],'Win3xO_ZachMorris':['RetroArch DOS (DOSBox)','RetroArch DOS (DOSBox-core)','RetroArch DOSBox (DOS)','RetroArch DOSBOX-PURE (DOS)'],'Sharp_X68000_ZachMorris':['RetroArch Sharp - X68000 (PX68k)','RetroArch Sharp X68000 (X68000)'],'Amiga_CDTV_ZachMorris':['RetroArch Commodore - Amiga (PUAE)','RetroArch PUAE (Amiga)','RetroArch UAE4ARM (Amiga)'],'Sharp_X1_ZachMorris':['RetroArch Sharp X1 (X Millennium)','RetroArch X1 Millennium (Sharp X1)'],'PS2_ZachMorris':['RetroArch Sony - PlayStation 2 (PCSX2)','RetroArch Sony - PlayStation 2 (Play!)','RetroArch PCSX2 (PS2)','RetroArch Play (PS2)'],'Quake_2_ZachMorris':['RetroArch Quake II (vitaQuake 2)','RetroArch VitaQuake2 (Quake 2)']}
RP_DEFAULTS = {'32X_ZachMorris':['game.libretro.picodrive'],'3DO_ZachMorris':['game.libretro.opera'],'Amiga_Bestof':['game.libretro.uae','game.libretro.uae4arm'],'Amiga_CD32_ZachMorris':['game.libretro.uae','game.libretro.uae4arm'],'Amiga_ZachMorris':['game.libretro.uae','game.libretro.uae4arm'],'Amstrad_CPC_ZachMorris':['game.libretro.cap32','game.libretro.crocods'],'Atari_2600_Bestof_ZachMorris':['game.libretro.stella'],'Atari_2600_ZachMorris':['game.libretro.stella'],'Atari_5200_ZachMorris':['game.libretro.atari800'],'Atari_7800_ZachMorris':['game.libretro.prosystem'],'Atari_800_ZachMorris':['game.libretro.atari800'],'Atari_Jaguar_ZachMorris':['game.libretro.virtualjaguar'],'Atari_Lynx_ZachMorris':['game.libretro.beetle-lynx','game.libretro.handy'],'Atari_ST_ZachMorris':['game.libretro.hatari'],'Atomiswave_ZachMorris':['game.libretro.flycast'],'C64_ZachMorris':['game.libretro.vice','game.libretro.frodo'],'CDI_ZachMorris':['game.libretro.mame'],'CannonBall_ZachMorris':['game.libretro.cannonball'],'Cavestory_Lefty420':['game.libretro.nx'],'Colecovision_ZachMorris':['game.libretro.bluemsx','game.libretro.smsplus-gx'],'Dinothawr_Lefty420':['game.libretro.dinothawr'],'Doom_Lefty420':['game.libretro.prboom'],'EasyRPG_ZachMorris':['game.libretro.easyrpg'],'FBN_ZachMorris':['game.libretro.fbneo','game.libretro.fbalpha2012'],'GBA_Bestof_ZachMorris':['game.libretro.mgba','game.libretro.beetle-gba'],'GBA_Hacks_ZachMorris':['game.libretro.mgba','game.libretro.beetle-gba'],'GBA_Translations_ZachMorris':['game.libretro.mgba','game.libretro.beetle-gba'],'GBA_ZachMorris':['game.libretro.mgba','game.libretro.beetle-gba'],'GBC_Bestof_ZachMorris':['game.libretro.gambatte','game.libretro.tgbdual'],'GBC_ZachMorris':['game.libretro.gambatte','game.libretro.tgbdual'],'GB_Classic_Bestof_ZachMorris':['game.libretro.gambatte','game.libretro.tgbdual'],'GB_Classic_ZachMorris':['game.libretro.gambatte','game.libretro.tgbdual'],'GameCube_Bestof_ZachMorris':['game.libretro.dolphin'],'GameCube_ZachMorris':['game.libretro.dolphin'],'Game_Gear_Bestof_ZachMorris':['game.libretro.genplus','game.libretro.smsplus-gx'],'Game_Gear_ZachMorris':['game.libretro.genplus','game.libretro.smsplus-gx'],'Game_and_Watch_ZachMorris':['game.libretro.gw'],'Genesis_Bestof_ZachMorris':['game.libretro.genplus','game.libretro.picodrive'],'Genesis_Hacks_ZachMorris':['game.libretro.genplus','game.libretro.picodrive'],'Genesis_Translations_ZachMorris':['game.libretro.genplus','game.libretro.picodrive'],'Genesis_ZachMorris':['game.libretro.genplus','game.libretro.picodrive'],'Intellivision_ZachMorris':['game.libretro.freeintv'],'Karaoke_ZachMorris':['game.libretro.pocketcdg'],'Karaoke_ZachMorris_1':['game.libretro.pocketcdg'],'Karaoke_ZachMorris_2':['game.libretro.pocketcdg'],'Karaoke_ZachMorris_3':['game.libretro.pocketcdg'],'Lutro_ZachMorris':['game.libretro.lutro'],'MAME_2003_Bestof_ZachMorris':['game.libretro.mame2003_plus','game.libretro.mame2003'],'MAME_2003_Plus_ZachMorris':['game.libretro.mame2003_plus','game.libretro.mame2003'],'MAME_2003_ZachMorris':['game.libretro.mame2003_plus','game.libretro.mame2003'],'MAME_Bestof_ZachMorris':['game.libretro.mame','game.libretro.mame2015'],'MAME_ZachMorris':['game.libretro.mame','game.libretro.mame2015'],'MSDOS_ZachMorris':['game.libretro.dosbox','game.libretro.dosbox-pure'],'MSX1_ZachMorris':['game.libretro.bluemsx','game.libretro.fmsx'],'MSX2_ZachMorris':['game.libretro.bluemsx','game.libretro.fmsx'],'Magnavox_O2_ZachMorris':['game.libretro.o2em'],'Master_System_Bestof_ZachMorris':['game.libretro.genplus','game.libretro.smsplus-gx'],'Master_System_ZachMorris':['game.libretro.genplus','game.libretro.smsplus-gx'],'N64_Bestof_ZachMorris':['game.libretro.parallel_n64','game.libretro.mupen64plus-nx'],'N64_ZachMorris':['game.libretro.parallel_n64','game.libretro.mupen64plus-nx'],'NDS_ZachMorris':['game.libretro.desmume','game.libretro.melonds'],'NES_Bestof_ZachMorris':['game.libretro.bnes','game.libretro.fceumm'],'NES_Hacks_ZachMorris':['game.libretro.bnes','game.libretro.fceumm'],'NES_Translations_ZachMorris':['game.libretro.bnes','game.libretro.fceumm'],'NES_ZachMorris':['game.libretro.bnes','game.libretro.fceumm'],'NGPC_ZachMorris':['game.libretro.beetle-ngp','game.libretro.race'],'Naomi1_ZachMorris':['game.libretro.flycast'],'Neo_Geo_CD_ZachMorris':['game.libretro.fbneo'],'OpenLara_ZachMorris':['game.libretro.openlara'],'PCE_CD_ZachMorris':['game.libretro.beetle-pce-fast'],'PCE_SuperGrafx_ZachMorris':['game.libretro.beetle-pce-fast'],'PS1_Bestof_ZachMorris':['game.libretro.beetle-psx','game.libretro.pcsx-rearmed'],'PS1_ZachMorris':['game.libretro.beetle-psx','game.libretro.pcsx-rearmed'],'PSP_ZachMorris':['game.libretro.ppsspp'],'PSP_Minis_ZachMorris':['game.libretro.ppsspp'],'Pokemon_Mini_ZachMorris':['game.libretro.pokemini'],'PowderToy_ZachMorris':['game.libretro.thepowdertoy'],'Quake_Lefty420':['game.libretro.tyrquake'],'REminiscence_ZachMorris':['game.libretro.reminiscence'],'RickDangerous_ZachMorris':['game.libretro.xrick'],'SCUMMVM_Bestof_ZachMorris':['game.libretro.scummvm'],'SCUMMVM_ZachMorris':['game.libretro.scummvm'],'SNES_Bestof_ZachMorris':['game.libretro.snes9x','game.libretro.bsnes-mercury-balanced'],'SNES_Hacks_ZachMorris':['game.libretro.snes9x','game.libretro.bsnes-mercury-balanced'],'SNES_Translations_ZachMorris':['game.libretro.snes9x','game.libretro.bsnes-mercury-balanced'],'SNES_ZachMorris':['game.libretro.snes9x','game.libretro.bsnes-mercury-balanced'],'Satellaview_ZachMorris':['game.libretro.snes9x','game.libretro.bsnes-mercury-balanced'],'Sega_CD_ZachMorris':['game.libretro.genplus','game.libretro.picodrive'],'Sega_Dreamcast_ZachMorris':['game.libretro.flycast'],'Sega_SG1000_ZachMorris':['game.libretro.genplus','game.libretro.smsplus-gx'],'Sega_Saturn_ZachMorris':['game.libretro.beetle-saturn','game.libretro.yabause'],'Supervision_ZachMorris':['game.libretro.potator'],'TG16_Bestof_ZachMorris':['game.libretro.beetle-pce-fast'],'TG16_ZachMorris':['game.libretro.beetle-pce-fast'],'TIC80_ZachMorris':['game.libretro.tic-80'],'Vectrex_ZachMorris':['game.libretro.vecx'],'VirtualBoy_ZachMorris':['game.libretro.beetle-vb'],'Wii_Bestof_ZachMorris':['game.libretro.dolphin'],'Wii_ZachMorris':['game.libretro.dolphin'],'Win31_ZachMorris':['game.libretro.dosbox','game.libretro.dosbox-pure'],'Wolfenstein_ZachMorris':['game.libretro.ecwolf'],'Wonderswan_Color_ZachMorris':['game.libretro.beetle-wswan'],'Wonderswan_ZachMorris':['game.libretro.beetle-wswan'],'ZX_Spectrum_ZachMorris':['game.libretro.fuse'],'eXoDOS_ZachMorris':['game.libretro.dosbox','game.libretro.dosbox-pure'],'Win3xO_ZachMorris':['game.libretro.dosbox','game.libretro.dosbox-pure'],'Win3xO_ZachMorris':['game.libretro.dosbox','game.libretro.dosbox-pure'],'Sharp_X68000_ZachMorris':['game.libretro.px68k'],'Amiga_CDTV_ZachMorris':['game.libretro.uae','game.libretro.uae4arm'],'Sharp_X1_ZachMorris':['game.libretro.xmil'],'PS2_ZachMorris':['game.libretro.pcsx2'],'Quake_2_ZachMorris':['game.libretro.vitaquake2']}
# clear_mem_cache('iagl_script_started') #For testing
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Wizard script started', level=xbmc.LOGDEBUG)
	iagl_addon_wizard.handle.setSetting(id='iagl_run_wizard',value='false')
	wizard_settings = dict()
	current_dialog = xbmcgui.Dialog()
	xbmc.playSFX(START_SOUND,False)
	ok_ret = current_dialog.ok(loc_str(30005),loc_str(30382))
	if not (iagl_addon_wizard.handle.getSetting(id='iagl_setting_enable_login')=='0' and iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username') and iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_password') and re.match(EMAIL_RE,iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username'))):
		li1 = xbmcgui.ListItem(label=loc_str(30200),label2=loc_str(30657),offscreen=True)
		li1.setArt({'thumb':CHOICE_ICON})
		li2 = xbmcgui.ListItem(label=loc_str(30204),label2=loc_str(30385),offscreen=True)
		li2.setArt({'thumb':SKIP_ICON})
		wizard_settings['enter_credentials'] = current_dialog.select(loc_str(30383),[li1,li2],0,0,True) #Enter Creds: 0=Yes, 1=No
		if wizard_settings.get('enter_credentials')==0:
			xbmc.playSFX(POS_SOUND,False)
			if iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username'):
				wizard_settings['archive_org_email'] = current_dialog.input(heading=loc_str(30023),defaultt=iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username'))
			else:
				wizard_settings['archive_org_email'] = current_dialog.input(heading=loc_str(30023))
			if wizard_settings.get('archive_org_email') and re.match(EMAIL_RE,wizard_settings.get('archive_org_email')):
				wizard_settings['archive_org_password'] = current_dialog.input(heading=loc_str(30024),option=xbmcgui.ALPHANUM_HIDE_INPUT)
			else:
				xbmc.playSFX(NEG_SOUND,False)
				ok_ret = current_dialog.ok(loc_str(30005),loc_str(30384))
				if iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username'):
					wizard_settings['archive_org_email'] = current_dialog.input(heading=loc_str(30023),defaultt=iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_username'))
				else:
					wizard_settings['archive_org_email'] = current_dialog.input(heading=loc_str(30023))
				if iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_password'):
					wizard_settings['archive_org_password'] = current_dialog.input(heading=loc_str(30024),defaultt=iagl_addon_wizard.handle.getSetting(id='iagl_setting_ia_password'),option=xbmcgui.ALPHANUM_HIDE_INPUT)
				else:
					wizard_settings['archive_org_password'] = current_dialog.input(heading=loc_str(30024),option=xbmcgui.ALPHANUM_HIDE_INPUT)
		if wizard_settings.get('archive_org_email') and wizard_settings.get('archive_org_password') and re.match(EMAIL_RE,wizard_settings.get('archive_org_email')): 
			xbmc.log(msg='IAGL:  Wizard enabled login', level=xbmc.LOGDEBUG)
			iagl_addon_wizard.handle.setSetting(id='iagl_setting_enable_login',value='0')
			iagl_addon_wizard.handle.setSetting(id='iagl_setting_ia_username',value=wizard_settings.get('archive_org_email'))
			iagl_addon_wizard.handle.setSetting(id='iagl_setting_ia_password',value=wizard_settings.get('archive_org_password'))
		else:
			xbmc.log(msg='IAGL:  Wizard did not enable login', level=xbmc.LOGDEBUG)
			xbmc.playSFX(NEG_SOUND,False)
			iagl_addon_wizard.handle.setSetting(id='iagl_setting_enable_login',value='1')
			ok_ret = current_dialog.ok(loc_str(30005),loc_str(30385))
	else:
		xbmc.log(msg='IAGL:  Wizard found existing login settings', level=xbmc.LOGDEBUG)

	li1 = xbmcgui.ListItem(label=loc_str(30128),label2=loc_str(30655),offscreen=True)
	li1.setArt({'thumb':RETROPLAYER_ICON})
	li2 = xbmcgui.ListItem(label=loc_str(30363),label2=loc_str(30656),offscreen=True)
	li2.setArt({'thumb':RETROARCH_ICON})
	wizard_settings['wizard_launcher'] = current_dialog.select(loc_str(30333),[li1,li2],0,0,True) #Choose launch process:  0=Retroplayer, 1=External
	loop = True
	while loop:
		if wizard_settings.get('wizard_launcher')<0:
			if current_dialog.yesno(loc_str(30386),loc_str(30386)):
				loop = False
				break
			else:
				wizard_settings['wizard_launcher'] = current_dialog.select(loc_str(30333),[li1,li2],0,0,True) #Choose launch process:  0=Retroplayer, 1=External
		else:
			loop = False
			break
	launch_type = None
	if wizard_settings.get('wizard_launcher')==1:
	# if iagl_addon_wizard.handle.getSetting(id='iagl_wizard_launcher')=='0': #External
		launch_type = loc_str(30206)
		xbmc.log(msg='IAGL:  Wizard script running for external launching', level=xbmc.LOGDEBUG)
		options = [loc_str(30116),loc_str(30117),loc_str(30118),loc_str(30123),loc_str(30514),loc_str(30582)]
		if iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')=='0':
			loop = True
			while loop:
				wizard_settings['ext_env'] = current_dialog.select(loc_str(30025),options)
				if wizard_settings.get('ext_env') != -1:
					xbmc.log(msg='IAGL:  Wizard external environment set to %(env)s'%{'env':options[wizard_settings.get('ext_env')]}, level=xbmc.LOGDEBUG)
					iagl_addon_wizard.handle.setSetting(id='iagl_external_user_external_env',value=str(wizard_settings.get('ext_env')+1))
					loop = False
					break
				else:
					if current_dialog.yesno(loc_str(30386),loc_str(30386)):
						loop = False
		else:
			xbmc.log(msg='IAGL:  External environment already set to %(env)s'%{'env':options[int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env'))-1]}, level=xbmc.LOGDEBUG)
		if iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')!='0' and int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [1,2,3] and not iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch'):
			start_path = ''
			POSSIBLE_RA_LOCATIONS = [os.path.join('/Applications','RetroArch.app','Contents','MacOS','RetroArch'),os.path.join('usr','bin','retroarch'),os.path.join('usr','local','bin','retroarch'),os.path.join(os.path.expanduser('~'),'bin','retroarch'),os.path.join(os.path.expanduser('~'),'ra','usr','local','bin','retroarch'),os.path.join('var','lib','flatpak','app','org.libretro.RetroArch','current','active','files','bin','retroarch'),os.path.join('C:','Program Files (x86)','Retroarch','retroarch.exe'),os.path.join('C:','Program Files','Retroarch','retroarch.exe'),os.path.join('home','kodi','bin','retroarch'),os.path.join('opt','retropie','emulators','retroarch','bin','retroarch'),os.path.join('opt','retroarch','bin','retroarch')]
			try:
				POSSIBLE_RA_LOCATIONS = [shutil.which('retroarch')]+POSSIBLE_RA_LOCATIONS
			except:
				xbmc.log(msg='IAGL:  shutil which failed', level=xbmc.LOGDEBUG)
			if any([os.path.exists(x) for x in POSSIBLE_RA_LOCATIONS if x]):
				start_path = [x for x in POSSIBLE_RA_LOCATIONS if x and os.path.exists(x)][0]
			loop = True
			while loop:
				wizard_settings['ra_app_location'] = current_dialog.browse(type=1,heading=loc_str(30028),shares='',defaultt=start_path)
				if wizard_settings.get('ra_app_location') and os.path.exists(str(wizard_settings.get('ra_app_location'))):
					xbmc.log(msg='IAGL:  Wizard RA app location set to %(value)s'%{'value':wizard_settings.get('ra_app_location')}, level=xbmc.LOGDEBUG)
					iagl_addon_wizard.handle.setSetting(id='iagl_external_path_to_retroarch',value=str(wizard_settings.get('ra_app_location')))
					loop = False
					break
				else:
					if current_dialog.yesno(loc_str(30386),loc_str(30386)):
						loop = False
		elif iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')!='0' and int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [1,2,3] and iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch'):
			xbmc.log(msg='IAGL:  Retroarch app location already set to %(value)s'%{'value':iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch')}, level=xbmc.LOGDEBUG)
		if iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')!='0' and int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [1,2,3,4,5,6] and not iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch_cfg'):
			start_path = ''
			POSSIBLE_CFG_LOCATIONS = [os.path.join(os.path.expanduser('~'),'Library','Application Support','RetroArch','config','retroarch.cfg'),os.path.join('C:','Program Files (x86)','Retroarch','retroarch.cfg'),os.path.join('C:','Program Files','Retroarch','retroarch.cfg'),os.path.join(os.path.expanduser('~'),'.config','retroarch','retroarch.cfg'),os.path.join(os.path.expanduser('~'),'AppData','Roaming','RetroArch','retroarch.cfg'),os.path.join(os.path.expanduser('~'),'.var','app','org.libretro.RetroArch','config','retroarch','retroarch.cfg'),os.path.join('opt','retropie','configs','all','retroarch.cfg'),os.path.join('mnt','internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('data','data','com.retroarch','retroarch.cfg'),os.path.join('data','data','com.retroarch','files','retroarch.cfg'),os.path.join('mnt','internal_sd','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),os.path.join('data','user','0','com.retroarch.aarch64','retroarch.cfg'),os.path.join('data','user','0','com.retroarch.aarch64','files','retroarch.cfg'),os.path.join('mnt','internal_sd','Android','data','com.retroarch.ra32','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch.ra32','files','retroarch.cfg'),os.path.join('data','data','com.retroarch.ra32','retroarch.cfg'),os.path.join('data','data','com.retroarch.ra32','files','retroarch.cfg')]
			if any([os.path.exists(x) for x in POSSIBLE_CFG_LOCATIONS if x]):
				start_path = [x for x in POSSIBLE_CFG_LOCATIONS if x and os.path.exists(x)][0]
			loop = True
			while loop:
				wizard_settings['ra_cfg_location'] = current_dialog.browse(type=1,heading=loc_str(30030),shares='',defaultt=start_path)
				if wizard_settings.get('ra_cfg_location') and os.path.exists(str(wizard_settings.get('ra_cfg_location'))):
					xbmc.log(msg='IAGL:  Wizard RA CFG location set to %(value)s'%{'value':wizard_settings.get('ra_cfg_location')}, level=xbmc.LOGDEBUG)
					iagl_addon_wizard.handle.setSetting(id='iagl_external_path_to_retroarch_cfg',value=str(wizard_settings.get('ra_cfg_location')))
					loop = False
					break
				else:
					if current_dialog.yesno(loc_str(30386),loc_str(30386)):
						loop = False
		elif iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')!='0' and int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [1,2,3,4,5,6] and iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch_cfg'):
			xbmc.log(msg='IAGL:  Retroarch CFG location already set to %(value)s'%{'value':iagl_addon_wizard.handle.getSetting(id='iagl_external_path_to_retroarch_cfg')}, level=xbmc.LOGDEBUG)
		if int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [1,2,3]:
			if current_dialog.yesno(loc_str(30005),loc_str(30617)):
				iagl_addon_wizard.handle.setSetting(id='iagl_netplay_enable_netplay_launch',value='0')
				iagl_addon_wizard.handle.setSetting(id='iagl_netplay_show_netplay_lobby',value='0')
				wizard_settings['netplay_nickname'] = current_dialog.input(heading=loc_str(30040),defaultt=iagl_addon_wizard.handle.getSetting(id='iagl_netplay_nickname'))
				if wizard_settings.get('netplay_nickname'):
					iagl_addon_wizard.handle.setSetting(id='iagl_netplay_nickname',value=wizard_settings.get('netplay_nickname'))
			else:
				iagl_addon_wizard.handle.setSetting(id='iagl_netplay_enable_netplay_launch',value='1')
				iagl_addon_wizard.handle.setSetting(id='iagl_netplay_show_netplay_lobby',value='1')
		else:
			iagl_addon_wizard.handle.setSetting(id='iagl_netplay_enable_netplay_launch',value='1')
			iagl_addon_wizard.handle.setSetting(id='iagl_netplay_show_netplay_lobby',value='1')

		li1 = xbmcgui.ListItem(label=loc_str(30200),label2=loc_str(30658),offscreen=True)
		li1.setArt({'thumb':CHOICE_ICON})
		li2 = xbmcgui.ListItem(label=loc_str(30204),label2=loc_str(30659),offscreen=True)
		li2.setArt({'thumb':SKIP_ICON})
		yesno_ret = current_dialog.select(loc_str(30387),[li1,li2],0,0,True) #Choose default external emulators:  0=Yes, 1=No
		if yesno_ret == 0:
			wizard_settings['game_list'] = dict()
			iagl_addon_wizard = iagl_addon() #Reload settings based on wizard entries
			ext_commands = iagl_addon_wizard.get_ext_launch_cmds()
			if ext_commands:
				dp = xbmcgui.DialogProgress()
				dp.create(loc_str(30377),loc_str(30379))
				dp.update(0,loc_str(30379))
				# current_bg_dialog = xbmcgui.DialogProgressBG()
				# current_bg_dialog.create(loc_str(30377),loc_str(30379))
				for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
					if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden':
						current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
						game_list_id = current_fn.name.replace(current_fn.suffix,'')
						wizard_settings['game_list'][game_list_id] = dict()
						wizard_settings['game_list'][game_list_id]['success'] = False
						wizard_settings['game_list'][game_list_id]['command'] = None
						wizard_settings['game_list'][game_list_id]['command_name'] = None
						dp.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377)+'[CR]'+loc_str(30379))
						# current_bg_dialog.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377),loc_str(30379))
						if dp.iscanceled():
							xbmc.log(msg='IAGL:  User cancelled the wizard mid process', level=xbmc.LOGDEBUG)
							wizard_settings['game_list'][game_list_id]['success'] = False
							wizard_settings['game_list'][game_list_id]['command'] = None
							wizard_settings['game_list'][game_list_id]['command_name'] = None
							break
						if EXT_DEFAULTS.get(game_list_id) and any([any([x.get('@name')==y for y in EXT_DEFAULTS.get(game_list_id)]) for x in ext_commands if x and x.get('@name')]):
							current_command_name = next(iter([x for x in EXT_DEFAULTS.get(game_list_id) if x in [y.get('@name') for y in ext_commands] if x]),'none')
							if iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')!='0' and int(iagl_addon_wizard.handle.getSetting(id='iagl_external_user_external_env')) in [4,5,6] and iagl_addon_wizard.handle.getSetting(id='iagl_enable_android_startactivity') in ['true','enabled','0']:
								current_command = next(iter([x.get('activity') for x in ext_commands if x and x.get('@name') == current_command_name]),'none')
							else:
								current_command = next(iter([x.get('command') for x in ext_commands if x and x.get('@name') == current_command_name]),'none')
							if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_launcher',header_value='external',confirm_update=False):
								xbmc.log(msg='IAGL:  Wizard update launcher for game list %(value)s to External'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
								if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_ext_launch_cmd',header_value=current_command,confirm_update=False):
									xbmc.log(msg='IAGL:  Wizard update launch command for game list %(value)s to %(ext_command)s'%{'value':game_list_id,'ext_command':current_command}, level=xbmc.LOGDEBUG)
									wizard_settings['game_list'][game_list_id]['success'] = True
									wizard_settings['game_list'][game_list_id]['command'] = current_command
									wizard_settings['game_list'][game_list_id]['command_name'] = current_command_name
						else:
							xbmc.log(msg='IAGL:  Wizard did not find a default external launch command for %(value)s'%{'value':game_list_id}, level=xbmc.LOGERROR)
				dp.close()
				del dp
				# current_bg_dialog.close()
				# xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
				# check_and_close_notification(notification_id='extendedprogressdialog')
				# del current_bg_dialog
			else:
				ok_ret = current_dialog.ok(loc_str(30005),loc_str(30388))
		else:
			xbmc.log(msg='IAGL:  Wizard external launch commands were skipped', level=xbmc.LOGDEBUG)
		li1 = xbmcgui.ListItem(label=loc_str(30664),label2=loc_str(30665),offscreen=True)
		li1.setArt({'thumb':CHOICE_ICON})
		li2 = xbmcgui.ListItem(label=loc_str(30666),label2=loc_str(30667),offscreen=True)
		li2.setArt({'thumb':CUSTOM_DL_ICON})
		li3 = xbmcgui.ListItem(label=loc_str(30668),label2=loc_str(30669),offscreen=True)
		li3.setArt({'thumb':SLOW_ICON})
		li4 = xbmcgui.ListItem(label=loc_str(30662),label2=loc_str(30663),offscreen=True)
		li4.setArt({'thumb':SKIP_ICON})
		yesno_ret = current_dialog.select('Set Game File Save Location',[li1,li2,li3,li4],0,0,True) #0=Default DL location, 1=Auto Setup Folders in a Directory,2=Manually Choose a folder for each system type, skip
		if yesno_ret == 0:
			dp = xbmcgui.DialogProgress()
			dp.create(loc_str(30377),loc_str(30379))
			dp.update(0,loc_str(30379))
			for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
				if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden' and isinstance(hh.get('emu_description'),str):
					current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
					game_list_id = current_fn.name.replace(current_fn.suffix,'')
					if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_downloadpath',header_value='default',confirm_update=False):
						dp.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377)+'[CR]'+loc_str(30379))
						if dp.iscanceled():
							xbmc.log(msg='IAGL:  User cancelled the wizard mid process', level=xbmc.LOGDEBUG)
							break
						xbmc.log(msg='IAGL:  Wizard update download path for game list %(value)s to default'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
			dp.close()
			del dp
		elif yesno_ret == 1:
			wizard_settings['custom_dl_directory'] = current_dialog.browse(type=0,heading=loc_str(30660),shares='')
			if check_if_dir_exists(wizard_settings['custom_dl_directory']):
				dp = xbmcgui.DialogProgress()
				dp.create(loc_str(30377),loc_str(30379))
				dp.update(0,loc_str(30379))
				for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
					if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden' and isinstance(hh.get('emu_description'),str):
						current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
						game_list_id = current_fn.name.replace(current_fn.suffix,'')
						game_list_dir = check_userdata_directory(os.path.join(wizard_settings['custom_dl_directory'],hh.get('emu_description').replace('Karaoke 1930-1979','Karaoke').replace('Karaoke 1980-1999','Karaoke').replace('Karaoke 2000-Present','Karaoke').replace(' ','_').replace(',','')))
						if isinstance(game_list_dir,Path) or isinstance(game_list_dir,str):
							if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_downloadpath',header_value=str(game_list_dir),confirm_update=False):
								dp.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377)+'[CR]'+loc_str(30379))
								if dp.iscanceled():
									xbmc.log(msg='IAGL:  User cancelled the wizard mid process', level=xbmc.LOGDEBUG)
									break
								xbmc.log(msg='IAGL:  Wizard update download path for game list %(value)s to %(dlpath)s'%{'value':game_list_id,'dlpath':game_list_dir}, level=xbmc.LOGDEBUG)
								if not wizard_settings.get('game_list'):
									wizard_settings['game_list'] = dict()
								if isinstance(wizard_settings['game_list'].get(game_list_id),dict):
									wizard_settings['game_list'][game_list_id]['custom_dir'] = game_list_dir
								else:
									wizard_settings['game_list'][game_list_id] = dict()
									wizard_settings['game_list'][game_list_id]['custom_dir'] = game_list_dir
				dp.close()
				del dp
		elif yesno_ret == 2:
			dirs_to_set = dict()
			dirs_to_set['current_fn'] = list()
			dirs_to_set['game_list_id'] = list()
			dirs_to_set['game_list_dir'] = list()
			dirs_to_set['game_list_dir_set'] = list()
			for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
					if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden' and isinstance(hh.get('emu_description'),str):
						current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
						dirs_to_set['current_fn'].append(current_fn)
						dirs_to_set['current_fn'].append(current_fn.name.replace(current_fn.suffix,''))
						dirs_to_set['game_list_dir'].append(hh.get('emu_description').replace('Karaoke 1930-1979','Karaoke').replace('Karaoke 1980-1999','Karaoke').replace('Karaoke 2000-Present','Karaoke').replace(' ','_').replace(',',''))
						dirs_to_set['game_list_dir_set'].append(False)
			custom_dirs = dict()
			for gld in sorted(set(dirs_to_set.get('game_list_dir'))):
				current_custom_dir = current_dialog.browse(type=0,heading=loc_str(30661).format(gld),shares='')
				if check_if_dir_exists(current_custom_dir):
					custom_dirs[gld] = current_custom_dir
			for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
				if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden' and isinstance(hh.get('emu_description'),str):
					current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
					game_list_id = current_fn.name.replace(current_fn.suffix,'')
					game_list_dir = hh.get('emu_description').replace('Karaoke 1930-1979','Karaoke').replace('Karaoke 1980-1999','Karaoke').replace('Karaoke 2000-Present','Karaoke').replace(' ','_').replace(',','')
					if game_list_dir in custom_dirs.keys():
						if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_downloadpath',header_value=str(custom_dirs.get(game_list_dir)),confirm_update=False):
							xbmc.log(msg='IAGL:  Wizard update download path for game list %(value)s to %(dlpath)s'%{'value':game_list_id,'dlpath':custom_dirs.get(game_list_dir)}, level=xbmc.LOGDEBUG)
							if not wizard_settings.get('game_list'):
								wizard_settings['game_list'] = dict()
							if isinstance(wizard_settings['game_list'].get(game_list_id),dict):
								wizard_settings['game_list'][game_list_id]['custom_dir'] = str(custom_dirs.get(game_list_dir))
							else:
								wizard_settings['game_list'][game_list_id] = dict()
								wizard_settings['game_list'][game_list_id]['custom_dir'] = str(custom_dirs.get(game_list_dir))
		else:
			xbmc.log(msg='IAGL:  Wizard download path updates were skipped', level=xbmc.LOGDEBUG)

	elif wizard_settings.get('wizard_launcher')==0:
		launch_type = loc_str(30364)
		xbmc.log(msg='IAGL:  Wizard script running for Retroplayer launching', level=xbmc.LOGDEBUG)
		#Turn off netplay for Retroplayer setup for now
		iagl_addon_wizard.handle.setSetting(id='iagl_netplay_enable_netplay_launch',value='1')
		iagl_addon_wizard.handle.setSetting(id='iagl_netplay_show_netplay_lobby',value='1')
		# yesno_ret = current_dialog.yesnocustom(loc_str(30005),loc_str(30390),)
		li1 = xbmcgui.ListItem(label=loc_str(30389),label2=loc_str(30654),offscreen=True)
		li1.setArt({'thumb':CHOICE_ICON})
		li2 = xbmcgui.ListItem(label=loc_str(30650),label2=loc_str(30651),offscreen=True)
		li2.setArt({'thumb':SLOW_ICON})
		li3 = xbmcgui.ListItem(label=loc_str(30652),label2=loc_str(30653),offscreen=True)
		li3.setArt({'thumb':SKIP_ICON})
		yesno_ret = current_dialog.select(loc_str(30390),[li1,li2,li3],0,0,True) #0=Auto, 1=Yes install,2=No, skip
		if yesno_ret in [0,1]:
			wizard_settings['game_list'] = dict()
			iagl_addon_wizard = iagl_addon() #Reload settings based on wizard entries
		if yesno_ret == 1:
			addons_available = []
			try:
				json_query = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient", "enabled": true}, "id": "1"}'))
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error executing JSONRPC command.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
				json_query = None
			if json_query and json_query.get('result') and json_query.get('result').get('addons'):
				addons_available = sorted([x.get('addonid') for x in json_query.get('result').get('addons') if x and x.get('addonid')!='game.libretro'])
			# current_bg_dialog = xbmcgui.DialogProgressBG()
			# current_bg_dialog.create(loc_str(30377),loc_str(30379))
			dp = xbmcgui.DialogProgress()
			dp.create(loc_str(30377),loc_str(30379))
			# xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).setProperty('iagl_wizard_progress','true') #Keep track of which window this is
			dp.update(0,loc_str(30379))
			for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
				if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden':
					current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
					game_list_id = current_fn.name.replace(current_fn.suffix,'')
					wizard_settings['game_list'][game_list_id] = dict()
					wizard_settings['game_list'][game_list_id]['success'] = False
					wizard_settings['game_list'][game_list_id]['command'] = None
					wizard_settings['game_list'][game_list_id]['command_name'] = None
					dp.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377)+'[CR]'+loc_str(30379))
					if dp.iscanceled():
						xbmc.log(msg='IAGL:  User cancelled the wizard mid process', level=xbmc.LOGDEBUG)
						wizard_settings['game_list'][game_list_id]['success'] = False
						wizard_settings['game_list'][game_list_id]['command'] = None
						wizard_settings['game_list'][game_list_id]['command_name'] = None
						break
					# current_bg_dialog.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377),loc_str(30379))
					if RP_DEFAULTS.get(game_list_id):
						if not any([y in addons_available for y in [x for x in RP_DEFAULTS.get(game_list_id) if x] if y]):
							xbmc.log(msg='IAGL:  Wizard did not find a default addon available for %(value)s, attempting to install.'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
							for aa in RP_DEFAULTS.get(game_list_id):
								xbmc.log(msg='IAGL:  Start install for %(value)s'%{'value':aa}, level=xbmc.LOGDEBUG)
								xbmc.executebuiltin('InstallAddon(%(value)s)'%{'value':aa},True)
								xbmc.log(msg='IAGL:  Complete install execution for %(value)s'%{'value':aa}, level=xbmc.LOGDEBUG)
						if any([y in addons_available for y in [x for x in RP_DEFAULTS.get(game_list_id) if x] if y]):
							current_command = next(iter([y for y in [x for x in RP_DEFAULTS.get(game_list_id) if x] if y in addons_available]),'none')
							if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_launcher',header_value='retroplayer',confirm_update=False):
								xbmc.log(msg='IAGL:  Wizard update launcher for game list %(value)s to Retroplayer'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
								if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_default_addon',header_value=current_command,confirm_update=False):
									xbmc.log(msg='IAGL:  Wizard update default addon for game list %(value)s to %(ext_command)s'%{'value':game_list_id,'ext_command':current_command}, level=xbmc.LOGDEBUG)
									wizard_settings['game_list'][game_list_id]['success'] = True
									wizard_settings['game_list'][game_list_id]['command'] = current_command
									wizard_settings['game_list'][game_list_id]['command_name'] = xbmcaddon.Addon(id=current_command).getAddonInfo('name')
						else:
							xbmc.log(msg='IAGL:  Wizard could not install a default addon for %(value)s'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
					else:
						xbmc.log(msg='IAGL:  Wizard did not find a default addon for %(value)s'%{'value':game_list_id}, level=xbmc.LOGERROR)
			dp.close()
			del dp
			# current_bg_dialog.close()
			# xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
			# check_and_close_notification(notification_id='extendedprogressdialog')
			# del current_bg_dialog
		elif yesno_ret == 0: #Set all to Auto
			dp = xbmcgui.DialogProgress()
			dp.create(loc_str(30377),loc_str(30379))
			dp.update(0,loc_str(30379))
			# current_bg_dialog = xbmcgui.DialogProgressBG()
			# current_bg_dialog.create(loc_str(30377),loc_str(30379))
			for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
				if hh and hh.get('emu_visibility') and hh.get('emu_visibility') != 'hidden':
					current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
					game_list_id = current_fn.name.replace(current_fn.suffix,'')
					wizard_settings['game_list'][game_list_id] = dict()
					wizard_settings['game_list'][game_list_id]['success'] = False
					wizard_settings['game_list'][game_list_id]['command'] = None
					wizard_settings['game_list'][game_list_id]['command_name'] = None
					dp.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377)+'[CR]'+loc_str(30379))
					if dp.iscanceled():
						xbmc.log(msg='IAGL:  User cancelled the wizard mid process', level=xbmc.LOGDEBUG)
						wizard_settings['game_list'][game_list_id]['success'] = False
						wizard_settings['game_list'][game_list_id]['command'] = None
						wizard_settings['game_list'][game_list_id]['command_name'] = None
						break
					# current_bg_dialog.update(int(100*(ii+1)/(len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header'))+.001)),loc_str(30377),loc_str(30379))
					current_command = 'none'
					if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_launcher',header_value='retroplayer',confirm_update=False):
						xbmc.log(msg='IAGL:  Wizard update launcher for game list %(value)s to Retroplayer'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
						if iagl_addon_wizard.game_lists.update_game_list_header(game_list_id,header_key='emu_default_addon',header_value=current_command,confirm_update=False):
							xbmc.log(msg='IAGL:  Wizard update default addon for game list %(value)s to Auto'%{'value':game_list_id}, level=xbmc.LOGDEBUG)
							wizard_settings['game_list'][game_list_id]['success'] = True
							wizard_settings['game_list'][game_list_id]['command'] = current_command
							wizard_settings['game_list'][game_list_id]['command_name'] = loc_str(30338)
			dp.close()
			del dp
			# current_bg_dialog.close()
			# xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
			# check_and_close_notification(notification_id='extendedprogressdialog')
			# del current_bg_dialog
	if wizard_settings.get('game_list') and wizard_settings.get('game_list').keys() and all([wizard_settings.get('game_list').get(kk).get('success') for kk in wizard_settings.get('game_list').keys()]):
		xbmc.playSFX(DONE_SOUND,False)
		ok_ret = current_dialog.ok(loc_str(30005),loc_str(30590)%{'launch_type':launch_type})
	elif wizard_settings.get('game_list') and wizard_settings.get('game_list').keys() and any([wizard_settings.get('game_list').get(kk).get('success') for kk in wizard_settings.get('game_list').keys()]):
		xbmc.playSFX(DONE_SOUND,False)
		ok_ret = current_dialog.ok(loc_str(30005),loc_str(30591)%{'launch_type':launch_type})
	else:
		if isinstance(launch_type,str):
			xbmc.playSFX(DONE_SOUND2,False)
			ok_ret = current_dialog.ok(loc_str(30005),loc_str(30592)%{'launch_type':launch_type})

	#Clear list cache and directory cache given updates completed above
	iagl_addon_wizard.clear_list_cache_folder()
	clear_mem_cache('iagl_directory')

	#Skip for now, too slow in general
	# if current_dialog.yesno(loc_str(30007),loc_str(30391)): #Precache lists question
	# 	dp = xbmcgui.DialogProgress()
	# 	iagl_addon_wizard = iagl_addon() #Reload settings based on wizard entries
	# 	dp.create(loc_str(30377),loc_str(30379))
	# 	dp.update(0,loc_str(30379))
	# 	total_files = len(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files'))
	# 	continue_processing = True
	# 	for ii,current_fn in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')):
	# 		if continue_processing:
	# 			game_list_id = current_fn.name.replace(current_fn.suffix,'')
	# 			percent = int(100.0 * ii / (total_files + .001))
	# 			current_game_list = iagl_addon_wizard.game_lists.get_game_list(game_list_id)
	# 			dp.update(percent,loc_str(30392)%{'game_list':current_game_list.get('emu_name')})
	# 			if dp.iscanceled():
	# 				continue_processing = False
	# 				xbmc.log(msg='IAGL:  User cancelled pre-cache processing', level=xbmc.LOGDEBUG)
	# 				break
	# 			_ = iagl_addon_wizard.game_lists.get_games_from_cache(game_list_id=current_fn.name.replace(current_fn.suffix,''))
	# 	dp.close()
	# 	del dp

	if iagl_addon_wizard.handle.getSetting(id='iagl_wizard_launcher_report')=='0' and isinstance(launch_type,str):
		xbmc.log(msg='IAGL:  Generating Wizard Report', level=xbmc.LOGDEBUG)
		report_items = dict()
		report_items['label'] = list()
		report_items['art'] = list()
		report_items['info'] = list()
		report_items['label'].append('IAGL Wizard Report ([COLOR green]UPDATED[/COLOR], [COLOR red]NOT UPDATED[/COLOR], [COLOR dimgray]HIDDEN[/COLOR])')
		report_items['art'].append(None)
		report_items['info'].append(None)
		if wizard_settings.get('wizard_launcher')=='0':
			report_items['label'].append('Settings updated for [B]Kodi Retroplayer[/B]')
			report_items['art'].append(None)
			report_items['info'].append(None)
			launch_type = 'Game Addon'
		else:
			report_items['label'].append('Settings updated for [B]External Launching[/B]')
			report_items['art'].append(None)
			report_items['info'].append(None)
			launch_type = 'External Launcher'
			
		iagl_addon_wizard = iagl_addon() #Reload settings based on wizard entries
		for ii,hh in enumerate(iagl_addon_wizard.directory.get('userdata').get('dat_files').get('header')):
			if hh:
				current_fn = iagl_addon_wizard.directory.get('userdata').get('dat_files').get('files')[ii]
				game_list_id = current_fn.name.replace(current_fn.suffix,'')
				current_launcher = 'Unknown'
				if wizard_settings.get('game_list') and wizard_settings.get('game_list').get(game_list_id) and wizard_settings.get('game_list').get(game_list_id).get('command_name'):
					current_launcher = wizard_settings.get('game_list').get(game_list_id).get('command_name')
				else:
					if iagl_addon_wizard.handle.getSetting(id='iagl_wizard_launcher_report')=='0':
						current_launcher = hh.get('emu_ext_launch_cmd')
					else:
						current_launcher = hh.get('emu_default_addon')
				current_color = 'red'
				current_status = 'NOT UPDATED'
				if hh.get('emu_visibility') and hh.get('emu_visibility') == 'hidden':
					current_color = 'dimgray'
					current_status = 'HIDDEN'
				elif wizard_settings.get('game_list') and wizard_settings.get('game_list').get(game_list_id) and wizard_settings.get('game_list').get(game_list_id).get('success'):
					current_color = 'green'
					current_status = 'UPDATED'
				elif wizard_settings.get('game_list') and wizard_settings.get('game_list').get(game_list_id) and wizard_settings.get('game_list').get(game_list_id).get('success')==False:
					current_color = 'red'
					current_status = 'NOT UPDATED'
				report_item = 'Game List: %(current_game_list)s, Status: [COLOR %(current_color)s]%(current_status)s[/COLOR], %(launch_type)s: %(current_launcher)s'%{'current_color':current_color,'current_status':current_status,'current_game_list':hh.get('emu_name'),'launch_type':launch_type,'current_launcher':current_launcher}
				report_items['label'].append(report_item)
				report_items['art'].append({'poster':choose_image(hh.get('emu_thumb')),'banner':choose_image(hh.get('emu_banner')),'fanart':choose_image(hh.get('emu_fanart')),'clearlogo':choose_image(hh.get('emu_logo')),'icon':choose_image(hh.get('emu_logo')),'thumb':choose_image(hh.get('emu_thumb'))})
				current_emu_postdlaction = get_post_dl_commands().get(hh.get('emu_postdlaction'))
				if not current_emu_postdlaction:
					current_emu_postdlaction = hh.get('emu_postdlaction')
				launch_command_string = ''
				download_path_string = loc_str(30361)
				current_header = loc_str(30362)%{'game_list_id':game_list_id}
				if hh.get('emu_launcher') == 'external':
					if hh.get('emu_ext_launch_cmd') == 'none':
						launch_command_string = '[COLOR FF12A0C7]%(elc)s:  [/COLOR]Not Set!'%{'elc':loc_str(30363)}
					else:
						launch_command_string = '[COLOR FF12A0C7]%(elc)s:  [/COLOR]%(lc)s'%{'elc':loc_str(30363),'lc':hh.get('emu_ext_launch_cmd')}
				if hh.get('emu_launcher') == 'retroplayer':
					if hh.get('emu_default_addon') == 'none':
						launch_command_string = '[COLOR FF12A0C7]%(rp)s:  [/COLOR]%(auto)s'%{'rp':loc_str(30364),'auto':loc_str(30338)}
					else:
						launch_command_string = '[COLOR FF12A0C7]%(rp)s:  [/COLOR]%(lc)s'%{'rp':loc_str(30364),'lc':hh.get('emu_default_addon')}
				if hh.get('emu_downloadpath') != 'default':
					download_path_string = hh.get('emu_downloadpath_resolved')
				current_text = '[B]%(md)s[/B][CR][COLOR FF12A0C7]%(gln)s:  [/COLOR]%(emu_name)s[CR][COLOR FF12A0C7]%(cat)s:  [/COLOR]%(emu_category)s[CR][COLOR FF12A0C7]%(platform_string)s:  [/COLOR]%(emu_description)s[CR][COLOR FF12A0C7]%(author_string)s:  [/COLOR]%(emu_author)s[CR][CR][B]%(dp)s[/B][CR][COLOR FF12A0C7]%(source)s:  [/COLOR]%(download_source)s[CR][COLOR FF12A0C7]%(dl)s:  [/COLOR]%(download_path_string)s[CR][COLOR FF12A0C7]%(pdlc)s:  [/COLOR]%(emu_postdlaction)s[CR][CR][B]%(lp)s[/B][CR][COLOR FF12A0C7]%(lw)s:  [/COLOR]%(emu_launcher)s[CR]%(launch_command_string)s'%{'emu_name':hh.get('emu_name'),'emu_category':hh.get('emu_category'),'emu_description':hh.get('emu_description'),'emu_author':hh.get('emu_author'),'download_source':hh.get('download_source'),'emu_postdlaction':current_emu_postdlaction,'emu_launcher':{'retroplayer':loc_str(30128),'external':loc_str(30003)}.get(hh.get('emu_launcher')),'launch_command_string':launch_command_string,'download_path_string':download_path_string,'platform_string':loc_str(30416),'author_string':loc_str(30419),'gln':loc_str(30365),'cat':loc_str(30415),'dp':loc_str(30366),'source':loc_str(30368),'dl':loc_str(30367),'pdlc':loc_str(30369),'lp':loc_str(30370),'lw':loc_str(30371),'md':loc_str(30372)}
				report_items['info'].append({'plot':current_text})
		set_mem_cache('iagl_wizard_results',report_items)
		xbmc.executebuiltin('ActivateWindow(10025,"plugin://plugin.program.iagl/wizard_report")')
	else:
		xbmc.log(msg='IAGL:  Wizard Report Skipped', level=xbmc.LOGDEBUG)		
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Wizard script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon_wizard, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache, check_and_close_notification, choose_image, get_post_dl_commands,MEDIA_SPECIAL_PATH,check_if_dir_exists,check_userdata_directory
