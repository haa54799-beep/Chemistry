#!/usr/bin/env python3
"""
classify_chapters.py — Chapter classification for CBSE Class 12 Chemistry
board-paper questions, using the OFFICIAL CBSE 2026-27 curriculum chapter list
as the authoritative reference.

Method: weighted concept-pattern scoring over the question's complete native
text (question stem + options + case-study passage + subparts + OR
alternatives). Patterns encode chemistry concepts, named reactions, reagents,
formulae and units — not single generic words. The chapter with the highest
score is the primary chapter; the score margin drives the confidence value.
"""

import re

# Official CBSE Class XII Chemistry (2026-27) units, in syllabus order.
CHAPTERS = [
    (1,  "Solutions"),
    (2,  "Electrochemistry"),
    (3,  "Chemical Kinetics"),
    (4,  "d and f Block Elements"),
    (5,  "Coordination Compounds"),
    (6,  "Haloalkanes and Haloarenes"),
    (7,  "Alcohols, Phenols and Ethers"),
    (8,  "Aldehydes, Ketones and Carboxylic Acids"),
    (9,  "Amines"),
    (10, "Biomolecules"),
]
CHAPTER_NAMES = {u: n for u, n in CHAPTERS}

# ---------------------------------------------------------------------------
# Concept patterns per chapter. (pattern, weight)
#   weight 3 : highly distinctive signal
#   weight 2 : strong signal
#   weight 1 : supporting signal
# Patterns are matched case-insensitively against the full question text.
# ---------------------------------------------------------------------------

