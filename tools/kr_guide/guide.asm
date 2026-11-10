; Guide menu for the Korean Gold/Silver mod (START menu '공략') — tools/kr_guide.py assembles this with
; rgbasm together with the generated kr_syms.inc (Korean ROM addresses) and guide_data.inc (texts, tables).
;
; - bank 4 (free tail): a 10-entry copy of the START menu item table (+ '공략' as item 9), the item's
;   function (FadeToMenu -> farcall GuideMain -> CloseSubmenu, like the trainer card) and two list hooks:
;   '공략' right after '가방', and '닫다' only while the menu has fewer than 8 items (8 fill the screen).
; - GUIDE_BANK: GuideMain — a full-screen list (이 맵 출현 / 전설·환상 / 다음 목표 / 도감 안내) drawn
;   like the options screen (Textbox + PlaceString, hBGMapMode 1), A opens a page, B goes back.
;   Korean glyphs are 8x16: PlaceString at tile row r draws rows r-1 and r, so text goes on rows 2, 5, 7, ... 15;
;   line break inside a string = $59 (kr_guide.py NEXT).

INCLUDE "kr_syms.inc"

DEF SCREEN_W EQU 20
MACRO hlcoord
	ld hl, wTilemap + SCREEN_W * (\2) + (\1)
ENDM

DEF PAD_A    EQU $01
DEF PAD_B    EQU $02
DEF PAD_UP   EQU $40
DEF PAD_DOWN EQU $80
DEF CURSOR_TILE EQU $ED     ; '▶' (single-byte charmap)
DEF BLANK_TILE  EQU $7F
DEF MENU_ROW    EQU 5
DEF CURSOR_COL  EQU 2

SECTION "KRGuideBank4", ROMX[BANK4_FREE], BANK[4]

GuideMenuItems::
	ORIGINAL_START_MENU_ITEMS          ; the 9 original entries (func, string, description)
	dw GuideItem, GuideItemString, GuideItemDesc

GuideItem:
	call FadeToMenu
	ld a, BANK(GuideMain)
	ld hl, GuideMain
	rst FarCall
	call CloseSubmenu
	ld a, 0                            ; back to the START menu (as the trainer card does)
	ret

GuidePackHook::                        ; replaces 'ld a, PACK / call AppendMenuList'
	ld a, 2
	call AppendMenuList
	ld a, 9
	jp AppendMenuList

GuideExitHook::                        ; replaces 'ld a, EXIT / call AppendMenuList'
	ld a, c
	cp 8
	ret nc
	ld a, 6
	jp AppendMenuList

GuideItemString:
	GUIDE_ITEM_STRING
GuideItemDesc:
	GUIDE_ITEM_DESC

SECTION "KRGuide", ROMX[$4000], BANK[GUIDE_BANK]

GuideMain::
	ldh a, [hInMenu]
	push af
	ld a, 1
	ldh [hInMenu], a
	call ClearBGPalettes
	ld c, 0
.redraw
	push bc
	call DrawMenu
	pop bc
	push bc
	call PutCursor
	call ShowScreen
	pop bc
.loop
	push bc
	call JoyTextDelay
	pop bc
	ldh a, [hJoyPressed]
	bit 1, a
	jr nz, .exit
	bit 0, a
	jr nz, .open
	bit 6, a
	jr nz, .up
	bit 7, a
	jr z, .loop
	inc c
	ld a, c
	cp NUM_PAGES
	jr c, .move
	ld c, 0
	jr .move
.up
	ld a, c
	and a
	jr nz, .dec
	ld c, NUM_PAGES
.dec
	dec c
.move
	push bc
	call ClearCursors
	pop bc
	push bc
	call PutCursor
	pop bc
	jr .loop
.open
	push bc
	ld a, c
	call OpenPage
	pop bc
	jr .redraw
.exit
	pop af
	ldh [hInMenu], a
	ret

ShowScreen:
	ld a, 1
	ldh [hBGMapMode], a
	call WaitBGMap
	ld b, SCGB_DIPLOMA
	call GetSGBLayout
	jp SetDefaultBGPAndOBP

Frame:
	hlcoord 0, 0
	ld b, 16
	ld c, 18
	jp Textbox

DrawMenu:
	call Frame
	hlcoord 2, 2
	ld de, TxtGuideTitle
	call PlaceString
	hlcoord CURSOR_COL + 2, MENU_ROW
	ld de, TxtMenuItems
	jp PlaceString

CursorAddr:                            ; c = row index -> hl
	hlcoord CURSOR_COL, MENU_ROW
	ld de, SCREEN_W * 2
	ld a, c
.next
	and a
	ret z
	add hl, de
	dec a
	jr .next

PutCursor:
	call CursorAddr
	ld [hl], CURSOR_TILE
	ret

ClearCursors:
	ld c, NUM_PAGES
.loop
	dec c
	push bc
	call CursorAddr
	ld [hl], BLANK_TILE
	pop bc
	ld a, c
	and a
	jr nz, .loop
	ret

WaitAB:
	call JoyTextDelay
	ldh a, [hJoyPressed]
	and PAD_A | PAD_B
	jr z, WaitAB
	ret

OpenPage:                              ; a = page
	and a
	jp z, PageWild
	ld de, TxtSoon
	push de
	call Frame
	pop de
	hlcoord 2, 2
	call PlaceString
	call WaitBGMap
	jp WaitAB

; 이 맵 출현: grass species of this time of day and water species of the current map (lists made at build time)
PageWild:
	call Frame
	hlcoord 2, 2
	ld de, TxtWildTitle
	call PlaceString
	ld a, [wMapGroup]
	ld b, a
	ld a, [wMapNumber]
	ld c, a
	ld hl, WildIndex
.find
	ld a, [hli]
	cp $ff
	jr z, .none
	cp b
	jr nz, .skip1
	ld a, [hli]
	cp c
	jr z, .found
	ld de, 8
	add hl, de
	jr .find
.skip1
	ld de, 9
	add hl, de
	jr .find
.none
	hlcoord 2, 5
	ld de, TxtNoWild
	call PlaceString
	jr .done
.found                                 ; hl -> dw morn, day, nite, water
	ld a, [wTimeOfDay]
	cp 3
	jr c, .time
	ld a, 2
.time
	push hl
	push af
	add a
	ld e, a
	ld d, 0
	ld hl, TimeLabels
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	hlcoord 2, 5
	call PlaceString
	pop af
	pop hl
	push hl
	add a
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	hlcoord 2, 7
	call PlaceString
	hlcoord 2, 13
	ld de, TxtWater
	call PlaceString
	pop hl
	ld de, 6
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
	hlcoord 2, 15
	call PlaceString
.done
	call WaitBGMap
	jp WaitAB

INCLUDE "guide_data.inc"
