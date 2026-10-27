"""MUSE-GM Module 2 - exhaustive enumeration of the 8-dimension space (4,445,280 combos).
Objective = hand-encoded rubric (0..1 per component). NOT measured data; every table below is an editorial judgment.
"""
import numpy as np, json, hashlib, itertools, sys

NODES=["US South>North migration","Harlem","Chicago","Detroit","South Central LA","Kingston JA","London (Brixton/Hackney)","Lagos","Accra","Sao Paulo","Salvador da Bahia","Port-au-Prince","Marseille","Toronto"]
ERAS=["1910s-20s Prohibition","1930s Depression","1940s-50s numbers/labor","1960s independence Africa","1970s blaxploitation/crack prelude","1980s Yardie/garrison","1990s crack/COINTELPRO aftermath","2000s-present transnational/digital"]
ECON=["bootlegging","policy/numbers","protection racket","labor racketeering","drug corridor","extortion/milicia","fraud/419","smuggling","informal security"]
PRES=["redlining","police surveillance","political garrison patronage","extralegal violence","immigration law","media criminalization","intra-community class fracture"]
MEDIA=["hostile tabloid","Black press counter-narrative","courtroom transcript","oral history","state intelligence file"]
FAM=["matriarch-led","sibling split","migration-separated","chosen family","dynastic","estranged-return"]
ARCH=["ethical rebel loner","strategist","enforcer","diplomat","self-defense figure","informant","heir"]
EFF=["humanized","dreaded","pivot"]
DIMS=[NODES,ERAS,ECON,PRES,MEDIA,FAM,ARCH,EFF]
SHAPE=tuple(len(d) for d in DIMS)