_PATTERNS = {
1: [  # Solutions
    (r"raoult'?s law", 3),
    (r"henry'?s law", 3),
    (r"colligative", 3),
    (r"azeotrop", 3),
    (r"freezing point", 3),
    (r"boiling point of (a )?solution|boiling point of water|boiling point of the solution", 3),
    (r"vapour pressure", 2),
    (r"liquid and its vapour|vapour-?liquid equilibrium", 2),
    (r"antifreeze|ethylene glycol", 3),
    (r"non-?volatile solute", 2),
    (r"addition of \d+ mol of|\d+ mol of \w+.{0,10}litre of water", 4),
    (r"deviation from raoult", 3),
    (r"freezing point (depression|of)", 3),
    (r"depression (in )?freezing point|depression of freezing", 3),
    (r"boiling point elevation|elevation (in )?boiling point|elevation of boiling", 3),
    (r"osmotic pressure", 3),
    (r"osmosis|semi-?permeable|reverse osmosis", 3),
    (r"isotonic|hypertonic|hypotonic", 3),
    (r"mole fraction", 3),
    (r"molality|molal\b", 3),
    (r"molarity", 2),
    (r"\b0?\.\d+\s*M\b.{0,40}(glucose|urea|kcl|cacl|sucrose|solut)", 2),
    (r"abnormal (molar|molecular) mass|abnormal molar mass", 3),
    (r"van'?t hoff factor", 3),
    (r"dimeris|dimeriz|associat\w* of|dissociation of.{0,30}(in|solution)", 2),
    (r"vapour pressure of (liquid )?solution|lowering of vapour pressure", 3),
    (r"ideal (and )?non-?ideal solution|non-?ideal solution|ideal solution", 3),
    (r"intermolecular forces|intermolecular interactions", 2),
    (r"solubility of.{0,30}(gas|o2|co2|nh3)|solubility.{0,20}in water", 2),
    (r"bends|anoxia", 3),
    (r"sprinkling of salt|salt.{0,20}clearing the snow|de-?icing", 2),
    (r"k[bh]\b|kb\s*=\s*\d|ebullioscopic|ebullioscopy", 2),
    (r"k[fh]\b|cryoscopic|cryoscopy", 2),
    (r"relative lowering", 2),
    (r"concentration of solution|concentration of the solution", 1),
    (r"\bsolution\b.{0,30}(boil|freez|vapour|pressure)", 2),
],
2: [  # Electrochemistry
    (r"electrochemical cell|galvanic cell|voltaic cell|daniel cell", 3),
    (r"electrode potential|standard electrode potential", 3),
    (r"e\s*[°ºo]\s*(cell|mg|zn|cu|ag|fe|ni|cr|mn|co|cl|h)", 3),
    (r"e°|e\^0|emf|electromotive force", 3),
    (r"nernst", 3),
    (r"electrolysis|electrolytic cell", 3),
    (r"electrode[s]?\b", 2),
    (r"\banode\b|\bcathode\b", 2),
    (r"salt bridge|half-?cell", 2),
    (r"lead (storage )?battery|battery\b|dry cell|mercury cell|fuel cell", 3),
    (r"corrosion|rusting", 3),
    (r"conductivity|conductance|molar conductivity|specific conductivity", 3),
    (r"kohlrausch|λm|Λm|lambda.?m", 3),
    (r"faraday|96500|\bnF\b", 2),
    (r"δg\s*=|Δg\s*=|delta ?g.?\s*-?\s*nf|dg\s*=\s*-", 2),
    (r"deposit(ed|ion)? at (anode|cathode)|gas (is )?(released|liberated) at", 2),
    (r"(zn|cu|ag|mg|fe|ni|cr|mn|co|al|sn|pb)\s*\(?s?\)?\s*\|\s*\1?\w*\s*\|", 3),
    (r"\|\s*(cu|zn|ag|mg|fe|ni|cr|mn|co|al|sn|pb|h2|cl2|o2|pt)\s*\|", 2),
    (r"inert electrode|platinum electrode|pt electrode|graphite electrode", 2),
    (r"standard hydrogen electrode|she\b", 2),
    (r"cell reaction|cell notation|cell diagram", 2),
    (r"concentration cell", 3),
    (r"overpotential|discharge of.{0,20}ion", 1),
    (r"\|\|", 2),
    (r"e\s*[°ºo]\s*\w{0,6}\s*=\s*[-–]", 2),
],
3: [  # Chemical Kinetics
    (r"rate (of )?reaction|rate constant|rate law|rate equation", 3),
    (r"order of (the )?reaction|order of reaction|order for the given reaction|the order (for|of)", 3),
    (r"molecularity", 3),
    (r"first order|second order|zero order|pseudo.{0,5}first order", 3),
    (r"half.?life|t½|t1/2", 3),
    (r"integrated rate", 3),
    (r"arrhenius|activation energy", 3),
    (r"\bea\b|activation energy", 3),
    (r"collision theory", 3),
    (r"rate\s*=\s*k|rate = k|k\s*=\s*[\d.]", 3),
    (r"mol\s*l?\s*–?\s*1\s*s\s*–?\s*1|mol l-1 s-1|mol l−1 s−1|s-1\b|s–1\b|s−1", 2),
    (r"temperature dependence of.{0,20}rate|effect of temperature", 2),
    (r"\[r\]0|\[r\]₀|\[a\]0|concentration of reactant", 1),
    (r"slowest step|rate determining|rate-determining", 2),
    (r"complex reaction|composite reaction", 2),
    (r"graph.{0,20}(rate|concentration|\[r\])|(rate|concentration).{0,20}graph", 2),
    (r"log\s*\(?p|log p|log\s*\d", 1),
    (r"experimental (quantity|order)|order is (an )?experimental", 2),
],
4: [  # d and f Block Elements
    (r"transition (metal|element|ion)s?", 3),
    (r"d-?block|f-?block|d and f", 2),
    (r"lanthanoid|actinoid|lanthanide|actinide", 3),
    (r"lanthanoid contraction", 3),
    (r"permanganate|kmno4|k\s*2\s*cr\s*2\s*o\s*7|dichromate|chromate", 3),
    (r"interstitial compound|alloy\b", 2),
    (r"catalyst.{0,30}transition|transition.{0,30}catalyst", 3),
    (r"zr.{0,5}hf|hafnium|zirconium", 3),
    (r"melting point (of|than).{0,20}(cr|mn)|cr.{0,10}higher melting", 2),
    (r"(zn|cd|hg).{0,30}(not|are not).{0,20}transition|zinc, cadmium and mercury", 3),
    (r"oxidation states?.{0,30}(transition|actinoid|lanthanoid)|wide range of oxidation", 2),
    (r"sc\s*3\+|scandium|3d\s*series|4d|5d", 2),
    (r"colour.{0,20}(transition|ion)|coloured.{0,20}(ion|salt)|d-?d transition", 2),
    (r"magnetic (moment|property|behaviour).{0,30}(transition|ion)|bm\b|bohr magneton", 2),
    (r"e°\s*m\s*2\+|e°m2\+|m2\+/m|e\s*[°ºo]\s*\(?(cr|mn|fe|co|ni|cu|zn)", 2),
    (r"(cr|mn|fe|co|ni|cu)\s*2?\+?\s*/\s*(cr|mn|fe|co|ni|cu)\b", 1),
    (r"potassium (permanganate|dichromate)|acidic solution of potassium", 2),
    (r"noble gas configuration.{0,30}(sc|zn)|scandium", 2),
    (r"amalgam", 1),
    (r"standard electrode potential values", 1),
    (r"\[ar\]\s*3d|3d\s*\d\s*4s\s*\d|4s\s*\d\s*3d", 3),
    (r"electronic configuration of (cr|chromium|zn|zinc|cu|copper|transition)", 2),
    (r"ionization enthalpy|ionisation enthalpy", 2),
    (r"manganate|mn\s*o\s*4|mno4", 3),
    (r"unpaired electron", 2),
    (r"in alkaline medium", 2),
    (r"noble gas configuration", 2),
    (r"cr\s*2\s*o\s*7|cr\s*o\s*4|dichromate|chromate", 3),
],
5: [  # Coordination Compounds
    (r"coordination (compound|complex|number|entity)", 3),
    (r"central metal (atom|ion)", 3),
    (r"ligand", 3),
    (r"werner", 3),
    (r"secondary valency|primary valency|valence of co", 2),
    (r"coordination number", 3),
    (r"iupac name.{0,40}(coordination|\[)|name of the (following )?(coordination )?(compound|complex)", 3),
    (r"\[\s*(co|ni|fe|cr|mn|cu|zn|ag|pt|pd|rh|cd|hg|ti|v)\s*\(", 3),
    (r"ionisation isomer|linkage isomer|geometrical isomer|optical isomer|stereo.?isomer", 3),
    (r"chelate effect|chelate\b|chelating", 3),
    (r"crystal field|cft\b|valance bond theory|valence bond theory|vbt\b", 3),
    (r"hybridisation.{0,30}(complex|\[)|hybridization.{0,30}(complex|\[)", 2),
    (r"magnetic behaviour.{0,30}(complex|\[)|magnetic (moment|behaviour)", 2),
    (r"paramagnetic|diamagnetic", 2),
    (r"octahedral|tetrahedral|square planar|d2sp3|sp3d2", 2),
    (r"d-?orbital.{0,20}(split|energ)|splitting of (the )?d", 2),
    (r"monodentate|bidentate|polydentate|ambidentate", 3),
    (r"edta|ethylenediaminetetra", 2),
    (r"(coordination )?complex", 3),
    (r"tollen'?s?.{0,10}reagent.{0,30}(complex)|[a-z]{2}\d*\(nh\s*3\)\s*\d?", 2),
    (r"stability of (the )?complex|stability constant", 1),
    (r"nomenclature of (coordination|complex)", 3),
    (r"heteroleptic|homoleptic", 3),
    (r"vitamin b\s*12|vitamin b12", 2),
],
6: [  # Haloalkanes and Haloarenes
    (r"haloalkane|haloarene|alkyl halide|aryl halide", 3),
    (r"\bc\s*4\s*h\s*9\s*br\b|c\s*4\s*h\s*9\s*cl\b|c\s*6\s*h\s*5\s*cl\b|chlorobenzene|bromobenzene|iodobenzene", 3),
    (r"c-?x bond|carbon-?halogen bond", 2),
    (r"nucleophilic substitution|\bs\s*n\s*1\b|\bs\s*n\s*2\b|\bsn1\b(?!\s*\+)|\bsn2\b(?!\s*\+)", 3),
    (r"elimination reaction|dehydrohalogenation|β-?elimination|dehalogenation", 2),
    (r"wurtz|finkelstein|swarts reaction", 3),
    (r"chloroform|iodoform reaction|dichloromethane|carbon tetrachloride|ccl4", 2),
    (r"ddt|freon|polyhalogen", 2),
    (r"aqueous koh|alc\.?\s*koh|koh.{0,20}(aq)", 2),
    (r"racemisation|racemic|inversion of configuration|walden|optically active", 2),
    (r"enantiomer|chirality|chiral|stereoisomer", 2),
    (r"haloarenes? (less|are less) reactive|less reactive towards nucleophilic", 2),
    (r"preparation of (haloalkane|alkyl halide|aryl halide)|from alcohol.{0,20}(pcl|pbr|hi|hcl)", 2),
    (r"(ch3| c2h5|c6h5).{0,3}(br|cl|i)\b.{0,15}(koh|naoh|aq)", 2),
    (r"grignard", 1),
    (r"sandmeyer|gattermann", 1),
    (r"(alkyl|aryl) (chloride|bromide|iodide)", 3),
    (r"\b(chloro|bromo|iodo|fluoro)(methane|ethane|propane|butane|pentane|benzene|ethene|propene)\b", 3),
    (r"\d+[-\s](bromo|chloro|iodo)[-\s]", 2),
    (r"aqueous (potassium|sodium) (hydroxide|koh)|aqueous koh", 2),
    (r"markovnikov|anti-?markovnikov|peroxide effect", 2),
    (r"addition of h(x|br|cl) to|of h(x|br|cl).{0,20}(alkene|alkene)", 2),
    (r"na metal.{0,40}dry ether|wurtz reaction|\bwurtz\b", 3),
    (r"dry acetone|nai.{0,20}acetone|halogen exchange|finkelstein", 3),
    (r"\bch\s*3\s*(cl|br|i)\b|\bc\s*2\s*h\s*5\s*(cl|br|i)\b|\bc\s*6\s*h\s*5\s*(cl|br|i)\b", 2),
],
7: [  # Alcohols, Phenols and Ethers
    (r"\bphenol\b|phenolic", 3),
    (r"\balcohol\b|alcohols\b", 3),
    (r"(?<!dry )\bether\b", 3),
    (r"–oh\b|-oh group|hydroxyl|hydroxy", 2),
    (r"–or\b|alkoxy", 2),
    (r"c\s*2\s*h\s*5\s*oh|ethanol|methanol|c\s*h\s*3\s*oh", 2),
    (r"(propan|butan|pentan|methan|ethan|hexan|heptan|octan)\s*-?\s*\d?\s*-?\s*ol\b|methyl alcohol|ethyl alcohol", 3),
    (r"lucas (reagent|test)", 3),
    (r"aspirin|salicylic acid|acetylation of (phenol|salicyl)", 3),
    (r"nitrophenol|o-?nitrophenol|p-?nitrophenol|2, ?4, ?6-?trinitrophenol|picric acid", 3),
    (r"reimer|kolbe'?s|kolbe reaction|friedel.?crafts", 3),
    (r"cumene|isopropylbenzene", 2),
    (r"williamson", 3),
    (r"dehydration of (alcohol|ethanol)|ethanol.{0,10}(conc|h2so4|al2o3)", 2),
    (r"oxidation of (alcohol|ethanol|primary alcohol)", 2),
    (r"bronsted.{0,20}(acid|base).{0,30}alcohol|alcohol.{0,30}bronsted", 2),
    (r"glycerol|propane-?1, ?2, ?3-?triol|triol", 2),
    (r"ether(s)? (from|preparation)|preparation of ether", 2),
    (r"phenol.{0,20}(react|with|nitration)|nitration of phenol", 2),
    (r"–oh group in phenols directs|phenol.{0,60}direct|direct.{0,40}phenol|directs? (the )?incoming group", 2),
    (r"electrophilic substitution.{0,30}phenol|phenol.{0,20}electrophilic", 2),
    (r"acidity of phenol|phenol.{0,20}(acidic|more acidic)", 2),
    (r"ethoxy|methoxy|anisole|phenetole", 2),
    (r"(primary|secondary|tertiary) alcohol", 2),
    (r"cleavage of ether|ether.{0,30}\bhi\b|\bhi\b.{0,30}ether|ether.{0,20}(hi|hbr)", 2),
],
8: [  # Aldehydes, Ketones and Carboxylic Acids
    (r"aldehyde|ketone", 3),
    (r"carbonyl", 2),
    (r"carboxylic acid", 3),
    (r"–cho\b|-cho\b|–cooh|carboxyl", 2),
    (r"tollen'?s|fehling| benedict", 3),
    (r"iodoform test", 3),
    (r"cannizzaro|aldol|claisen|perkin|benzoin|rosenmund|hell.?volhard|hvz", 3),
    (r"2, ?4-?dnp|2, ?4-?dinitrophenyl|dinitrophenyl|hydrazone|oxime|semicarbazone|phenylhydrazone", 3),
    (r"benzoic acid|benzaldehyde|acetophenone|acetaldehyde|acetone|ethanoic acid|acetic acid", 3),
    (r"\b(ethanal|propanal|butanal|methanal|propanone|butanone|formaldehyde)\b", 3),
    (r"benzonitrile|ethanenitrile|nitrile", 2),
    (r"ethyl benzoate|esterification|ester\b", 2),
    (r"nucleophilic addition", 3),
    (r"hcn.{0,10}(addition|react)|addition of hcn|hcn ?\+? ?[a-z]", 2),
    (r"nahso3|sodium (bi)?sulphite", 2),
    (r"acidity of (carboxylic )?acid|acidic (nature|strength).{0,20}(acid|than)", 2),
    (r"alpha.{0,10}hydrogen|α-?hydrogen.{0,10}(acidic|aldehyde|ketone)", 2),
    (r"benzoic acid and ethyl benzoate|distinguish.{0,30}(acid|benzoic)", 2),
    (r"reduction of (aldehyde|ketone).{0,20}alcohol|aldehyde.{0,20}oxidation", 2),
    (r"carboxylic acids have higher boiling", 2),
    (r"sodium benzoate|\bbenzoate\b", 2),
    (r"decarboxylation|soda lime", 2),
    (r"acidic strengths|acidic strength|stronger (acid|and why)", 2),
    (r"distinguish between.{0,40}(aldehyde|ketone|acid)", 2),
    (r"methyl ketone", 2),
],
9: [  # Amines
    (r"\bamine\b|amines\b", 3),
    (r"–nh\s*2|nh\s*2 group|amino", 3),
    (r"aniline|phenylamine|benzenamine", 3),
    (r"hinsberg", 3),
    (r"diazonium|diazotisation|diazotization|benzenediazonium", 4),
    (r"from benzenediazonium|obtain.{0,40}diazonium", 3),
    (r"sandmeyer|coupling reaction|gattermann", 3),
    (r"gabriel.{0,15}(phthalimide|synthesis)", 3),
    (r"hofmann bromamide|bromamide degradation|naobr.{0,10}amide", 3),
    (r"carbylamine|isocyanide|isonitrile", 2),
    (r"carbylamine (reaction|test)|product of (the )?carbylamine", 8),
    (r"p\s*k\s*b\b|basicity of amine|basic nature of amine|stronger base than", 2),
    (r"(ch\s*3|c\s*6\s*h\s*5).{0,5}nh\s*2|aliphatic amine|aromatic amine", 3),
    (r"ammonium salt.{0,20}amine|amine.{0,20}mineral acid|mineral acid.{0,20}amine", 2),
    (r"nitration of aniline|acetylated before|acetylation of aniline", 2),
    (r"reduction of nitro(benzene| compound).{0,20}amine|nitro.{0,20}(aniline|amine)", 2),
    (r"ammonolysis", 2),
    (r"c\s*3\s*h\s*9\s*n|c\s*6\s*h\s*5\s*n\s*h\s*2", 2),
    (r"(primary|secondary|tertiary) amine", 2),
    (r"quaternary ammonium", 1),
    (r"benzonitrile|aniline to benzonitrile", 2),
    (r"c\s*6\s*h\s*5\s*so\s*2\s*cl|benzenesulphonyl|benzene sulphonyl|hinsberg", 3),
    (r"\(c\s*2\s*h\s*5\)\s*[23]?\s*n\s*h|\(c\s*2\s*h\s*5\)\s*3\s*n\b|c\s*2\s*h\s*5\s*n\s*h\s*2", 2),
    (r"basicities|basicity of|order of (decreasing|increasing) basic", 2),
    (r"gabriel (phthalimide )?synthesis", 4),
    (r"naobr|sodium hypobromite", 3),
    (r"\b\w*(yl|an|en)amine\b", 2),
    (r"(naobr|br\s*2.{0,20}koh|koh.{0,20}br\s*2).{0,40}amide|amide.{0,40}(naobr|br\s*2|bromine|koh)", 4),
    (r"reduction of (a )?nitrile|nitrile.{0,20}reduction|reduction of (ethanenitrile|propanenitrile|benzonitrile|cyanide)", 3),
    (r"lithium aluminium hydride|lialh\s*4", 1),
],
10: [  # Biomolecules
    (r"biomolecule", 3),
    (r"carbohydrate|glucose|fructose|sucrose|lactose|maltose|starch|cellulose", 3),
    (r"mono-?saccharide|di-?saccharide|poly-?saccharide", 3),
    (r"protein|enzyme|amino acid|peptide (linkage|bond)|glycosidic", 3),
    (r"nucleic acid|dna|rna|nucleotide|nucleoside", 3),
    (r"vitamin", 3),
    (r"hormone", 2),
    (r"gluconic acid|n-?hexane.{0,20}glucose|glucose.{0,20}(hi|br|hno)", 3),
    (r"osazone|oxime.{0,20}glucose|glucose.{0,20}oxime", 2),
    (r"essential (and )?non-?essential amino|amino acids", 2),
    (r"zwitterion|isoelectric", 2),
    (r"denaturation|denatured", 2),
    (r"mutarotation|anomer|α-?d-?glucose|α/β|alpha and beta", 2),
    (r"invert sugar|inversion of (sugar|cane)", 2),
    (r"hydrolysis of (sucrose|starch|carbohydrate)", 2),
    (r"d-?glucose|glucose.{0,20}(open chain|ring|structure)", 3),
    (r"aspartame|saccharin|artificial sweetener", 2),
    (r"polypeptide", 2),
],
}

