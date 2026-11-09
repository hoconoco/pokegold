; mod: Prof. Elm trade evolution (after the 8th Johto badge, ProfElmScript calls this with callasm).
; Opens the party menu; a mon that evolves by trade (holding the required item, if any) evolves
; right here as if traded. wScriptVar = 1 when it evolved, 0 otherwise (cancelled / cannot evolve —
; a buzzer plays for a mon that cannot). No new text, so the Korean ROM port can use the same flow.
ElmTradeEvolution::
	xor a
	ld [wScriptVar], a
	farcall SelectMonFromParty
	ret c
	ld a, [wCurPartySpecies]
	cp EGG
	jr z, .cannot
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord
.loop
	ld a, BANK(EvosAttacksPointers)
	call GetFarByte
	inc hl
	and a
	jr z, .cannot
	cp EVOLVE_TRADE
	jr z, .trade
	cp EVOLVE_STAT
	jr nz, .next
	inc hl
.next
	inc hl
	inc hl
	jr .loop

.trade
	ld a, BANK(EvosAttacksPointers)
	call GetFarByte
	cp -1
	jr z, .evolve
	ld b, a
	push bc
	ld a, MON_ITEM
	call GetPartyParamLocation
	pop bc
	ld a, [hl]
	cp b
	jr nz, .cannot
.evolve
	ld a, LINK_TRADECENTER
	ld [wLinkMode], a
	farcall EvolvePokemon
	xor a
	ld [wLinkMode], a
	ld a, 1
	ld [wScriptVar], a
	ret

.cannot
	ld de, SFX_WRONG
	call PlaySFX
	jp WaitSFX