NE=np.array([ # node x era plausibility
[1,1,1,.6,.3,.15,.15,.1],        # usmig
[1,1,1,.4,.8,.6,.8,.5],          # harlem
[1,1,.8,.4,.8,.8,.8,.7],         # chicago
[1,.8,.8,.5,.9,.8,.8,.6],        # detroit
[.1,.3,.6,.5,.8,1,1,.7],         # sc LA
[.2,.3,.5,.6,1,1,.7,.6],         # kingston
[.2,.3,.6,.5,.9,1,.8,.7],        # london
[.3,.4,.5,1,.8,.9,.9,1],         # lagos
[.3,.4,.5,1,.7,.7,.6,.6],        # accra
[.2,.3,.4,.3,.7,.8,.9,1],        # sao paulo
[.3,.4,.5,.3,.6,.6,.7,.8],       # salvador
[.5,.5,.5,.6,.6,.6,.8,.8],       # port-au-prince
[.3,.4,.6,.4,.6,.6,.7,.8],       # marseille
[.1,.1,.2,.3,.4,.7,.8,.9]])      # toronto
NEC=np.array([ # node x economy: boot,policy,prot,labor,drug,milicia,419,smug,infsec
[1,.9,.6,.8,.3,.1,.1,.5,.5],[1,1,.7,.6,.9,.1,.2,.5,.5],[1,1,.8,.8,.9,.1,.2,.5,.5],[.9,.8,.7,.8,1,.1,.2,.7,.5],
[.1,.3,.7,.4,1,.2,.2,.6,.6],[.2,.5,1,.3,1,.4,.3,.8,.8],[.2,.3,.8,.4,.9,.1,.5,.8,.7],[.3,.3,.7,.4,.7,.6,1,1,.7],
[.2,.3,.5,.3,.6,.3,.8,.9,.6],[.1,.5,.8,.3,1,.7,.2,.7,.8],[.1,.7,.8,.3,.9,.6,.2,.6,.7],[.1,.3,.8,.3,.6,.8,.3,.8,.8],
[.5,.3,.9,.6,1,.1,.4,1,.5],[.2,.2,.7,.4,.9,.1,.4,.7,.6]])
EEC=np.array([ # era x economy
[1,.7,.8,.7,.3,.2,.1,.8,.5],[.5,1,.8,.8,.3,.2,.1,.6,.5],[.2,1,.8,1,.6,.3,.2,.6,.5],[.2,.4,.6,.4,.4,.5,.3,.8,.6],
[.1,.7,.7,.5,.9,.5,.4,.7,.6],[.1,.5,.9,.4,1,.6,.8,.8,.7],[.1,.4,.8,.3,1,.8,.9,.8,.8],[.1,.3,.7,.3,.8,.9,1,.8,.9]])
# pressure x node (rows pressure)
PN=np.array([
[1,1,1,1,1,.1,.2,.1,.1,.3,.3,.1,.2,.5],            # redlining
[.9,.9,.9,.9,1,.9,1,.7,.7,.9,.8,.8,.9,.9],         # police surveillance
[.2,.4,.3,.3,.3,1,.4,.6,.5,.4,.4,.8,.3,.2],        # garrison patronage
[.9,.8,.9,.9,1,1,.7,.7,.7,1,.9,1,.7,.5],           # extralegal violence
[.1,.4,.2,.2,.3,.5,1,.4,.4,.3,.3,.4,1,1],          # immigration law
[.9,.9,.9,.9,.9,.8,.9,.7,.7,.8,.8,.7,.8,.8],       # media criminalization
[.7,.8,.8,.8,.8,.8,.7,.7,.7,.8,.8,.7,.7,.7]])      # class fracture
PE=np.array([
[.3,1,1,1,1,1,1,1],[.9,.9,1,.9,1,1,1,1],[.1,.1,.2,.7,1,1,.8,.6],[.9,.8,.9,.9,1,1,1,1],
[.6,.5,.8,.5,.8,.9,.9,1],[1,1,1,.9,.9,.9,.9,.9],[.7,.8,.8,.7,.8,.8,.8,.8]])
ME=np.array([ # media x era
[1,1,1,1,1,1,1,.8],[1,1,1,.8,.8,.6,.5,.5],[.9,.9,.9,.9,.9,.9,.9,.9],[.8,.8,.8,.8,.8,.8,.8,.8],[.3,.4,.7,1,1,.9,.8,.8]])
# media x node-group availability (state file / Black press need institutions)
MN=np.array([ # rows media; cols nodes
[1]*14,
[1,1,1,1,1,.7,.8,.7,.7,.5,.5,.4,.4,.6],
[.9]*14,[.9]*14,
[1,1,1,1,1,1,1,.6,.6,.5,.5,.5,.6,.7]])
# family x node
FN=np.array([
[.9,1,.8,.8,.8,.9,.8,.8,.7,.8,.8,.9,.7,.8],        # matriarch-led (documented policy queens, boardinghouse keepers, matrifocal kinship)
[.8]*14,
[1,.8,.7,.7,.7,.9,.9,.5,.5,.5,.5,.8,.8,.9],         # migration-separated
[.8,.8,.8,.8,.9,.8,.9,.8,.8,.8,.8,.8,.8,.8],        # chosen family
[.5,.6,.7,.7,.6,.8,.5,.6,.5,.5,.5,.7,.9,.5],        # dynastic
[.7,.8,.8,.8,.8,.95,.95,.8,.8,.8,.8,.95,.8,.95]])   # estranged-return
FE=np.array([ # family x era
[.9,.9,.9,.8,.8,.8,.8,.8],[.8]*8,[1,1,1,.7,.7,.9,.9,.9],[.8]*8,[.6,.6,.8,.8,.8,.8,.7,.7],[.7,.7,.7,.7,.8,.9,.9,.9]])
FEC=np.array([ # family x economy
[.8,1,.7,.6,.6,.5,.6,.6,.6],[.8,.8,.8,.8,.8,.8,.8,.8,.8],[.7,.7,.7,.6,.8,.5,.8,.9,.6],[.8,.8,.8,.8,.9,.8,.8,.8,.8],
[1,1,.9,.9,.8,.7,.7,.8,.7],[.7,.7,.8,.8,.9,.7,.8,.9,.8]])
# empathy
AFIT=np.array([[.95,.45,.85],[.6,.8,.8],[.5,.95,.8],[.8,.4,.6],[.95,.3,.75],[.75,.35,.9],[.75,.6,.95]]) # arch x effect
MH=np.array([.4,.9,.7,1,.5]); MD=np.array([.7,.5,.8,.6,.9])      # media access humanized / dreaded
FH=np.array([.95,.8,.85,.8,.6,.85]); FD=np.array([.6,.6,.5,.5,.9,.8])
# craft
CEC=np.array([.9,.95,.85,.8,.7,.8,.5,.85,.7]); CER=np.array([1,1,1,.7,.9,.85,.8,.6])
CAR=np.array([.9,.6,.95,.55,.85,.8,.75]); CME=np.array([.9,.9,.6,.85,.95])
# dread
DAR=np.array([.6,.75,1,.35,.3,.55,.7]); DPR=np.array([.55,.85,.9,1,.5,.6,.6]); DME=np.array([.8,.4,.7,.6,.9])
# counter-stereotype
SME=np.array([.35,1,.75,.9,.8]); SPR=np.array([1,.9,1,.85,.9,1,.6]); SAR=np.array([.8,.85,.5,.9,1,.7,.7])
SND=np.array([.6,.55,.6,.5,.75,.7,.8,.85,.9,.85,.95,.9,.95,.9]) # node non-default-ness (diaspora specificity)
SND[1]=.6; SND[3]=.6; SND[4]=.5; SND[2]=.55; SND[0]=.75