# Patterns that indicate a DIFFERENT chapter strongly (used only to break
# near-ties in favour of the more central concept).
_DOMAIN_HINTS = {
    # (pattern, chapter_unit, weight) — extra evidence
    "electrolysis_of_aq": (r"electrolysis of aqueous", 2, 2),
    "electrolysis_generic": (r"electrolysis", 2, 2),
    "rate_pressure_data": (r"total pressure", 3, 1),
    "half_life_graph": (r"t½|t1/2|half.?life", 3, 3),
    "complex_formula": (r"\[\s*(co|ni|fe|cr|mn|cu|zn|ag|pt|pd|rh|cd|hg|ti|v)\s*\(", 5, 3),
    "transition_table": (r"e°.{0,3}m\s*2\+|e\s*[°ºo]\s*\(?(cr|mn|fe|co|ni|cu|zn)", 4, 2),
    "named_reaction_organic": (r"(cannizzaro|aldol|reimer|kolbe|tollen|fehling|iodoform|hinsberg|sandmeyer|gabriel|wurtz|finkelstein)", None, 0),
}


def _compile(unit):
    out = []
    for pat, w in _PATTERNS[unit]:
        out.append((re.compile(pat, re.IGNORECASE), w, pat))
    return out


_COMPILED = {u: _compile(u) for u, _ in CHAPTERS}


