; Kanto Pokémon in grass

KantoGrassWildMons:

	def_grass_wildmons DIGLETTS_CAVE
	db 4 percent, 2 percent, 8 percent ; encounter rates: morn/day/nite
	; morn
	db 15, DIGLETT
	db 17, DIGLETT
	db 19, DIGLETT
	db 13, DUNSPARCE
	db 19, FURRET
	db 24, SUDOWOODO
	db 29, DUGTRIO
	; day
	db 15, DIGLETT
	db 17, DIGLETT
	db 19, DIGLETT
	db 13, DUNSPARCE
	db 19, FURRET
	db 24, SUDOWOODO
	db 29, DUGTRIO
	; nite
	db 15, DIGLETT
	db 17, DIGLETT
	db 19, DIGLETT
	db 13, DUNSPARCE
	db 19, FURRET
	db 24, SUDOWOODO
	db 29, DUGTRIO
	end_grass_wildmons

	def_grass_wildmons MOUNT_MOON
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, SANDSHREW
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	; day
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, SANDSHREW
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	; nite
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, SANDSHREW
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	ELIF DEF(_SILVER)
	; morn
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, ZUBAT
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	; day
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, ZUBAT
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	; nite
	db 6, ZUBAT
	db 8, GEODUDE
	db 8, ZUBAT
	db 12, HOPPIP
	db 10, SNEASEL
	db 8, SNEASEL
	db 8, CLEFAIRY
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROCK_TUNNEL_1F
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	; morn
	db 10, CUBONE
	db 10, GEODUDE
	db 12, MACHOP
	db 8, IGGLYBUFF
	db 14, SNUBBULL
	db 13, SMOOCHUM
	db 13, CUBONE
	; day
	db 10, CUBONE
	db 10, GEODUDE
	db 12, MACHOP
	db 8, IGGLYBUFF
	db 14, SNUBBULL
	db 13, SMOOCHUM
	db 13, CUBONE
	; nite
	db 10, CUBONE
	db 10, GEODUDE
	db 12, MACHOP
	db 8, IGGLYBUFF
	db 14, SNUBBULL
	db 13, SMOOCHUM
	db 13, CUBONE
	end_grass_wildmons

	def_grass_wildmons ROCK_TUNNEL_B1F
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	; morn
	db 12, CUBONE
	db 12, GEODUDE
	db 16, ONIX
	db 10, HOPPIP
	db 14, SLUGMA
	db 14, SUNKERN
	db 14, KANGASKHAN
	; day
	db 12, CUBONE
	db 12, GEODUDE
	db 16, ONIX
	db 10, HOPPIP
	db 14, SLUGMA
	db 14, SUNKERN
	db 14, KANGASKHAN
	; nite
	db 12, CUBONE
	db 12, GEODUDE
	db 16, ONIX
	db 10, HOPPIP
	db 14, SLUGMA
	db 14, SUNKERN
	db 14, KANGASKHAN
	end_grass_wildmons

	def_grass_wildmons VICTORY_ROAD
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, URSARING
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	; day
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, URSARING
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	; nite
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, URSARING
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	ELIF DEF(_SILVER)
	; morn
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, DONPHAN
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	; day
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, DONPHAN
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	; nite
	db 32, GRAVELER
	db 32, GOLBAT
	db 33, DONPHAN
	db 34, GLIGAR
	db 36, MURKROW
	db 35, URSARING
	db 35, RHYHORN
	ENDC
	end_grass_wildmons

	def_grass_wildmons TOHJO_FALLS
	IF DEF(_GOLD)
	db 4 percent, 4 percent, 4 percent ; encounter rates: morn/day/nite
	ELIF DEF(_SILVER)
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	ENDC
	; morn
	db 22, ZUBAT
	db 22, RATICATE
	db 22, GOLBAT
	db 21, MURKROW
	db 20, IGGLYBUFF
	db 23, SLUGMA
	db 23, SLOWPOKE
	; day
	db 22, ZUBAT
	db 22, RATICATE
	db 22, GOLBAT
	db 21, MURKROW
	db 20, IGGLYBUFF
	db 23, SLUGMA
	db 23, SLOWPOKE
	; nite
	db 22, ZUBAT
	db 22, RATICATE
	db 22, GOLBAT
	db 21, MURKROW
	db 20, IGGLYBUFF
	db 23, SLUGMA
	db 23, SLOWPOKE
	end_grass_wildmons

	def_grass_wildmons ROUTE_1
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 2, PIDGEY
	db 2, RATTATA
	db 3, SENTRET
	db 3, CYNDAQUIL
	db 6, PICHU
	db 4, SUNKERN
	db 4, PIDGEY
	; day
	db 2, PIDGEY
	db 2, RATTATA
	db 3, SENTRET
	db 3, CYNDAQUIL
	db 6, PICHU
	db 4, SUNKERN
	db 4, PIDGEY
	; nite
	db 2, HOOTHOOT
	db 2, RATTATA
	db 3, RATTATA
	db 3, CYNDAQUIL
	db 6, PICHU
	db 4, SUNKERN
	db 4, HOOTHOOT
	end_grass_wildmons

	def_grass_wildmons ROUTE_2
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 3, CATERPIE
	db 3, PIDGEY
	db 5, METAPOD
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	; day
	db 3, CATERPIE
	db 3, PIDGEY
	db 5, METAPOD
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	; nite
	db 3, HOOTHOOT
	db 3, SPINARAK
	db 5, HOOTHOOT
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	ELIF DEF(_SILVER)
	; morn
	db 3, WEEDLE
	db 3, LEDYBA
	db 5, KAKUNA
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	; day
	db 3, WEEDLE
	db 3, PIDGEY
	db 5, KAKUNA
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	; nite
	db 3, HOOTHOOT
	db 3, HOOTHOOT
	db 5, HOOTHOOT
	db 7, ELEKID
	db 7, SMEARGLE
	db 4, CLEFFA
	db 4, PIKACHU
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_3
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 5, SPEAROW
	db 5, RATTATA
	db 8, SPEAROW
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, SPEAROW
	; day
	db 5, SPEAROW
	db 5, RATTATA
	db 8, SPEAROW
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, SPEAROW
	; nite
	db 5, RATTATA
	db 5, ZUBAT
	db 8, RATTATA
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, RATTATA
	ELIF DEF(_SILVER)
	; morn
	db 5, SPEAROW
	db 5, RATTATA
	db 8, EKANS
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, SPEAROW
	; day
	db 5, SPEAROW
	db 5, RATTATA
	db 8, EKANS
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, SPEAROW
	; nite
	db 5, RATTATA
	db 5, ZUBAT
	db 8, EKANS
	db 6, HOUNDOUR
	db 10, WOBBUFFET
	db 8, SNUBBULL
	db 8, RATTATA
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_4
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	IF DEF(_GOLD)
	; morn
	db 5, SPEAROW
	db 5, RATTATA
	db 8, SPEAROW
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, SPEAROW
	; day
	db 5, SPEAROW
	db 5, RATTATA
	db 8, SPEAROW
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, SPEAROW
	; nite
	db 5, SPEAROW
	db 5, ZUBAT
	db 8, RATTATA
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, RATTATA
	ELIF DEF(_SILVER)
	; morn
	db 5, SPEAROW
	db 5, RATTATA
	db 8, EKANS
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, SPEAROW
	; day
	db 5, SPEAROW
	db 5, RATTATA
	db 8, EKANS
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, SPEAROW
	; nite
	db 5, RATTATA
	db 5, ZUBAT
	db 8, EKANS
	db 6, MAGBY
	db 10, LARVITAR
	db 8, DELIBIRD
	db 8, RATTATA
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_5
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, PIDGEY
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	; day
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, PIDGEY
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	; nite
	db 13, ODDISH
	db 14, ODDISH
	db 13, BELLSPROUT
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	ELIF DEF(_SILVER)
	; morn
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, MEOWTH
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	; day
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, MEOWTH
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	; nite
	db 13, ODDISH
	db 14, MEOWTH
	db 13, BELLSPROUT
	db 15, LEDYBA
	db 12, SUDOWOODO
	db 14, MAGBY
	db 14, ABRA
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_6
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, PIDGEY
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	; day
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, PIDGEY
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	; nite
	db 13, ODDISH
	db 14, ODDISH
	db 13, BELLSPROUT
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	ELIF DEF(_SILVER)
	; morn
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, MEOWTH
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	; day
	db 13, PIDGEY
	db 13, BELLSPROUT
	db 14, MEOWTH
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	; nite
	db 13, ODDISH
	db 14, MEOWTH
	db 13, BELLSPROUT
	db 15, DELIBIRD
	db 12, SUDOWOODO
	db 14, PICHU
	db 14, ABRA
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_7
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 17, RATTATA
	db 17, SPEAROW
	db 18, GROWLITHE
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, RATTATA
	; day
	db 17, RATTATA
	db 17, SPEAROW
	db 18, GROWLITHE
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, GROWLITHE
	; nite
	db 17, RATTATA
	db 17, MURKROW
	db 18, GROWLITHE
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, HOUNDOUR
	ELIF DEF(_SILVER)
	; morn
	db 17, MEOWTH
	db 17, SPEAROW
	db 18, VULPIX
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, RATTATA
	; day
	db 17, MEOWTH
	db 17, SPEAROW
	db 18, VULPIX
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, VULPIX
	; nite
	db 17, MEOWTH
	db 17, MURKROW
	db 18, VULPIX
	db 19, SKIPLOOM
	db 19, MURKROW
	db 15, HOUNDOUR
	db 15, HOUNDOUR
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_8
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 17, PIDGEOTTO
	db 19, PIDGEOTTO
	db 15, ABRA
	db 18, SLUGMA
	db 17, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	; day
	db 17, PIDGEOTTO
	db 19, PIDGEOTTO
	db 15, ABRA
	db 18, SLUGMA
	db 17, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	; nite
	db 17, NOCTOWL
	db 20, HAUNTER
	db 15, ABRA
	db 19, SLUGMA
	db 18, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	ELIF DEF(_SILVER)
	; morn
	db 17, MEOWTH
	db 19, PIDGEOTTO
	db 15, ABRA
	db 18, SLUGMA
	db 17, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	; day
	db 17, MEOWTH
	db 19, PIDGEOTTO
	db 15, ABRA
	db 18, SLUGMA
	db 17, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	; nite
	db 17, MEOWTH
	db 20, HAUNTER
	db 15, ABRA
	db 19, SLUGMA
	db 18, SLUGMA
	db 15, FURRET
	db 15, KADABRA
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_9
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 13, MANKEY
	db 15, RATTATA
	db 13, SPEAROW
	db 15, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, PRIMEAPE
	; day
	db 13, MANKEY
	db 15, RATTATA
	db 13, SPEAROW
	db 15, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, PRIMEAPE
	; nite
	db 13, MANKEY
	db 15, RATTATA
	db 15, RATICATE
	db 13, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, PRIMEAPE
	ELIF DEF(_SILVER)
	; morn
	db 13, RATTATA
	db 15, SPEAROW
	db 13, SPEAROW
	db 15, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, RATICATE
	; day
	db 13, RATTATA
	db 15, SPEAROW
	db 13, SPEAROW
	db 15, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, RATICATE
	; nite
	db 13, RATTATA
	db 15, RATTATA
	db 15, RATICATE
	db 13, CLEFFA
	db 15, MURKROW
	db 15, MISDREAVUS
	db 15, RATICATE
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_10_NORTH
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 16, SPEAROW
	db 17, VOLTORB
	db 16, RATICATE
	db 18, QUILAVA
	db 16, MILTANK
	db 15, SHUCKLE
	db 15, ELECTABUZZ
	; day
	db 16, SPEAROW
	db 17, VOLTORB
	db 17, RATICATE
	db 18, QUILAVA
	db 15, MILTANK
	db 17, SHUCKLE
	db 17, ELECTABUZZ
	; nite
	db 16, QUAGSIRE
	db 17, VOLTORB
	db 16, RATICATE
	db 17, QUILAVA
	db 18, MILTANK
	db 15, SHUCKLE
	db 15, ELECTABUZZ
	end_grass_wildmons

	def_grass_wildmons ROUTE_11
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 14, DROWZEE
	db 15, RATTATA
	db 15, MAGNEMITE
	db 16, WOBBUFFET
	db 16, WOBBUFFET
	db 16, SMEARGLE
	db 16, HYPNO
	; day
	db 14, DROWZEE
	db 15, RATTATA
	db 15, MAGNEMITE
	db 16, WOBBUFFET
	db 16, WOBBUFFET
	db 16, SMEARGLE
	db 16, HYPNO
	; nite
	db 14, DROWZEE
	db 15, RATTATA
	db 15, MAGNEMITE
	db 16, WOBBUFFET
	db 16, WOBBUFFET
	db 16, SMEARGLE
	db 16, HYPNO
	end_grass_wildmons

	def_grass_wildmons ROUTE_13
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 22, MAGBY
	db 24, MISDREAVUS
	db 22, PICHU
	db 25, CHANSEY
	; day
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 22, MAGBY
	db 24, MISDREAVUS
	db 24, PICHU
	db 25, CHANSEY
	; nite
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, NOCTOWL
	db 22, MAGBY
	db 24, MISDREAVUS
	db 24, PICHU
	db 25, CHANSEY
	ELIF DEF(_SILVER)
	; morn
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 22, MAGBY
	db 24, MISDREAVUS
	db 22, PICHU
	db 25, CHANSEY
	; day
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 22, MAGBY
	db 24, MISDREAVUS
	db 24, PICHU
	db 25, CHANSEY
	; nite
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, NOCTOWL
	db 22, MAGBY
	db 24, MISDREAVUS
	db 24, PICHU
	db 25, CHANSEY
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_14
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 24, TOGEPI
	db 26, HITMONTOP
	db 22, GLIGAR
	db 25, CHANSEY
	; day
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 24, TOGEPI
	db 26, HITMONTOP
	db 26, GLIGAR
	db 25, CHANSEY
	; nite
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, NOCTOWL
	db 22, TOGEPI
	db 24, HITMONTOP
	db 24, GLIGAR
	db 25, CHANSEY
	ELIF DEF(_SILVER)
	; morn
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 24, TOGEPI
	db 26, HITMONTOP
	db 22, GLIGAR
	db 25, CHANSEY
	; day
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 24, TOGEPI
	db 26, HITMONTOP
	db 26, GLIGAR
	db 25, CHANSEY
	; nite
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, NOCTOWL
	db 22, TOGEPI
	db 24, HITMONTOP
	db 24, GLIGAR
	db 25, CHANSEY
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_15
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 22, SHUCKLE
	db 24, PINECO
	db 22, DELIBIRD
	db 25, CHANSEY
	; day
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, PIDGEOTTO
	db 22, SHUCKLE
	db 24, PINECO
	db 24, DELIBIRD
	db 25, CHANSEY
	; nite
	db 23, NIDORINA
	db 23, NIDORINO
	db 25, NOCTOWL
	db 22, SHUCKLE
	db 24, PINECO
	db 24, DELIBIRD
	db 25, CHANSEY
	ELIF DEF(_SILVER)
	; morn
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 22, SHUCKLE
	db 24, PINECO
	db 22, DELIBIRD
	db 25, CHANSEY
	; day
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, PIDGEOTTO
	db 22, SHUCKLE
	db 24, PINECO
	db 24, DELIBIRD
	db 25, CHANSEY
	; nite
	db 23, NIDORINO
	db 23, NIDORINA
	db 25, NOCTOWL
	db 22, SHUCKLE
	db 24, PINECO
	db 24, DELIBIRD
	db 25, CHANSEY
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_16
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 26, GRIMER
	db 27, FEAROW
	db 28, GRIMER
	db 29, CLEFFA
	db 27, ARIADOS
	db 30, SUNFLORA
	db 30, MUK
	; day
	db 26, GRIMER
	db 27, FEAROW
	db 28, GRIMER
	db 29, CLEFFA
	db 27, ARIADOS
	db 30, SUNFLORA
	db 30, MUK
	; nite
	db 26, GRIMER
	db 27, GRIMER
	db 28, GRIMER
	db 28, CLEFFA
	db 27, ARIADOS
	db 30, SUNFLORA
	db 30, MUK
	end_grass_wildmons

	def_grass_wildmons ROUTE_17
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 28, FEAROW
	db 27, GRIMER
	db 29, GRIMER
	db 30, SNEASEL
	db 29, LEDIAN
	db 32, STEELIX
	db 32, MUK
	; day
	db 28, FEAROW
	db 27, SLUGMA
	db 29, GRIMER
	db 30, SNEASEL
	db 25, LEDIAN
	db 32, STEELIX
	db 32, MUK
	; nite
	db 28, GRIMER
	db 27, GRIMER
	db 29, GRIMER
	db 30, SNEASEL
	db 29, LEDIAN
	db 32, STEELIX
	db 32, MUK
	end_grass_wildmons

	def_grass_wildmons ROUTE_18
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 26, GRIMER
	db 27, FEAROW
	db 28, GRIMER
	db 29, GIRAFARIG
	db 27, MISDREAVUS
	db 30, YANMA
	db 30, MUK
	; day
	db 26, GRIMER
	db 27, FEAROW
	db 28, GRIMER
	db 29, GIRAFARIG
	db 27, MISDREAVUS
	db 30, YANMA
	db 30, MUK
	; nite
	db 26, GRIMER
	db 27, GRIMER
	db 28, GRIMER
	db 28, GIRAFARIG
	db 27, MISDREAVUS
	db 30, YANMA
	db 30, MUK
	end_grass_wildmons

	def_grass_wildmons ROUTE_21
	db 6 percent, 6 percent, 6 percent ; encounter rates: morn/day/nite
	; morn
	db 30, TANGELA
	db 25, TANGELA
	db 35, TANGELA
	db 20, IGGLYBUFF
	db 30, SMEARGLE
	db 28, MURKROW
	db 28, MR__MIME
	; day
	db 30, TANGELA
	db 25, TANGELA
	db 35, TANGELA
	db 20, IGGLYBUFF
	db 28, SMEARGLE
	db 30, MURKROW
	db 30, MR__MIME
	; nite
	db 30, TANGELA
	db 25, TANGELA
	db 35, TANGELA
	db 20, IGGLYBUFF
	db 30, SMEARGLE
	db 28, MURKROW
	db 28, MR__MIME
	end_grass_wildmons

	def_grass_wildmons ROUTE_22
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 3, RATTATA
	db 3, SPEAROW
	db 5, SPEAROW
	db 4, MURKROW
	db 6, MILTANK
	db 7, AIPOM
	db 7, FEAROW
	; day
	db 3, RATTATA
	db 3, SPEAROW
	db 5, SPEAROW
	db 4, MURKROW
	db 6, MILTANK
	db 7, AIPOM
	db 7, FEAROW
	; nite
	db 3, RATTATA
	db 3, RATTATA
	db 5, RATTATA
	db 4, MURKROW
	db 6, MILTANK
	db 7, AIPOM
	db 7, RATTATA
	end_grass_wildmons

	def_grass_wildmons ROUTE_24
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 8, BELLSPROUT
	db 10, BELLSPROUT
	db 9, ABRA
	db 12, MAREEP
	db 8, SMOOCHUM
	db 14, MURKROW
	db 14, WEEPINBELL
	; day
	db 8, BELLSPROUT
	db 10, SUNKERN
	db 9, ABRA
	db 12, MAREEP
	db 10, SMOOCHUM
	db 14, MURKROW
	db 14, WEEPINBELL
	; nite
	db 8, VENONAT
	db 10, ODDISH
	db 9, ABRA
	db 13, MAREEP
	db 10, SMOOCHUM
	db 10, MURKROW
	db 10, VENOMOTH
	end_grass_wildmons

	def_grass_wildmons ROUTE_25
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	; morn
	db 8, PIDGEY
	db 10, BELLSPROUT
	db 8, VENONAT
	db 9, SNUBBULL
	db 10, PHANPY
	db 14, GLIGAR
	db 14, WEEPINBELL
	; day
	db 8, PIDGEY
	db 10, BELLSPROUT
	db 10, PIDGEY
	db 9, SNUBBULL
	db 12, PHANPY
	db 14, GLIGAR
	db 14, WEEPINBELL
	; nite
	db 8, VENONAT
	db 10, ODDISH
	db 10, VENOMOTH
	db 9, SNUBBULL
	db 14, PHANPY
	db 10, GLIGAR
	db 10, BELLSPROUT
	end_grass_wildmons

	def_grass_wildmons ROUTE_26
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 28, DODUO
	db 28, SANDSLASH
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 30, WOBBUFFET
	db 30, QUAGSIRE
	; day
	db 28, DODUO
	db 28, SANDSLASH
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 30, WOBBUFFET
	db 30, DODRIO
	; nite
	db 28, RATICATE
	db 28, SANDSLASH
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 32, WOBBUFFET
	db 32, QUAGSIRE
	ELIF DEF(_SILVER)
	; morn
	db 28, DODUO
	db 28, RATICATE
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 30, WOBBUFFET
	db 30, QUAGSIRE
	; day
	db 28, DODUO
	db 28, RATICATE
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 30, WOBBUFFET
	db 30, ARBOK
	; nite
	db 28, RATICATE
	db 28, RATICATE
	db 32, PONYTA
	db 30, PUPITAR
	db 30, STEELIX
	db 30, WOBBUFFET
	db 30, ARBOK
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_27
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 28, DODUO
	db 28, RATICATE
	db 30, DODUO
	db 28, YANMA
	db 32, NOCTOWL
	db 30, BLISSEY
	db 30, SANDSLASH
	; day
	db 28, DODUO
	db 28, RATICATE
	db 30, DODUO
	db 30, YANMA
	db 32, NOCTOWL
	db 30, BLISSEY
	db 30, SANDSLASH
	; nite
	db 28, QUAGSIRE
	db 28, RATICATE
	db 30, QUAGSIRE
	db 30, YANMA
	db 32, NOCTOWL
	db 30, BLISSEY
	db 30, SANDSLASH
	ELIF DEF(_SILVER)
	; morn
	db 28, DODUO
	db 28, ARBOK
	db 30, DODUO
	db 28, YANMA
	db 32, NOCTOWL
	db 30, BLISSEY
	db 30, DODRIO
	; day
	db 28, DODUO
	db 28, ARBOK
	db 30, DODUO
	db 30, YANMA
	db 32, NOCTOWL
	db 30, BLISSEY
	db 30, DODRIO
	; nite
	db 28, QUAGSIRE
	db 28, ARBOK
	db 30, QUAGSIRE
	db 30, YANMA
	db 32, NOCTOWL
	db 32, BLISSEY
	db 32, QUAGSIRE
	ENDC
	end_grass_wildmons

	def_grass_wildmons ROUTE_28
	db 10 percent, 10 percent, 10 percent ; encounter rates: morn/day/nite
	IF DEF(_GOLD)
	; morn
	db 39, TANGELA
	db 40, PONYTA
	db 40, URSARING
	db 42, STANTLER
	db 41, STEELIX
	db 43, STANTLER
	db 43, DODRIO
	; day
	db 39, TANGELA
	db 40, PONYTA
	db 40, URSARING
	db 42, STANTLER
	db 41, STEELIX
	db 43, STANTLER
	db 43, DODRIO
	; nite
	db 39, TANGELA
	db 40, PONYTA
	db 40, URSARING
	db 40, STANTLER
	db 42, STEELIX
	db 42, STANTLER
	db 42, RAPIDASH
	ELIF DEF(_SILVER)
	; morn
	db 39, TANGELA
	db 40, PONYTA
	db 40, DONPHAN
	db 42, STANTLER
	db 41, STEELIX
	db 43, STANTLER
	db 43, DODRIO
	; day
	db 39, TANGELA
	db 40, PONYTA
	db 40, DONPHAN
	db 42, STANTLER
	db 41, STEELIX
	db 43, STANTLER
	db 43, DODRIO
	; nite
	db 39, TANGELA
	db 40, PONYTA
	db 40, DONPHAN
	db 40, STANTLER
	db 42, STEELIX
	db 42, STANTLER
	db 42, RAPIDASH
	ENDC
	end_grass_wildmons

	db -1 ; end