def bc(arr, axes):
    """broadcast arr whose dims map to given axes into full 8-d shape"""
    shp=[1]*8
    for a,s in zip(axes,arr.shape): shp[a]=s
    return arr.reshape(shp)
# axes: 0 node,1 era,2 econ,3 pres,4 media,5 fam,6 arch,7 eff
def components():
    pn=PN.T  # node x pres
    cci=(bc(NE,(0,1))**.22*bc(NEC,(0,2))**.18*bc(EEC,(1,2))**.15*bc(pn,(0,3))**.10*bc(PE.T,(1,3))**.10*bc(ME.T,(1,4))**.10*bc(MN.T,(0,4))**.15)
    emp_h=.6*bc(AFIT,(6,7))+.2*bc(MH,(4,))+.2*bc(FH,(5,))
    emp_d=.6*bc(AFIT,(6,7))+.2*bc(MD,(4,))+.2*bc(FD,(5,))
    w=np.array([1,0,.5]); wd=np.array([0,1,.5])
    emp=emp_h*bc(w,(7,))+emp_d*bc(wd,(7,))
    fsr=.5*bc(FN.T,(0,5))+.25*bc(FE.T,(1,5))+.25*bc(FEC.T,(2,5))
    mcf=(bc(CEC,(2,))+bc(CER,(1,))+bc(CAR,(6,))+bc(CME,(4,)))/4
    dre=.4*bc(DAR,(6,))+.3*bc(DPR,(3,))+.3*bc(DME,(4,))
    csp=(bc(SME,(4,))+bc(SPR,(3,))+bc(SAR,(6,))+bc(SND,(0,)))/4
    full=lambda x: np.broadcast_to(x,SHAPE)
    return [full(c) for c in (cci,emp,fsr,mcf,dre,csp)]
NAMES=["Causal_Chain_Integrity","Empathy_Structure","Family_System_Realism","Manga_Craft_Fidelity","Dread_Enforcement_Potential","Counter_Stereotypical_Power"]
W_MASTER=np.array([.30,.20,.15,.15,.10,.10]); W_EQUAL=np.ones(6)/6
def score(comps,w): return sum(wi*c for wi,c in zip(w,comps))
def label(idx): return {n:DIMS[i][idx[i]] for i,n in enumerate(["node","era","economy","pressure","media","family","archetype","effect"])}
def top(S,eff,k=5):
    sub=S[...,eff].ravel()
    order=np.lexsort((np.arange(sub.size),-sub))[:k]   # deterministic tiebreak by index
    return order,sub
if __name__=="__main__":
    comps=components(); S=score(comps,W_MASTER); Se=score(comps,W_EQUAL)
    total=int(np.prod(SHAPE)); print("combinations",total, "finite", bool(np.isfinite(S).all()), "range",float(S.min()),float(S.max()))
    cfg=json.dumps({"dims":DIMS,"weights":W_MASTER.tolist(),"tables":[t.tolist() for t in (NE,NEC,EEC,PN,PE,ME,MN,FN,FE,FEC,AFIT,MH,MD,FH,FD,CEC,CER,CAR,CME,DAR,DPR,DME,SME,SPR,SAR,SND)]},sort_keys=True)
    h=hashlib.sha256(cfg.encode()).hexdigest(); print("config_sha256",h)
    out={"config_sha256":h,"combinations":total,"lists":{}}
    for e,en in enumerate(EFF):
        order,sub=top(S,e,5)
        subE=Se[...,e].ravel(); eq_order=set(np.lexsort((np.arange(subE.size),-subE))[:5].tolist())
        ties=int((np.isclose(sub,sub[order[0]],atol=1e-12)).sum())
        rows=[]
        for o in order:
            idx=np.unravel_index(o,SHAPE[:7]); full=idx+(e,)
            rows.append({"score":round(float(sub[o]),4),"config":label(full),"components":{n:round(float(c[full]),3) for n,c in zip(NAMES,comps)}})
        out["lists"][en]={"top5":rows,"tied_at_top":ties,"overlap_with_equal_weight_top5":len(eq_order & set(order.tolist()))}
        print(en,"tied_at_top",ties,"overlap_equalweights",len(eq_order & set(order.tolist())))
        for r in rows: print(r["score"],list(r["config"].values())[:7],r["components"])
    json.dump(out,open("surface.json","w"),indent=1)
