GET DATA /TYPE=TXT /FILE='surface_top.csv' /ENCODING='UTF8' /DELIMITERS="," /QUALIFIER='"'
  /ARRANGEMENT=DELIMITED /FIRSTCASE=2 /VARIABLES=
  effect F2.0
  rank F5.0
  score F8.5
  Causal_Chain_Integrity F8.5
  Empathy_Structure F8.5
  Family_System_Realism F8.5
  Manga_Craft_Fidelity F8.5
  Dread_Enforcement_Potential F8.5
  Counter_Stereotypical_Power F8.5
  node F3.0
  era F3.0
  economy F3.0
  pressure F3.0
  media F3.0
  family F3.0
  archetype F3.0
  .
VARIABLE LABELS node 'Diaspora node' era 'Era' economy 'Economy' pressure 'Systemic pressure' media 'Media frame' family 'Family system' archetype 'Archetype' effect 'Character-effect target' .
VALUE LABELS
  node 1 'US South>North migration' 2 'Harlem' 3 'Chicago' 4 'Detroit' 5 'South Central LA' 6 'Kingston JA' 7 'London (Brixton/Hackney)' 8 'Lagos' 9 'Accra' 10 'Sao Paulo' 11 'Salvador da Bahia' 12 'Port-au-Prince' 13 'Marseille' 14 'Toronto'
  /era 1 '1910s-20s Prohibition' 2 '1930s Depression' 3 '1940s-50s numbers/labor' 4 '1960s independence Africa' 5 '1970s blaxploitation/crack prelude' 6 '1980s Yardie/garrison' 7 '1990s crack/COINTELPRO aftermath' 8 '2000s-present transnational/digital'
  /economy 1 'bootlegging' 2 'policy/numbers' 3 'protection racket' 4 'labor racketeering' 5 'drug corridor' 6 'extortion/milicia' 7 'fraud/419' 8 'smuggling' 9 'informal security'
  /pressure 1 'redlining' 2 'police surveillance' 3 'political garrison patronage' 4 'extralegal violence' 5 'immigration law' 6 'media criminalization' 7 'intra-community class fracture'
  /media 1 'hostile tabloid' 2 'Black press counter-narrative' 3 'courtroom transcript' 4 'oral history' 5 'state intelligence file'
  /family 1 'matriarch-led' 2 'sibling split' 3 'migration-separated' 4 'chosen family' 5 'dynastic' 6 'estranged-return'
  /archetype 1 'ethical rebel loner' 2 'strategist' 3 'enforcer' 4 'diplomat' 5 'self-defense figure' 6 'informant' 7 'heir'
  /effect 1 'humanized' 2 'dreaded' 3 'pivot'
  .
EXECUTE.