def normalize(text):
    """Normalize question text for pattern matching: collapse whitespace,
    unify dashes and quotes (the PDF uses U+2019, en/em dashes, minus signs).
    """
    t = (text.replace("’", "'").replace("‘", "'").replace("ʼ", "'")
             .replace("–", "-").replace("—", "-").replace("−", "-")
             .replace(" ", " "))
    return re.sub(r"\s+", " ", t)


def classify(text):
    """Classify a question's full text into a primary CBSE chapter.

    Returns dict: {unit, chapter, scores (all units), confidence, top_matches}
    """
    text = normalize(text)
    scores = {}
    matches = {}
    for u, _ in CHAPTERS:
        s = 0
        ms = []
        for rx, w, pat in _COMPILED[u]:
            if rx.search(text):
                s += w
                ms.append(pat)
        scores[u] = s
        matches[u] = ms
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    top_u, top_s = ranked[0]
    second_u, second_s = ranked[1] if len(ranked) > 1 else (None, 0)
    margin = top_s - second_s
    # confidence: high when a clear winner with several hits; lower on ties
    if top_s == 0:
        conf = 0.0
    else:
        base = min(0.99, 0.55 + 0.07 * len(matches[top_u]) + 0.05 * min(top_s, 12))
        if margin == 0:
            base -= 0.35
        elif margin == 1:
            base -= 0.15
        elif margin == 2:
            base -= 0.05
        conf = round(max(0.05, min(0.99, base)), 3)
    return {
        "unit": top_u,
        "chapter": CHAPTER_NAMES[top_u],
        "score": top_s,
        "scores": scores,
        "runner_up": CHAPTER_NAMES.get(second_u),
        "runner_up_score": second_s,
        "margin": margin,
        "confidence": conf,
        "top_matches": matches[top_u][:8],
    }


if __name__ == "__main__":
    import json, sys
    data = json.load(open(sys.argv[1]))
    for q in data:
        # combined text = native PDF text + OCR of the original-page crops.
        # OCR assists image-heavy questions (diagrams, structure-only options);
        # the native text remains the primary signal.
        text = q.get("combined_text") or q["native_text"]
        r = classify(text)
        r["text_source"] = "native+ocr" if q.get("combined_text") else "native"
        q["classification"] = r
    json.dump(data, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(q["classification"]["chapter"] for q in data))
